import unicodedata

def normalize_text(s: str | None) -> str | None:
    """
    Normalise un texte pour les comparaisons :
      - Supprime les accents
      - Convertit en minuscules
      - Supprime les espaces superflus

    :param s: Chaîne à normaliser
    :return: Chaîne normalisée ou None
    """
    if not s:
        return None

    # Décomposition Unicode : é → e + ́
    s = unicodedata.normalize("NFD", s)
    # Suppression des marques d'accent (catégorie Mn)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Trim + minuscule
    return s.strip().lower()
