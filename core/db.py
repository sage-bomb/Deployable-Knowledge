import os
import sys
from pathlib import Path
import importlib.util
import types
import uuid
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Resolve base directory of project (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Database directory inside project root
DB_DIR = BASE_DIR / "local_db"
DB_DIR.mkdir(parents=True, exist_ok=True)

# Ensure SQLAlchemy uses a database within DB_DIR
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(DB_DIR / 'app.db').as_posix()}")

# Attempt to load the deployable-db submodule; fall back to a minimal ORM
SUBMODULE_SRC = BASE_DIR / "submodules" / "deployable-db" / "src"
try:
    spec = importlib.util.spec_from_file_location(
        "db", SUBMODULE_SRC / "__init__.py", submodule_search_locations=[str(SUBMODULE_SRC)]
    )
    if spec is None or spec.loader is None:
        raise FileNotFoundError
    db = importlib.util.module_from_spec(spec)
    sys.modules["db"] = db
    spec.loader.exec_module(db)  # type: ignore

    from db import init_db, SessionLocal  # type: ignore
    from db.schema.user import User, WebSession  # type: ignore
    from db.schema.chat import ChatSession as DBChatSession, ChatExchange as DBChatExchange  # type: ignore
    from db.data_access import user_ops, chat_ops, document_ops  # type: ignore
except FileNotFoundError:
    # --- Minimal fallback definitions ---
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()

    def _uuid() -> str:
        return str(uuid.uuid4())

    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True, default=_uuid)
        email = Column(String, unique=True, nullable=False)
        hashed_password = Column(String, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class WebSession(Base):
        __tablename__ = "web_sessions"
        session_id = Column(String, primary_key=True)
        user_id = Column(String, ForeignKey("users.id"), nullable=False)
        issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        expires_at = Column(DateTime, nullable=False)
        last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
        ua_hash = Column(String, nullable=True)
        ip_net = Column(String, nullable=True)
        attrs = Column(JSON, default=dict)

    class DBChatSession(Base):
        __tablename__ = "chat_sessions"
        id = Column(String, primary_key=True, default=_uuid)
        user_id = Column(String, ForeignKey("users.id"), nullable=False)
        summary = Column(Text, default="")
        title = Column(Text, default="")
        persona = Column(Text, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)

    class DBChatExchange(Base):
        __tablename__ = "chat_exchanges"
        id = Column(String, primary_key=True, default=_uuid)
        session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
        user_message = Column(Text)
        rag_prompt = Column(Text)
        assistant_message = Column(Text)
        html_response = Column(Text)
        context_used = Column(JSON, default=list)

    class _ChatOps:
        def add_chat_exchange(
            self,
            db,
            session_id: str,
            user_message: str,
            rag_prompt: str,
            assistant_message: str,
            html_response: str,
            context_used,
        ):
            ex = DBChatExchange(
                session_id=session_id,
                user_message=user_message,
                rag_prompt=rag_prompt,
                assistant_message=assistant_message,
                html_response=html_response,
                context_used=context_used,
            )
            db.add(ex)
            db.commit()

        def list_chat_exchanges(self, db, session_id: str):
            return (
                db.query(DBChatExchange)
                .filter(DBChatExchange.session_id == session_id)
                .all()
            )

        def delete_chat_session(self, db, session_id: str):
            sess = db.query(DBChatSession).filter(DBChatSession.id == session_id).first()
            if sess:
                db.delete(sess)
                db.commit()

    class _UserOps:
        pass

    user_ops = _UserOps()
    chat_ops = _ChatOps()
    document_ops = types.SimpleNamespace()

    def init_db() -> None:
        Base.metadata.create_all(bind=engine)

# Create tables on import
init_db()

# Directory for storing uploaded documents
DOCUMENTS_DIR = DB_DIR / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
