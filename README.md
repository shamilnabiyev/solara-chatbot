# Solara Chatbot 

Solara Chatbot App using Azure OpenAI models

<div align="center">
    <img src="docs/imgs/chatbot-gui.png" alt="Chatbot GUI" width="500"/>
</div>


Install dependencies

```bash
pip install -r requirements
```

Create `.env` file and add the env variables to it:

```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=sales_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
AZURE_OPENAI_MODEL_DEPLOYMENT='azure-openai-deployment-name'
AZURE_OPENAI_ENDPOINT='azure-openai-endpoint'
AZURE_OPENAI_API_VERSION='azure-openai-api-version'
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
