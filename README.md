# CodeSage

CodeSage is an AI-powered codebase assistant that helps you understand, search, and analyze your code using natural language.

Upload your code files and ask questions — CodeSage will search relevant code snippets and generate intelligent explanations.

---

## 📸 Preview

![CodeSage UI](CodeSage.png)

---

# ✨ Features

- 🔍 Semantic Code Search
- 🤖 AI Code Explanation
- 📁 Multi-file Upload Support
- ⚡ Streaming AI Responses
- 🧠 Vector Search with ChromaDB
- 🌳 Code Parsing using Tree-sitter
- 💬 ChatGPT-like Interface
- 🔐 Environment-based API Key (.env)

---

# 🏗️ Project Structure
```bash
.
├── main.py
├── README.md
├── requirements.txt
└── templates
    └── index.html

```

---

# ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/codesage.git
cd codesage
```

### 2.Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
(or Windows)
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 🔑 Environment Variables

Create .env file:
```bash
API_KEY=your_groq_api_key
```
```bash
▶️ Run Server
uvicorn main:app --reload
```
Open browser:
```bash
http://127.0.0.1:8000

```
### 🧠 How It Works

1.Upload code files
2.Code is parsed using Tree-sitter
3.Code chunks converted to embeddings
4.Stored in ChromaDB
5.User asks question
6.Relevant code retrieved
7.AI generates explanation


### 🛠️ Tech Stack

- FastAPI
- Groq (Llama 3)
- ChromaDB
- Sentence Transformers
- Tree-sitter
- Jinja2
- HTML / CSS / JS


### 📸 UI Features

- Streaming AI responses
- Rolling typing indicator
- Sidebar file explorer
- Chat history

## 📌 Example Usage

### Upload Files

Upload your project files:

```bash
main.py
services.py
auth.py
```

Ask:
```bash
How login flow works?
```
#### CodeSage will:

Find relevant functions
Show code snippets
Generate explanation

---

## 🚀 Future Improvements

- 📁 Folder upload support  
- 🎨 Syntax highlighting for code snippets  
- ⚡ Real-time streaming using WebSockets  
- 🧠 Multi-project support  
- 🔎 Code navigation and function references  
- 📌 Clickable file and function links  
- 📄 Support for more programming languages  
- 💾 Persistent chat history  
- 🔐 Authentication and user sessions  
- 📊 Better code search ranking and relevance  

---

## 👨‍💻 **Author**

**Omkar Waghmare**  
Engineering in Computer Science | Aspiring Data Scientist