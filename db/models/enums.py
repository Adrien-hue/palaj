# db/models/enums.py
from enum import Enum

class TypeJourDB(str, Enum):
    ABSENCE = "absence"
    CONGE = "conge"
    POSTE = "poste"
    REPOS = "repos"
    ZCOT = "zcot"
    INCONNU = "inconnu"
