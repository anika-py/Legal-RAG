import os
from chromadb import PersistentClient
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MISTRAL_ENDPOINT = "https://models.github.ai/inference"
MODEL_NAME = "mistral-ai/Mistral-Nemo"

# Check if running inside Docker
IN_DOCKER = os.path.exists("/.dockerenv")

if IN_DOCKER:
    # Path inside the container
    CHROMA_DIR = "/app/avocado_large/chroma_legal_database"
else:
    # Path on Windows machine
    CHROMA_DIR = r"D:\Projects\legal\main_webapp\avocado_large\chroma_legal_database"


COLLECTION_NAME = "legal_judgments"

client = PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(COLLECTION_NAME)

model = SentenceTransformer("all-MiniLM-L6-v2")

chat_history = []

def extract_legal_keywords(query):
    """
    Extract simple legal keywords from the query, e.g., Article numbers, Sections, or statutes.
    You can improve this with regex or NLP for more complex cases.
    """
    keywords = []
    # Example: extract "Article 15" → "Article 15"
    import re
    matches = re.findall(r'(Article|Section)\s*\d+', query, re.IGNORECASE)
    keywords.extend(matches)
    return keywords

def retrieve_context(query, k=15):
    """
    Retrieve top-k chunks from ChromaDB with hybrid semantic + keyword filtering.
    """
    query_emb = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_emb, n_results=k)

    chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not chunks or not any(chunks):
        return "No relevant context could be retrieved."

    # Extract keywords from the query (e.g., Article numbers)
    query_keywords = extract_legal_keywords(query)

    # Keyword filtering
    def keyword_filter(chunks, metadatas, keywords):
        if not keywords:
            return chunks, metadatas  # nothing to filter
        filtered_chunks = []
        filtered_metas = []
        for chunk, meta in zip(chunks, metadatas):
            text_to_search = " ".join([str(chunk)] + [str(v) for v in meta.values()]).lower()
            if all(kw.lower() in text_to_search for kw in keywords):
                filtered_chunks.append(chunk)
                filtered_metas.append(meta)
        return filtered_chunks, filtered_metas

    kw_chunks, kw_metas = keyword_filter(chunks, metadatas, query_keywords)

    # Fallback to semantic results if keyword filter returns nothing
    final_chunks, final_metas = (kw_chunks, kw_metas) if kw_chunks else (chunks, metadatas)

    # Build context string
    context_parts = []
    for chunk, meta in zip(final_chunks, final_metas):
        bench = meta.get("bench", "N/A")
        case_title = meta.get("case_title", "Unknown Case")
        date = meta.get("date_of_judgment", "Unknown Date")
        context_parts.append(
            f"---\nCase Title: {case_title}\nDate: {date}\nBench: {bench}\nContent: {chunk}\n---"
        )

    joined_context = "\n".join(context_parts)
    if len(joined_context) > 12000:
        joined_context = joined_context[:12000] + "\n\n...[Context truncated]..."

    return joined_context

def query_mistral(context, question, chat_history):
    history_string = ""
    for turn in chat_history[-3:]:
        history_string += f"Question: {turn['question']}\nAnswer: {turn['answer']}\n\n"

    system_message = {
        "role": "system",
    "content": """You are a legal assistant trained exclusively on Indian Supreme Court judgments between 1950 and 2025.

Important instructions:
- If the user asks for the **meaning, definition, or explanation** of a constitutional article, statute, or legal term, provide a concise and clear **definition first**.
- Only include case examples if the user explicitly asks for them.
- Otherwise, answer based on the retrieved context.

Your task is to:
- Select the **most relevant case** from the provided context.
- Only summarize when asked by the user.
- When summarizing, include:
  - The **final decision** (e.g., conviction upheld/overturned, sentence modified, relief granted).
  - The **reasoning behind the decision**.
  - Any **statutes, constitutional articles, or precedents applied**.
  - Say Hello to the user if they say "hi" or "hello".

Judgment Summarization Rules:
- Do NOT confuse **claims or pleadings** with the Court’s **actual findings**.
- If the judgment **reverses, affirms, or modifies** a lower court decision, clearly mention that.
- If the case involves **sentencing**, explicitly state whether the sentence was confirmed, reduced, or commuted (e.g., death penalty to life imprisonment).
- If both **conviction** and **sentencing** are discussed, summarize both.
- If a precedent is applied, briefly state its name and purpose.

Avoid:
- Quoting from affidavits, pleadings, or sale deeds unless the **Court endorsed that view**.
- Saying “the plaintiff has a right to...” unless the **judgment confirms it**.
- Guessing or filling in information not present in the context.

If you find no relevant ruling, say:
"I couldn't find relevant information in the provided context."

When nothing specific is asked, include:
- **Case Title**
- **Judgment Date (in Date Month Year format)**
- **Bench (if available)**
- **Summary of Court’s Decision**
- **Legal Principle(s) Illustrated**
- **Any Articles or Precedents Cited**
"""
    }

    user_message = {
        "role": "user",
        "content": f"""
Context from vector database:
----------------------------
{context}

Chat History (last 3):
----------------------------
{history_string}

User Question:
{question}

Answer as per instructions above.
"""
    }

    try:
        response = requests.post(
            url=f"{MISTRAL_ENDPOINT}/chat/completions",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
            json={
                "model": MODEL_NAME,
                "messages": [system_message, user_message],
                "temperature": 0.3,
                "max_tokens": 1024,
                "top_p": 1.0
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Mistral API error: {str(e)}"

def clean_query(query):
    generic_words = ["random", "some", "give me", "about", "related to", "case of"]
    query_lower = query.lower()
    for word in generic_words:
        query_lower = query_lower.replace(word, "")
    return query_lower.strip() or query.strip()

def rag_query(user_query, chat_history):
    search_query = clean_query(user_query)
    context = retrieve_context(search_query)

    if context == "No relevant context could be retrieved.":
        final_answer = "Sorry, I couldn't find relevant information in the legal database for your question."
    else:
        final_answer = query_mistral(context, user_query, chat_history)

    chat_history.append({"question": user_query, "answer": final_answer})
    if len(chat_history) > 20:
        chat_history.pop(0)

    return {"reply": final_answer, "history": chat_history}