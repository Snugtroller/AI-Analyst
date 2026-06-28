# AI Report Generator

This workspace contains a chat-style report app with a Python backend and a React frontend.

## What it does

- Accepts a prompt like ChatGPT
- Uses Groq to generate a structured report
- Shows a report preview in the browser
- Lets you download the report as Markdown

## Folders

- `Backend/` FastAPI backend that calls Groq and returns report data
- `Frontend/` Vite + React frontend with the chat-style UI

## Setup

1. Copy `.env.example` to `.env` and add your `GROQ_API_KEY`.
2. Install backend dependencies:

```bash
pip install -r Backend/requirements.txt
```

3. Install frontend dependencies:
+++-
```bash
cd Frontend
npm install
```

4. Run the backend:

```bash
uvicorn Backend.main:app --reload --port 8000
```

5. Run the frontend:

```bash
cd Frontend
npm run dev
```
