"""High level CRUD helpers for database access.

These helpers provide a thin abstraction over SQLAlchemy queries so that other
parts of the application can interact with the database without dealing with the
ORM details. The functions are intentionally minimal and will expand as the
migration from file-based storage progresses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional
import uuid

from sqlalchemy.orm import Session

from . import SessionLocal
from . import models

# Utility --------------------------------------------------------------------

def get_session() -> Session:
    """Return a new :class:`Session` bound to the engine."""
    return SessionLocal()

# User operations -------------------------------------------------------------

def create_user(db: Session, email: str, hashed_password: str) -> models.User:
    user = models.User(id=str(uuid.uuid4()), email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

# Web session operations ------------------------------------------------------

def create_web_session(
    db: Session,
    *,
    session_id: str,
    user_id: str,
    issued_at: datetime,
    expires_at: datetime,
    ua_hash: str | None = None,
    ip_net: str | None = None,
    attrs: dict | None = None,
) -> models.WebSession:
    sess = models.WebSession(
        session_id=session_id,
        user_id=user_id,
        issued_at=issued_at,
        expires_at=expires_at,
        last_seen=issued_at,
        ua_hash=ua_hash,
        ip_net=ip_net,
        attrs=attrs or {},
    )
    db.add(sess)
    db.commit()
    return sess


def get_web_session(db: Session, session_id: str) -> Optional[models.WebSession]:
    return db.query(models.WebSession).filter(models.WebSession.session_id == session_id).first()


def delete_web_session(db: Session, session_id: str) -> None:
    db.query(models.WebSession).filter(models.WebSession.session_id == session_id).delete()
    db.commit()

# Chat session operations -----------------------------------------------------

def create_chat_session(db: Session, user_id: str) -> models.ChatSession:
    sess = models.ChatSession(user_id=user_id)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def get_chat_session(db: Session, session_id: str) -> Optional[models.ChatSession]:
    return db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()


def add_chat_exchange(
    db: Session,
    session_id: str,
    user_message: str,
    rag_prompt: str,
    assistant_message: str,
    html_response: str,
    context_used: Iterable[dict],
) -> models.ChatExchange:
    exchange = models.ChatExchange(
        session_id=session_id,
        user_message=user_message,
        rag_prompt=rag_prompt,
        assistant_message=assistant_message,
        html_response=html_response,
        context_used=list(context_used),
    )
    db.add(exchange)
    db.commit()
    db.refresh(exchange)
    return exchange


def list_chat_sessions(db: Session, user_id: str) -> List[models.ChatSession]:
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id).all()

# Prompt operations -----------------------------------------------------------

def create_prompt(db: Session, prompt_id: str, name: str, content: dict) -> models.PromptTemplate:
    prompt = models.PromptTemplate(id=prompt_id, name=name, content=content)
    db.add(prompt)
    db.commit()
    return prompt


def get_prompt(db: Session, prompt_id: str) -> Optional[models.PromptTemplate]:
    return db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()


def list_prompts(db: Session) -> List[models.PromptTemplate]:
    return db.query(models.PromptTemplate).all()

# Document operations --------------------------------------------------------

def create_document(
    db: Session,
    *,
    filename: str,
    path: str,
    tags: Iterable[str] | None = None,
) -> models.Document:
    doc = models.Document(filename=filename, path=path, tags=list(tags or []))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, doc_id: str) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == doc_id).first()


def list_documents(db: Session) -> List[models.Document]:
    return db.query(models.Document).all()
