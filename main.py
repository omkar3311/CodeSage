from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse , JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List
import shutil
import os

from tree_sitter_languages import get_language, get_parser
from tree_sitter import Parser
from sentence_transformers import SentenceTransformer
from groq import Groq
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

model = SentenceTransformer("BAAI/bge-small-en")
# os.makedirs("chroma_db", exist_ok=True)
# client = chromadb.Client(
#     Settings(
#         persist_directory="./chroma_db",
#         anonymized_telemetry=False
#     )
# )

client = chromadb.Client()

# collection = client.get_or_create_collection("code_chunks")
collection = client.create_collection("code_chunks")

groq = Groq(api_key=os.getenv("API_KEY"))

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "c_sharp",
    ".php": "php",
    ".rb": "ruby",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml"
}

IGNORE_FOLDERS = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "build"
}

def get_parser_for_file(file_path):

    ext = os.path.splitext(file_path)[1]
    language = EXTENSION_MAP.get(ext)

    if not language:
        return None

    try:
        parser = get_parser(language)
        return parser

    except Exception as e:
        return None
    
def extract_chunks(node, code, file_name, chunks):
    CHUNK_TYPES = {
        "function_definition",
        "class_definition",
        "function_declaration",
        "method_definition",
        "class_declaration",
        "element",
        "function_declarator",
        "class_specifier"
    }

    if node.type in CHUNK_TYPES:

        start = node.start_byte
        end = node.end_byte

        chunk = code[start:end]

        name = None

        for child in node.children:
            if child.type in ["identifier", "property_identifier"]:
                name = code[child.start_byte:child.end_byte]
                break

        chunks.append({
            "file": file_name,
            "type": node.type,
            "name": name or "unknown",
            "start_line": node.start_point[0],
            "end_line": node.end_point[0],
            "text": chunk
        })

    for child in node.children:
        extract_chunks(child, code, file_name, chunks)


def process_directory(paths, chunks):

    for path in paths:

        if os.path.isfile(path):
            process_file(path, chunks)

        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):

                dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]

                for file in files:
                    file_path = os.path.join(root, file)
                    process_file(file_path, chunks)


def process_file(file_path):

    parser = get_parser_for_file(file_path)

    if not parser:
        return []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    tree = parser.parse(bytes(code, "utf-8"))
    node = tree.root_node

    chunks = []

    extract_chunks(node, code, file_path, chunks)

    
    return chunks

def process_code(file_name, code):
    parser = get_parser_for_file(file_name)

    if not parser:
        return []

    tree = parser.parse(bytes(code, "utf-8"))
    node = tree.root_node

    chunks = []

    extract_chunks(node, code, file_name, chunks)

    if not chunks:
        chunks.append({
            "file": file_name,
            "type": "file",
            "name": file_name,
            "start_line": 0,
            "end_line": len(code.splitlines()),
            "text": code
        })
    return chunks

def embed_chunks(chunks):
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embeddings"] = embedding.tolist()
    return chunks

def add_collection(chunks):
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        ids.append(f"{chunk['file']}_{i}")
        documents.append(chunk["text"])
        embeddings.append(chunk["embeddings"])
        
        metadatas.append({
            "file": chunk["file"],
            "type": chunk["type"],
            "name": str(chunk.get("name", "unknown")),
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"]
        })
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

