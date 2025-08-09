# config.py
SESSION_IDLE_TIMEOUT_MINUTES = 15
SESSION_ABSOLUTE_TTL_HOURS = 8
SESSION_REFRESH_ON_ACTIVITY = True

SESSION_COOKIE_NAME = "session_id"        # auto becomes __Host-session_id on HTTPS
CSRF_COOKIE_NAME = "csrf_token"
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_SECURE_COOKIES = True             # keep True in prod
DEV_ALLOW_INSECURE_COOKIES = True         # allows HTTP-only on localhost

SESSION_BIND_USER_AGENT = True
SESSION_BIND_IP_PREFIX_CIDR = None        # e.g., 24 to bind /24

AUTH_ALLOW_PATHS = {"/", "/begin", "/docs", "/openapi.json", "/healthz", "/favicon.ico"}
AUTH_ALLOW_PATH_PREFIXES = {"/static"}
SESSION_DIR = "user_sessions"
