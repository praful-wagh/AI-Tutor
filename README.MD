
# 🎙️ Aura: Realtime AI Whiteboard Tutor

Aura is an interactive, real-time tutoring application that simulates a classroom experience. Using LLM, Aura simultaneously "writes" key concepts on a digital whiteboard and "speaks" explanations in a natural, human-like voice.

## ✨ Features

* **Dual-Stream Output:** Uses Function Calling to ensure the visual board and audio script are perfectly synced.
* **Interactive Whiteboard:** A dark-mode, chalkboard-style interface that renders Markdown and $LaTeX$.
* **Voice & Text Input:** Ask questions by typing or using the built-in browser Speech-to-Text.
* **Human-Like Interaction:** Aura uses natural transitions and spatial references (e.g., "As you can see on the board...").
* **Powered by Groq:** Experience near-instant responses with Llama 3.3 70B.

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, WebSockets
* **LLM:** Groq SDK (Llama 3.3 70B)
* **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla)
* **Speech:** Browser Web Speech API (Synthesis & Recognition)
* **Rendering:** Marked.js (Markdown) & MathJax/KaTeX (for $LaTeX$)

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.8+
* A LLM API key

### 2. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Set your Groq API key in your environment variables or directly in `main.py`:
```python
client = AsyncGroq(api_key="your_groq_api_key_here")
```

### 4. Running the App
Execute the main script:
```bash
python main.py
```
The app will automatically open in your browser at `http://127.0.0.1:8000`.

## 📂 Project Structure
```
├── main.py              # FastAPI Backend & WebSocket Logic
├── static/
│   └── index.html       # Frontend UI & Voice Logic
└── requirements.txt     # Dependency list for deployment
```
