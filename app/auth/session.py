from __future__ import annotations
import os, json, secrets, hmac, hashlib, base64, re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from core.db import SessionLocal, User, WebSession

UTC = timezone.utc
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

def _now() -> datetime:
    return datetime.now(UTC)

def _rand_b64(n_bytes: int = 32) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(n_bytes)).decode().rstrip("=")

def _hash(s: str) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()

def _ip_prefix(remote: str, cidr: Optional[int]) -> Optional[str]:
    if not remote or not cidr or "/" in (remote or ""):
        return None
    parts = remote.split(".")
    if len(parts) != 4:
        return None
    keep = cidr // 8
    rest = 4 - keep
    prefix = ".".join(parts[:keep]) + (".0" * rest)
    return f"{prefix}/{cidr}"

class SessionSettings(BaseModel):
    idle_timeout_minutes: int = 15
    absolute_ttl_hours: int = 8
    refresh_on_activity: bool = True

    cookie_name: str = "session_id"
    csrf_cookie_name: str = "csrf_token"
    samesite: str = "Strict"
    secure_cookies: bool = True
    dev_allow_insecure_on_localhost: bool = True

    bind_user_agent: bool = True
    bind_ip_prefix_cidr: Optional[int] = None

    allow_paths: Set[str] = {"/", "/begin", "/logout", "/docs", "/openapi.json", "/healthz", "/favicon.ico"}
    allow_path_prefixes: Set[str] = {"/static", "/documents"}

    session_dir: str = "user_sessions"

    class Config:
        arbitrary_types_allowed = True

def load_settings_from_config() -> "SessionSettings":
    try:
        import app.auth.config
        return SessionSettings(
            idle_timeout_minutes=getattr(config, "SESSION_IDLE_TIMEOUT_MINUTES", 15),
            absolute_ttl_hours=getattr(config, "SESSION_ABSOLUTE_TTL_HOURS", 8),
            refresh_on_activity=getattr(config, "SESSION_REFRESH_ON_ACTIVITY", True),
            cookie_name=getattr(config, "SESSION_COOKIE_NAME", "session_id"),
            csrf_cookie_name=getattr(config, "CSRF_COOKIE_NAME", "csrf_token"),
            samesite=getattr(config, "SESSION_COOKIE_SAMESITE", "Strict"),
            secure_cookies=getattr(config, "SESSION_SECURE_COOKIES", True),
            dev_allow_insecure_on_localhost=getattr(config, "DEV_ALLOW_INSECURE_COOKIES", True),
            bind_user_agent=getattr(config, "SESSION_BIND_USER_AGENT", True),
            bind_ip_prefix_cidr=getattr(config, "SESSION_BIND_IP_PREFIX_CIDR", None),
            allow_paths=set(getattr(config, "AUTH_ALLOW_PATHS", {"/","/docs","/openapi.json","/healthz","/favicon.ico"})),
            allow_path_prefixes=set(getattr(config, "AUTH_ALLOW_PATH_PREFIXES", {"/static", "/documents"})),
            session_dir=getattr(config, "SESSION_DIR", "user_sessions"),
        )
    except Exception:
        return SessionSettings()

class Session(BaseModel):
    session_id: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    last_seen: datetime
    ua_hash: Optional[str] = None
    ip_net: Optional[str] = None
    attrs: Dict[str, Any] = Field(default_factory=dict)
    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

class SessionStore:
    def get(self, sid: str) -> Optional["Session"]: ...
    def put(self, sess: "Session") -> None: ...
    def delete(self, sid: str) -> None: ...

class FileSessionStore(SessionStore):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    def _path(self, sid: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", sid)
        return os.path.join(self.base_dir, f"{safe}.json")
    def get(self, sid: str) -> Optional["Session"]:
        p = self._path(sid)
        if not os.path.exists(p): return None
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("issued_at","expires_at","last_seen"):
            data[k] = datetime.fromisoformat(data[k])
        return Session(**data)
    def put(self, sess: "Session") -> None:
        p = self._path(sess.session_id)
        tmp = p + ".tmp"
        data = sess.model_dump()
        for k in ("issued_at","expires_at","last_seen"):
            data[k] = data[k].isoformat()
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, p)
    def delete(self, sid: str) -> None:
        p = self._path(sid)
        try: os.remove(p)
        except FileNotFoundError: pass

