# Database Schema

This repository currently persists several pieces of data as JSON files on the
filesystem. To prepare for migrating this information to a database the
`db` module introduces SQLAlchemy models and helper functions. The tables cover
user accounts, web sessions, chat history, prompt templates and document
metadata.

## Tables

- **users** – basic user records with email, hashed password and per-user LLM configuration.
- **web_sessions** – login sessions issued by the HTTPS interface.
- **chat_sessions** – individual chat conversations.
- **chat_exchanges** – messages within a chat session.
- **prompts** – prompt templates previously stored as JSON files.
- **documents** – metadata for uploaded documents.

Run `from db import init_db; init_db()` to create the tables in the default
SQLite database (`app.db`). The rest of the application continues to operate on
its existing file based storage.
