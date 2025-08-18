import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from mistralai import Mistral, UserMessage, SystemMessage

# Load .env variables
load_dotenv()

# Config
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "legal-landmark-cases")

MISTRAL_ENDPOINT = "https://models.github.ai/inference"
MODEL_NAME = "mistral-ai/Mistral-Nemo"

# Pinecone setup
pc = Pinecone(api_key=PINECONE_API_KEY)
if INDEX_NAME not in pc.list_indexes().names():
    raise ValueError(f"Index '{INDEX_NAME}' does not exist in Pinecone project.")
index = pc.Index(INDEX_NAME)

# Embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Chat history
chat_history = []

def retrieve_context(query, k=5):
    query_emb = embed_model.encode(query).tolist()
    response = index.query(vector=query_emb, top_k=k, include_metadata=True)
    matches = response.get("matches", [])

    if not matches:
        return "No relevant context could be retrieved."

    context_parts = []
    for match in matches:
        meta = match.get("metadata", {})
        chunk_text = meta.get("chunk_text", "")
        case_title = meta.get("case_title", "Unknown Case")
        date = meta.get("date_of_judgment", "Unknown Date")
        bench = meta.get("bench", "N/A")
        context_parts.append(
            f"---\nCase Title: {case_title}\nDate: {date}\nBench: {bench}\nContent: {chunk_text}\n---"
        )

    joined_context = "\n".join(context_parts)
    if len(joined_context) > 12000:
        joined_context = joined_context[:12000] + "\n\n...[Context truncated]..."

    return joined_context


def query_mistral(context, question, chat_history):
    """
    Query GitHub-hosted Mistral-Nemo model using mistralai SDK.
    """
    # Compile last 3 rounds of chat history
    history_string = ""
    for turn in chat_history[-3:]:
        history_string += f"Question: {turn['question']}\nAnswer: {turn['answer']}\n\n"

    system_message = """You are a legal research assistant specialized in Indian Supreme Court judgments.

Your behavior:
- If the user asks a **general legal question** (e.g., about a constitutional article, principle, or interpretation), give a **clear, conversational answer** first, then mention the most relevant case and its principle briefly (1973,1978,1992,1994,2018,2024 specifically).
- If the user asks to **summarize a judgment or case**, provide:
    - **Case Title**
    - **Date (DD Month YYYY)**
    - **Bench**
    - **Final Decision** (upheld/overturned, relief granted, etc.)
    - **Reasoning** (tests applied, constitutional interpretation)
    - **Articles or Precedents cited**
- If the question is unclear, ask a clarifying question.

Rules:
- Use only the provided context (do not hallucinate).
- Do not confuse pleadings with the Court’s findings.
- If no relevant case is found, say:
  "I couldn't find relevant information in the provided context."
- Keep answers short, precise, and authoritative.
"""

    # Construct user prompt
    user_prompt = f"""
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

    try:
        client = Mistral(api_key=GITHUB_TOKEN, server_url=MISTRAL_ENDPOINT)

        response = client.chat.complete(
            model=MODEL_NAME,
            messages=[
                SystemMessage(content=system_message),
                UserMessage(content=user_prompt)
            ],
            temperature=0.2,
            max_tokens=1024,
            top_p=1.0
        )

        return response.choices[0].message.content.strip()

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