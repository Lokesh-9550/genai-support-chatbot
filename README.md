# AI-Powered Customer Support Chatbot

A full-stack Gen AI chatbot that answers customer support questions using a
Retrieval-Augmented Generation (RAG) pipeline: relevant help-center articles
are retrieved with TF-IDF similarity search and used to ground the answer.

## Tech Stack
- **Backend:** Python, Flask
- **Retrieval:** scikit-learn TF-IDF + cosine similarity
- **Generation:** OpenAI API (optional — falls back to extractive answers with no key)
- **Database:** SQLite (stdlib `sqlite3`) for local dev — swap in PostgreSQL by pointing the queries in `models.py` at `psycopg2` for production
- **Frontend:** Vanilla JavaScript, HTML, CSS

## Features
- Real-time chat UI backed by a REST API (`/api/chat`)
- RAG retrieval over a JSON knowledge base (`data/knowledge_base.json`) — swap
  in your own articles to support a real product
- Conversation history persisted per browser session
- Works fully offline out of the box (no API key required); automatically
  upgrades to LLM-generated answers when `OPENAI_API_KEY` is set

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional — enables real LLM-generated answers
export OPENAI_API_KEY=sk-...

python app.py
```

Visit `http://localhost:5000`.

## API

| Endpoint        | Method | Description                                   |
|------------------|--------|------------------------------------------------|
| `/api/chat`      | POST   | `{"message": "..."}` → grounded answer + sources |
| `/api/history`   | GET    | Returns the conversation history for the session |
| `/api/health`    | GET    | Health check                                    |

## Project Structure
```
genai-support-chatbot/
├── app.py              # Flask routes
├── rag.py               # Retrieval + generation pipeline
├── models.py            # sqlite3 persistence (conversations, messages)
├── data/knowledge_base.json
├── templates/index.html
├── static/chat.js, style.css
└── requirements.txt
```
