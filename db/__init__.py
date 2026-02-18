# db/__init__.py
from backend.app.settings import settings
from db.database import Database

db = Database(settings.database_url, debug=False, echo=False)
