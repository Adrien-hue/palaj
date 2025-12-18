import csv
from pathlib import Path

def extract_unique_codes(filepath: str | Path) -> set[str]:
    """
    Analyse un fichier de planning (format CSV semi-structuré)
    et retourne l'ensemble des codes distincts trouvés dans toutes les cellules.

    Exemple d'utilisation :
    >>> extract_unique_codes("data/planning_janvier.csv")
    {'SJ', 'MJ', 'NJ', 'RP', 'RN', 'RU', 'C', 'FORM  AID-GTI'}
    """
    codes: set[str] = set()

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    # On saute la première ligne (en-têtes de dates)
    for row in rows[1:]:
        for cell in row[1:]:  # on ignore la colonne du nom
            code = cell.strip()
            if not code:
                continue

            # normalisation légère
            normalized = code.upper().replace(" ", " ").strip()  # supprime espaces bizarres
            codes.add(normalized)

    return codes


if __name__ == "__main__":
    path = input("Chemin du fichier CSV à analyser : ").strip('"')
    if not path:
        print("[ERROR] Aucun fichier spécifié.")
        exit(1)

    unique_codes = extract_unique_codes(path)
    print("\n📊 Codes distincts trouvés dans le fichier :")
    for c in sorted(unique_codes):
        print(f" - {c}")

    print(f"\nTotal : {len(unique_codes)} codes uniques.")
