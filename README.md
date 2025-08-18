# Avocado AI – Legal Judgment Search Engine

**Live Demo:** [[https://avocado-ai.duckdns.org/](https://avocado-ai.duckdns.org/)]

---

## Overview
Avocado AI is an AI-powered Retrieval-Augmented Generation (RAG) system designed to search through [Supreme Court of India judgments (1950–2025)](https://www.kaggle.com/datasets/adarshsingh0903/legal-dataset-sc-judgments-india-19502024) and provide context-aware answers. It allows users to query legal cases in natural language and get context-aware answers with references to judgments.  
Built with Flask, ChromaDB, Pinecone and Mistral, this project demonstrates my expertise in **Natural Language Processing (NLP), Large Language Models (LLMs), and Full-Stack Deployment**.

---

## ✨ Features
* Vector Search with ChromaDB – Efficient retrieval of relevant judgments.
* Mistral AI Integration – Generates clear, context-aware summaries and answers.
* Session Memory – Chat remembers your previous questions  if you refresh the page for coherent conversations. Clicking the title or logo starts a new chat.
* Deployed on Cloud with Docker – Accessible through a secure endpoint served via Flask + Nginx + Certbot
* Interactive Chat UI – User-friendly interface with styled Q&A boxes.
* Accessible through a live demo link  

---

## 🛠 Tech Stack
- **Backend:** Python, Flask  
- **Database:** ChromaDB, Pinecone
- **Frontend:** HTML, CSS, JavaScript (Flask templates)  
- **Deployment:** Docker, AWS EC2, Nginx, Certbot  

---
## 📂 Project Structure
```
├── app.py                  # Flask backend
├── avocado-large/
│   └── query_engine.py     # ChromaDB + Mistral AI RAG-pipeline
├── avocado-small/
│   └── query_engine.py     # Pinecone + Mistral AI RAG-pipeline
├── templates/              # HTML templates
├── static/                 # CSS + JS
├── requirements.txt        # Dependencies
└── docker-compose.yml      # Deployment setup
└── Preprocessing/
    └── (1)preprocessing_and_validation.ipynb # Parsing and cleaning the PDFs/json files of the Judgements. Creating a json file with 2.1M+ text chunks
    └── (2)embedding_colab.ipynb              # Vector embedding the text on Google Colab (Free Ver.) using the T4 GPU. Storing the embeddings into 4 files of 5 gbs
    └── (3)embedding_validation.ipynb            # Ensuring all chunks were embedded
    └── (4)chromadb_databasing.py             # Storing the vector embeddings on a persistent ChromaDB client - created a 20GB database
    └── (5)pinecone_databasing.ipynb          # Storing the vector embeddings on Pinecone (Free Ver.) through Google Colab
```
