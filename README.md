# Solara Chatbot 

Simple Solara Chatbot using local Ollama

<div align="center">
    <img src="docs/imgs/chatbot-gui.png" alt="Chatbot GUI" width="500"/>
</div>


Install dependencies

```bash
pip install -r requirements
```

Option 1: Run the standalone solara app

```bash
solara run sol.py 
```

The app will be available at `http://localhost:8765`

Option 2: Embedd the solara app into FastAPI app

```bash
SOLARA_APP=gui/sol.py uvicorn app:app
```
The app will be available at `http://localhost:8000/solara/`
