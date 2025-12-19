# db/__init__.py
from db.database import SQLiteDatabase

# Base globale
db = SQLiteDatabase("data/planning.db", debug=False, echo=False)
