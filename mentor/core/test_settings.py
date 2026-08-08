from mentor.core.settings import *  # noqa: F401,F403

# Tests run against an in-memory SQLite database so the suite has no
# dependency on a running Postgres instance.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
