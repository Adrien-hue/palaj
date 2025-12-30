# db/__init__.py
from db.database import SQLiteDatabase

# Base globale
db = SQLiteDatabase("data/palaj.db", debug=False, echo=False)
