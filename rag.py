"""
Retrieval-Augmented Generation pipeline.

Retrieval: TF-IDF + cosine similarity over the knowledge base (fast, free,
no external API needed — this is what runs by default).

Generation: if OPENAI_API_KEY is set in the environment, the top-matching
KB articles are passed to the OpenAI chat completion API as context and a
grounded answer is generated. If no key is set, the app falls back to a
lightweight extractive responder so the whole project still runs end to
end with zero paid dependencies.
"""
import os
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_PATH = os.path.join(os.path.dirname(__file__), "data", "knowledge_base.json")


class RAGPipeline:
    def __init__(self, kb_path: str = KB_PATH, top_k: int = 2):
        self.top_k = top_k
        with open(kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)

        corpus = [f"{doc['title']}. {doc['content']}" for doc in self.kb]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str):
        """Return the top_k most relevant KB docs for a query, with scores."""
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.doc_matrix).flatten()
        ranked_idx = sims.argsort()[::-1][: self.top_k]
        results = []
        for idx in ranked_idx:
            if sims[idx] <= 0:
                continue
            doc = dict(self.kb[idx])
            doc["score"] = float(sims[idx])
            results.append(doc)
        return results

    def generate(self, query: str, retrieved_docs):
        """Produce an answer grounded in the retrieved docs."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return self._generate_with_openai(query, retrieved_docs, api_key)
        return self._generate_extractive(query, retrieved_docs)

    def _generate_with_openai(self, query, retrieved_docs, api_key):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            context = "\n\n".join(
                f"[{d['title']}]: {d['content']}" for d in retrieved_docs
            )
            system_prompt = (
                "You are a helpful customer support assistant. Answer the "
                "user's question using ONLY the context provided below. If "
                "the context does not contain the answer, say you don't "
                "have that information and suggest contacting support.\n\n"
                f"Context:\n{context}"
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                max_tokens=300,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:  # pragma: no cover - network/key failures
            return self._generate_extractive(query, retrieved_docs, note=str(exc))

    def _generate_extractive(self, query, retrieved_docs, note=None):
        if not retrieved_docs:
            return (
                "I couldn't find anything relevant to that in our help "
                "center. Could you rephrase, or contact support@example.com "
                "for a human to take a look?"
            )
        top = retrieved_docs[0]
        answer = f"Here's what I found on **{top['title']}**:\n\n{top['content']}"
        if len(retrieved_docs) > 1:
            others = ", ".join(d["title"] for d in retrieved_docs[1:])
            answer += f"\n\nYou might also find this related: {others}."
        if note:
            answer += "\n\n(Note: falling back to extractive mode — set OPENAI_API_KEY to enable LLM-generated answers.)"
        return answer
