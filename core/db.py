import os
import sys
from pathlib import Path
import importlib.util

# Resolve base directory of project (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Database directory inside project root
DB_DIR = BASE_DIR / "local_db"
DB_DIR.mkdir(parents=True, exist_ok=True)

# Ensure SQLAlchemy uses a database within DB_DIR
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(DB_DIR / 'app.db').as_posix()}")

# Load the deployable-db package without installation
SUBMODULE_SRC = BASE_DIR / "submodules" / "deployable-db" / "src"
spec = importlib.util.spec_from_file_location(
    "db", SUBMODULE_SRC / "__init__.py", submodule_search_locations=[str(SUBMODULE_SRC)]
)
db = importlib.util.module_from_spec(spec)
sys.modules["db"] = db
assert spec.loader is not None
spec.loader.exec_module(db)  # type: ignore

# Import ORM package after path/environment are configured
from db import init_db, SessionLocal  # type: ignore
from db.schema.user import User, WebSession  # type: ignore
from db.schema.chat import ChatSession as DBChatSession, ChatExchange as DBChatExchange  # type: ignore
from db.data_access import user_ops, chat_ops, document_ops  # type: ignore

# Create tables on import
init_db()

# Directory for storing uploaded documents
DOCUMENTS_DIR = DB_DIR / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