def search_code(query, top_k=2, threshold=0.7):
    query_embedding = model.encode(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    filtered_docs = []
    filtered_meta = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        similarity = 1 - dist  # convert distance to similarity

        if similarity >= threshold:
            filtered_docs.append(doc)
            filtered_meta.append(meta)

    return {
        "documents": [filtered_docs],
        "metadatas": [filtered_meta]
    }

# def search_code(query , top_k = 2):
#     query_embedding = model.encode(query)
#     return collection.query(
#         query_embeddings= [query_embedding],
#         n_results = top_k
#     )


# def AI(query):

#     results = search_code(query)
#     # if not results["documents"][0]:
#     #     context = ""
#     snippets = []
#     context_parts = []

#     for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
#         snippet = f"{meta['name']} ({meta['file']}):\n{doc}"
#         snippets.append(snippet)
#         context_parts.append(snippet)

#     context = "\n\n".join(context_parts)

#     try:
#         chat_completion = groq.chat.completions.create(
#             messages=[
#                 {
#                     "role": "system",
#                     "content": """
#         You are a codebase assistant.

#         Rules:
#         - You will receive a user query and code snippets.
#         - Focus primarily on answering the user query.
#         - Use code snippets only if they are relevant to the query.
#         - If snippets are not relevant, still answer the query based on reasoning.
#         - Do not explain irrelevant parts of the code.
#         - Do not add examples in your explanation.
#         - Keep explanation concise and clear.
#         - Do not repeat code unless necessary.
#         - Do not hallucinate features not present in code.
#         - If query cannot be answered from snippets, say so clearly and still guide based on query.
#         """
#                 },
#                 {
#                     "role": "user",
#                     "content": f"""
#         User Query:
#         {query}

#         Code Snippets:
#         {context}
#         """
#                 }
#             ],
#             model="llama-3.1-8b-instant",
#             temperature=0.1,
#             max_tokens=500
#         )

#         explanation = chat_completion.choices[0].message.content
#         # explanation = "explanation"

#         return {
#             "snippets": snippets,
#             "explanation": explanation
#         }

#     except Exception as e:
#         return f"Error: {str(e)}"

def AI(query):

    results = search_code(query)

    snippets = []
    context_parts = []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    for doc, meta in zip(docs, metas):
        snippet = f"{meta['name']} ({meta['file']}):\n{doc}"
        snippets.append(snippet)
        context_parts.append(snippet)

    context = "\n\n".join(context_parts)

    # Check if snippets exist
    has_context = len(snippets) > 0

    try:

        system_prompt = """
You are a codebase chatbot.

Rules:
- You answer like a chatbot interacting with a developer
- If code snippets are provided, use them to answer
- If no snippets are provided, focus only on user's query
- Do NOT act like general AI assistant
- Stay focused on coding and codebase related discussion
- Keep answers concise and technical
- Do not repeat code unless necessary.
- Do not add examples in your explanation.
- Do not hallucinate features not present in snippets
- If snippets are missing, clearly say you didn't find relevant code
"""

        user_prompt = f"""
User Query:
{query}

Code Snippets:
{context if has_context else "No relevant code snippets found."}
"""

        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=500
        )

        explanation = chat_completion.choices[0].message.content

        return {
            "snippets": snippets,
            "explanation": explanation
        }

    except Exception as e:
        return {
            "snippets": [],
            "explanation": f"Error: {str(e)}"
        }



def show_all_files():
    uploaded_files_history = []

    results = collection.get()

    files = set()

    for meta in results["metadatas"]:
        files.add(meta["file"])

    for file in files:
        uploaded_files_history.append(file)
        
    return uploaded_files_history

chat_history = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    uploaded_files_history = show_all_files()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "files": uploaded_files_history,
            "history": chat_history
        }
    )


@app.post("/upload")
async def upload(request: Request, files: List[UploadFile] = File(...)):
    for file in files:

        content = await file.read()
        code = content.decode("utf-8", errors="ignore")

        chunks = process_code(file.filename, code)

        if not chunks:
            continue
        chunks = embed_chunks(chunks)
        add_collection(chunks)

    uploaded_files_history = show_all_files()
    return {"files": uploaded_files_history}


@app.post("/chat")
async def chat(question: str = Form(...)):

    result = AI(question)

    chat_history.append({
        "question": question,
        "answer": result
    })

    uploaded_files_history = show_all_files()

    return JSONResponse({
        "snippets": result["snippets"],
        "explanation": result["explanation"],
        "files": uploaded_files_history,
        "history": chat_history
    })