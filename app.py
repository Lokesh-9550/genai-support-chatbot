import uuid
import json

from flask import Flask, request, jsonify, render_template, session

from models import init_db, get_or_create_conversation, add_message, get_messages
from rag import RAGPipeline

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"

rag = RAGPipeline()
init_db()


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    session_id = session.get("session_id") or str(uuid.uuid4())
    session["session_id"] = session_id

    retrieved = rag.retrieve(user_message)
    answer = rag.generate(user_message, retrieved)

    conversation_id = get_or_create_conversation(session_id)
    add_message(conversation_id, "user", user_message)
    add_message(
        conversation_id,
        "assistant",
        answer,
        retrieved_kb_ids=",".join(d["id"] for d in retrieved),
    )

    return jsonify(
        {
            "answer": answer,
            "sources": [{"id": d["id"], "title": d["title"], "score": round(d["score"], 3)} for d in retrieved],
        }
    )


@app.route("/api/history")
def history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"messages": []})
    return jsonify({"messages": get_messages(session_id)})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