class DBSessionStore(SessionStore):
    """Database-backed session storage using the deployable-db submodule."""

    def __init__(self):
        self.session_factory = SessionLocal

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Attach UTC tzinfo to naive datetimes returned from the DB."""
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    def get(self, sid: str) -> Optional["Session"]:
        with self.session_factory() as db:
            ws = db.query(WebSession).filter(WebSession.session_id == sid).first()
            if not ws:
                return None
            return Session(
                session_id=ws.session_id,
                user_id=ws.user_id,
                issued_at=self._ensure_utc(ws.issued_at),
                expires_at=self._ensure_utc(ws.expires_at),
                last_seen=self._ensure_utc(ws.last_seen),
                ua_hash=ws.ua_hash,
                ip_net=ws.ip_net,
                attrs=ws.attrs or {},
            )

    def put(self, sess: "Session") -> None:
        with self.session_factory() as db:
            user = db.query(User).filter(User.id == sess.user_id).first()
            if not user:
                user = User(id=sess.user_id, email=f"{sess.user_id}@local", hashed_password="!")
                db.add(user)
            ws = db.query(WebSession).filter(WebSession.session_id == sess.session_id).first()
            if ws:
                ws.user_id = sess.user_id
                ws.issued_at = sess.issued_at.replace(tzinfo=None)
                ws.expires_at = sess.expires_at.replace(tzinfo=None)
                ws.last_seen = sess.last_seen.replace(tzinfo=None)
                ws.ua_hash = sess.ua_hash
                ws.ip_net = sess.ip_net
                ws.attrs = sess.attrs
            else:
                ws = WebSession(
                    session_id=sess.session_id,
                    user_id=sess.user_id,
                    issued_at=sess.issued_at.replace(tzinfo=None),
                    expires_at=sess.expires_at.replace(tzinfo=None),
                    last_seen=sess.last_seen.replace(tzinfo=None),
                    ua_hash=sess.ua_hash,
                    ip_net=sess.ip_net,
                    attrs=sess.attrs,
                )
                db.add(ws)
            db.commit()

    def delete(self, sid: str) -> None:
        with self.session_factory() as db:
            ws = db.query(WebSession).filter(WebSession.session_id == sid).first()
            if ws:
                db.delete(ws)
                db.commit()

class SessionManager:
    def __init__(self, store: SessionStore, settings: SessionSettings):
        self.store = store
        self.settings = settings

    def _is_https(self, request: Request) -> bool:
        return request.scope.get("scheme", "http") == "https"

    def _cookie_name(self, request: Request) -> str:
        if self._is_https(request) and self.settings.secure_cookies:
            return "__Host-" + self.settings.cookie_name
        return self.settings.cookie_name

    def _cookie_kwargs(self, request: Request, http_only=True) -> Dict[str, Any]:
        https = self._is_https(request)
        secure = self.settings.secure_cookies and https
        if not https and not self.settings.dev_allow_insecure_on_localhost:
            raise HTTPException(status_code=500, detail="Refusing to set cookies without HTTPS.")
        return {"httponly": http_only, "secure": secure, "samesite": self.settings.samesite, "path": "/"}

    def _binding(self, request: Request) -> Dict[str, Optional[str]]:
        ua_hash = _hash(request.headers.get("user-agent")) if self.settings.bind_user_agent else None
        client_ip = request.client.host if request.client else None
        ip_net = _ip_prefix(client_ip, self.settings.bind_ip_prefix_cidr)
        return {"ua_hash": ua_hash, "ip_net": ip_net}

    def issue(self, response: Response, request: Request, user_id: str) -> "Session":
        now = _now()
        ttl = timedelta(hours=self.settings.absolute_ttl_hours)
        sid = _rand_b64(32)
        csrf = _rand_b64(32)
        b = self._binding(request)
        sess = Session(
            session_id=sid, user_id=user_id,
            issued_at=now, last_seen=now, expires_at=now + ttl,
            ua_hash=b["ua_hash"], ip_net=b["ip_net"],
        )
        sess.attrs["csrf"] = csrf
        self.store.put(sess)
        response.set_cookie(self._cookie_name(request), sid, **self._cookie_kwargs(request, http_only=True))
        response.set_cookie(self.settings.csrf_cookie_name, csrf, **self._cookie_kwargs(request, http_only=False))
        return sess

    def ensure(self, request: Request, response: Response, user_id: str = "local-user") -> "Session":
        try:
            return self.fetch_valid_session(request, require_csrf=False)
        except HTTPException:
            return self.issue(response, request, user_id=user_id)

    def _validate_binding(self, sess: "Session", request: Request) -> None:
        if self.settings.bind_user_agent and sess.ua_hash:
            if not hmac.compare_digest(sess.ua_hash, _hash(request.headers.get("user-agent"))):
                raise HTTPException(status_code=401, detail="Session client binding mismatch.")
        if self.settings.bind_ip_prefix_cidr and sess.ip_net:
            cur = _ip_prefix(request.client.host if request.client else "", self.settings.bind_ip_prefix_cidr)
            if not cur or not hmac.compare_digest(sess.ip_net, cur):
                raise HTTPException(status_code=401, detail="Session network binding mismatch.")

    def _validate_csrf(self, sess: "Session", request: Request) -> None:
        header = request.headers.get("X-CSRF-Token")
        cookie = request.cookies.get(self.settings.csrf_cookie_name)
        expected = sess.attrs.get("csrf")
        supplied = header or cookie
        if not supplied or not expected or not hmac.compare_digest(str(supplied), str(expected)):
            raise HTTPException(status_code=403, detail="CSRF token invalid or missing.")

    def fetch_valid_session(self, request: Request, require_csrf: bool) -> "Session":
        sid = request.cookies.get(self._cookie_name(request))
        if not sid:
            raise HTTPException(status_code=401, detail="Missing session cookie.")
        sess = self.store.get(sid)
        if not sess:
            raise HTTPException(status_code=401, detail="Invalid session.")
        now = _now()
        if now >= sess.expires_at:
            self.store.delete(sess.session_id)
            raise HTTPException(status_code=401, detail="Session expired.")
        idle = timedelta(minutes=self.settings.idle_timeout_minutes)
        if now - sess.last_seen > idle:
            self.store.delete(sess.session_id)
            raise HTTPException(status_code=401, detail="Session idle timeout.")
        self._validate_binding(sess, request)
        if require_csrf and request.method not in SAFE_METHODS:
            self._validate_csrf(sess, request)
        if self.settings.refresh_on_activity:
            sess.last_seen = now
            self.store.put(sess)
        return sess

class SessionValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, manager: SessionManager, settings: SessionSettings):
        super().__init__(app)
        self.manager = manager
        self.settings = settings

    def _is_allowed(self, path: str) -> bool:
        if path in self.settings.allow_paths:
            return True
        return any(path.startswith(p) for p in self.settings.allow_path_prefixes)

    async def dispatch(self, request: Request, call_next):
        if self._is_allowed(request.url.path):
            return await call_next(request)
        try:
            sess = self.manager.fetch_valid_session(request, require_csrf=True)
            request.state.user_id = sess.user_id
            request.state.session = sess
        except HTTPException as e:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": e.detail}, status_code=e.status_code)
        return await call_next(request)

def build_session_router() -> APIRouter:
    r = APIRouter()
    @r.get("/healthz")
    async def healthz():
        return PlainTextResponse("ok")
    return r

def setup_auth(app, settings: Optional[SessionSettings] = None):
    settings = settings or load_settings_from_config()
    # Persist sessions in the SQL database instead of the filesystem
    store = DBSessionStore()
    manager = SessionManager(store, settings)
    app.add_middleware(SessionValidationMiddleware, manager=manager, settings=settings)
    app.include_router(build_session_router())
    app.state.session_manager = manager
    app.state.session_settings = settings
    return manager, settings
