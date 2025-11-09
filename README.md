# Keep in Touch

Group chat experiment I built in second year to get more comfortable with Flask and a bit of AI integration. You log in, pick one of four rooms (Kyle, Jane, Sam or David) and the bot on the other end keeps the conversation going.

## Features
- register and log in with JWT tokens
- four themed rooms with separate histories
- bot replies even when the Gemini quota is gone thanks to a fallback list
- dark UI that behaves on desktop and mobile

## Tech stack
- Flask, SQLite, bcrypt, PyJWT
- Plain HTML, CSS and vanilla JavaScript
- Optional Google Gemini key for smarter replies (still works without it)

## Getting started
What I do when testing locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
python run.py
```

The server listens on port 3000. Open `http://localhost:3000`, create an account and start chatting. If you leave the Gemini key blank in `.env`, the app falls back to the handwritten responses in `ai_service.py`.

## To-do list for later
- better front-end validation
- a way to clear old messages without poking the database
- maybe let two real users share the same room

Thanks for taking a look—happy to hear suggestions.

