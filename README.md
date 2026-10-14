# SupportDesk AI  (Project #30: AI-Powered Full-Stack SaaS App)

A mini SaaS where each user signs up, creates AI chatbots for their business
(custom instructions / FAQs), and chats with them. Chat history is saved.

## Tech stack
- Backend: Python + FastAPI
- Database: SQLite (built into Python, zero setup)
- Auth: JWT + PBKDF2 password hashing
- AI: OpenAI API (works in demo mode without a key)
- Frontend: plain HTML + CSS + JavaScript (no build step)

## Project structure
supportdesk-ai/
  app/
    __init__.py
    config.py     -> loads .env
    database.py   -> SQLite tables
    auth.py       -> hashing + JWT
    ai.py         -> OpenAI call
    main.py       -> API routes
  static/index.html  -> the web UI
  requirements.txt
  .env.example

## Run it (Windows)
1. Open the folder in a terminal (cmd or PowerShell).
2. python -m venv venv
3. venv\Scripts\activate
4. pip install -r requirements.txt
5. copy .env.example .env   (then edit .env: add OPENAI_API_KEY and a random JWT_SECRET)
6. uvicorn app.main:app --reload
7. Open http://127.0.0.1:8000  (API docs: http://127.0.0.1:8000/docs)

No API key? Leave it blank and the bot replies in demo mode.

## API endpoints
POST   /api/register              {email, password}
POST   /api/login                 {email, password}
GET    /api/bots                  (auth)
POST   /api/bots                  {name, instructions}
DELETE /api/bots/{id}
GET    /api/bots/{id}/messages
POST   /api/bots/{id}/chat        {message}

## Ideas to level it up
1. Deploy on Render / Railway and add it to your portfolio
2. Upload a PDF/FAQ and answer from it (RAG)
3. Embeddable chat widget (one <script> tag for any website)
4. Stripe payments for a paid plan
5. Streaming replies, rate limiting, PostgreSQL