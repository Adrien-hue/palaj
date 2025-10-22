from tabulate import tabulate
from typing import List
from models.planning import Planning
from models.poste import Poste

def afficher_planning_tableau(planning: Planning, postes: List[Poste]):
    """
    Affiche le planning sous forme de tableau :
    - Lignes : dates
    - Colonnes : tranches de tous les postes
    - Cellules : agent affecté
    """
    # Construire la liste de toutes les tranches (colonnes)
    colonnes = []
    for poste in postes:
        for tranche in poste.tranches:
            colonnes.append(f"{poste.nom} {tranche.abbr}")
    
    # Préparer les lignes du tableau
    tableau = []
    for jour in planning.jours:
        ligne = [jour.strftime("%d-%m-%Y")]
        for poste in postes:
            for tranche in poste.tranches:
                # Cherche l'affectation correspondant à ce jour et cette tranche
                aff = next(
                    (a for a in planning.get_affectations_par_jour(jour) if a.tranche == tranche),
                    None
                )
                if aff:
                    ligne.append(aff.agent.get_full_name())
                else:
                    ligne.append("")  # Case vide si pas d'agent
        tableau.append(ligne)
    
    # Préparer les headers : Date + toutes les tranches
    headers = ["Date"] + colonnes
    
    # Afficher le tableau
    print(tabulate(tableau, headers=headers, tablefmt="grid"))
