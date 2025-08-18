import json
import os
from chromadb import PersistentClient
from tqdm import tqdm

EMBEDDING_FILES = [
    "embeddings\embedding_output_part_0.jsonl",
    "embeddings\embedding_output_part_1.jsonl",
    "embeddings\embedding_output_part_2.jsonl",
    "embeddings\embedding_output_part_3.jsonl"
]
CHUNK_SIZE = 2000 


CHROMA_DIR = "C:\chroma_legal_database"
COLLECTION_NAME = "legal_judgments"

client = PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(COLLECTION_NAME)


total_inserted = 0
for file_path in EMBEDDING_FILES:
    print(f"\nProcessing: {os.path.basename(file_path)}")

    ids, embeddings, documents, metadatas = [], [], [], []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Indexing", unit="chunk"):
            try:
                entry = json.loads(line)
                ids.append(entry["id"])
                embeddings.append(entry["embedding"])
                documents.append(entry["document"])
                metadatas.append(entry["metadata"])

                if len(ids) >= CHUNK_SIZE:
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas
                    )
                    total_inserted += len(ids)

                    ids.clear()
                    embeddings.clear()
                    documents.clear()
                    metadatas.clear()
    
            except Exception as e:
                print(f"Skipping due to error: {e}")
                continue

    # Insert remaining
    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        total_inserted += len(ids)

print(f"\nDone! Total chunks indexed in ChromaDB: {total_inserted:,}")
