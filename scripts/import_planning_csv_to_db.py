import csv
from datetime import datetime, date, timedelta
from core.domain.entities import Agent, Affectation

from db.repositories import agent_repo, affectation_repo, tranche_repo

SAVE = True

# Dictionnaire de correspondance mois abrégés français → numéro
MOIS_FR = {
    "janv": 1,
    "févr": 2,
    "mars": 3,
    "avr": 4,
    "mai": 5,
    "juin": 6,
    "juil": 7,
    "août": 8,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "déc": 12,
}

TRANCHES_ALIASES = {
    "CM2 VM": "CM2",
    "GIVSOLM/": "GIVSOLM",
    "GIVSOLS/": "GIVSOLS",
    "R/LIVM1P": "RLIVM1P",
    "R/LIVS1P": "RLIVS1P",
    "R/LIVN1P": "RLIVN1P",
    "R/LIVM2P": "RLIVM2P",
    "R/LIVM6P": "RLIVM6P",
    "R/LIVM7P": "RLIVM7P",
    "R/LIVS3P": "RLIVS3P",
    "R/LIVS6P": "RLIVS6P",
    "R/LIVN6P": "RLIVN6P",
    "RLIVSP4P": "RLIVS4P",
    
    "NU/X2": "GTI N",
    "RP/X2": "GTI N",
    "X2": "GTI N",
    "S2": "GTI S",
    "-2": "GTI M",
    "-2 (AVEC AURORE)": "GTI M",
    "-2 ( AVEC AURORE)": "GTI M",
    "-2 (AVEC AURORE)": "GTI M",
    "-2 (AVEC CÉDRIC)": "GTI M",
    "M": "A GTI M",
    "M AGTI": "A GTI M",
    "M\nENTRETIEN 10H": "A GTI M",
    "M (LUDO EN \nDOUBLE)": "A GTI M",
    "M (LUDO EN DOUBLE)": "A GTI M",
    "M (PUIS KARINE)": "A GTI M",
    "S": "A GTI S",
    "S?": "A GTI S",
    "S (EFP)": "A GTI S",
    "S(12H)": "A GTI S",
    "S EIA": "A GTI S",
    "S (VM 14H)": "A GTI S",
    "S (DOUBLON\nDELPHINE)": "A GTI S",
    "S (GCA 14H-16H30)": "A GTI S",
    "S (10H-18H)": "A GTI S",
    "RP/X2 GM": "NJ",
    "X2 GM": "NJ",
}

def parse_date_francaise(jour_str: str, annee: int = 2025) -> date:
    """
    Convertit une date française abrégée (ex: '30-janv') en objet date.
    """
    jour_str = jour_str.strip().lower().replace(".", "").replace(" ", "")
    try:
        # ex: "30-janv"
        jour_part, mois_part = jour_str.split("-")
        mois_num = MOIS_FR[mois_part]
        return date(annee, mois_num, int(jour_part))
    except Exception as e:
        raise ValueError(f"Format de date invalide: '{jour_str}' ({e})")

#   UPSERT Agent
def upsert_agent(full_name: str):
    """
    Crée ou met à jour un Agent existant à partir du nom complet.
    Recherche sur le nom complet (ex: "Julie MARTIN").
    """
    if not full_name or not full_name.strip():
        raise ValueError("Le nom complet de l'agent ne peut pas être vide")

    parts = full_name.strip().split(" ", 1)
    prenom = parts[0].capitalize()
    nom = parts[1].upper()

    # Recherche d'un agent existant
    existing_agent = None
    if hasattr(agent_repo, "get_by_full_name"):
        existing_agent = agent_repo.get_by_full_name(nom=nom, prenom=prenom)

    if existing_agent:
        # Vérifie si des données doivent être mises à jour
        existing_agent = existing_agent

        updated = False
        
        if prenom and existing_agent.prenom != prenom:
            existing_agent.prenom = prenom
            updated = True
        if existing_agent.nom != nom:
            existing_agent.nom = nom
            updated = True

        if updated and SAVE and hasattr(agent_repo, "update"):
            agent_repo.update(existing_agent)
            # print(f"🟡 Agent mis à jour : {prenom} {nom}")
        else:
            print(f"✅ Agent existant trouvé : {prenom} {nom}")

        return existing_agent

    # Création d’un nouvel agent
    agent = Agent(
        id=hash(full_name) % 100000,
        prenom=prenom,
        nom=nom,
    )
    
    if SAVE:
        agent_repo.create(agent)
        print(f"🆕 Nouvel agent ajouté : {prenom} {nom}")
    # else:
    #     print(f"🧩 (Simulation) Agent à créer : {prenom} {nom}")

    return agent

#   UPSERT EtatJourAgent
def upsert_etat_jour_agent(agent_id, jour, type_jour):
    """Crée ou met à jour un EtatJourAgent existant pour le couple (agent, jour)."""
    existing = etat_jour_agent_repo.get_for_agent_and_day(agent_id, jour) if hasattr(etat_jour_agent_repo, "get_for_agent_and_day") else None
    if existing:
        if existing.type_jour != type_jour:

            existing.type_jour = type_jour
            if SAVE:
                etat_jour_agent_repo.update(existing)
        return existing
    else:
        etat = EtatJourAgent(agent_id, jour, type_jour)
        if SAVE:
            etat_jour_agent_repo.create(etat)
        #     print(f"🆕 Nouvel état journalier ajouté : {agent_id} {jour} {type_jour}")
        # else:
        #     print(f"🧩 (Simulation) État journalier à créer : {agent_id} {jour} {type_jour}")
        return etat


def upsert_affectation(agent_id, jour, tranche_id):
    """Crée ou met à jour une Affectation existante pour le couple (agent, jour)."""
    existing = affectation_repo.get_for_agent_and_day(agent_id, jour)
    if existing:
        if existing.tranche_id != tranche_id:
            # print(f"🔄 Mise à jour de l'affectation : {existing.tranche_id} → {tranche_id}")
            existing.tranche_id = tranche_id
            if SAVE:
                affectation_repo.update(existing)
        return existing
    else:
        affect = Affectation(agent_id, tranche_id, jour)
        if SAVE:
            affectation_repo.create(affect)
        #     print(f"🆕 Nouvel affectation ajouté : {agent_id} {jour} {tranche_id}")
        # else:
        #     print(f"🧩 (Simulation) Affectation à créer : {agent_id} {jour} {tranche_id}")
        return affect

def import_planning_csv_to_db(
    filepath: str,
    repos_codes: list[str],
    travail_codes: list[str],
    zcot_codes: list[str],
    conge_codes: list[str],
    absence_codes: list[str],
    encoding: str = "utf-8"
):
    """
    Importe un fichier de planning CSV dans la base :
    - crée les agents
    - insère les états journaliers
    - insère les affectations si nécessaire
    - vérifie la cohérence du calendrier (1er janv → 31 déc)
    """

    print(f"\n📂 Import du fichier : {filepath}")

    with open(filepath, newline="", encoding=encoding) as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    if not rows:
        print("❌ Fichier vide.")
        return

   # --- Vérification des dates ---
    raw_dates = rows[0][1:]
    try:
        dates = [parse_date_francaise(d) for d in raw_dates]
    except ValueError as e:
        raise ValueError(f"❌ Erreur de parsing des dates : {e}")

    # 1️⃣ Vérifier le nombre de jours
    expected_start = date(2025, 1, 1)
    expected_end = date(2025, 12, 31)
    expected_count = (expected_end - expected_start).days + 1

    if len(dates) != expected_count:
        print(f"❌ Le fichier contient {len(dates)} colonnes de dates, attendu : {expected_count} (du 01/01/2025 au 31/12/2025)")

    # 2️⃣ Vérifier l’ordre et la continuité
    for i in range(1, len(dates)):
        expected_next = dates[i - 1] + timedelta(days=1)
        if dates[i] != expected_next:
            raise ValueError(
                f"❌ Discontinuité détectée entre {dates[i - 1]} et {dates[i]} (attendu : {expected_next})."
            )

    if dates[0] != expected_start or dates[-1] != expected_end:
        print(f"❌ Les dates doivent couvrir toute l’année 2025 (début {dates[0]}, fin {dates[-1]}).")

    print(f"✅ Vérification des dates : {dates[0]} → {dates[-1]} ({len(dates)} jours)")

    # --- Import des agents et jours ---
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue

        full_name = row[0].strip()

        agent = upsert_agent(full_name)

        affect_none = 0
        for i, code in enumerate(row[1:]):
            jour = dates[i]
            code_norm = code.strip().upper()

            etat = None

            if not code_norm or code_norm == "":
                affect_none += 1
                continue

             # --- Déterminer le type de jour ---
            if code_norm in repos_codes:
                etat = EtatJourAgent(agent.id, jour, TypeJour.REPOS)

            elif code_norm in travail_codes or code_norm in TRANCHES_ALIASES:
                etat = EtatJourAgent(agent.id, jour, TypeJour.POSTE)

                # Gestion automatique des tranches
                if code_norm in TRANCHES_ALIASES:
                    original_code = code_norm
                    code_norm = TRANCHES_ALIASES[code_norm]
                    print(f"↪️  Alias détecté : '{original_code}' → '{code_norm}'")
                tranche = tranche_repo.get_by_name(code_norm) if hasattr(tranche_repo, "get_by_name") else None
                if not tranche:
                    print(f"🆕 Nouvelle tranche à créer : {code_norm}")
                else:
                    # Création de l'affectation
                    upsert_affectation(agent.id, jour, tranche.id)
                        
            elif code_norm in zcot_codes:
                etat = EtatJourAgent(agent.id, jour, TypeJour.ZCOT)
            elif code_norm in conge_codes:
                etat = EtatJourAgent(agent.id, jour, TypeJour.CONGE)
            elif code_norm in absence_codes:
                etat = EtatJourAgent(agent.id, jour, TypeJour.ABSENCE)
            else:
                print(f"⚠️  Code inconnu '{code_norm}' pour {agent.get_full_name()} le {jour}")
                continue

            upsert_etat_jour_agent(agent.id, jour, etat.type_jour)

        print(f"📅 Jours sans affectation pour {agent.get_full_name()} : {affect_none}")

    print("\n✅ Import terminé avec succès.")

if __name__ == "__main__":
    print("=======================================")
    print("        Intégration des données        ")
    print("=======================================")

    GTI_FILE_PATH = "data/prepared/Planning_2025(GTI).csv"
    GM_FILE_PATH = "data/prepared/Planning_2025(GM).csv"
    GIPV_FILE_PATH = "data/prepared/Planning_2025(GIPV).csv"
    GIV_FILE_PATH = "data/prepared/Planning_2025(GIV).csv"
    RLIV_FILE_PATH = "data/prepared/Planning_2025(RLIV).csv"

    CODE_CONGES = [
        'AZ',
        'AC',
        'C',
        'C24',
        'C25',
        'CD',
        'CN',
        'CP',
        'CS',
        'VT',
        'F',
        'FE',
        'FV',
        'FV/',
        'AY',
        '0,00\xa0F',
        '1,00\xa0F',
        '2,00\xa0F',
        '-2,00\xa0F',
        '3,00\xa0F',
        '4,00\xa0F',
        'F4/',
        '5,00\xa0F',
        '6,00\xa0F',
        '7,00\xa0F',
        '8,00\xa0F',
        '9,00\xa0F',
        'RU',
        'C?',
        'TY',
        'RP/C25',
        'RP/C',
    ]

    CODE_REPOS = [
        'RQ',
        'RP',
        'RP/',
        'RN',
        'RN',
        'RP',
        '/',
    ]

    CODE_ABS = [
        'ABS',
        'MA',
        'AM',
        'DC',
        'EM',
        'D2I',
        'AT',
    ]


    # gti_code_unique = extract_unique_codes(GTI_FILE_PATH)

    # print("Codes GTI uniques extraits :")
    # print(gti_code_unique)

    CODE_POSTE_GTI = [
        'NU/X2',
        'RP/X2',
        'X2',
        'S2',
        '-2',
        '-2 (AVEC AURORE)',
        '-2 ( AVEC AURORE)',
        '-2 (AVEC AURORE)',
        '-2 (AVEC CÉDRIC)',
        'MJ',
        'SJ',
        'ML',
        'SL',
        'NL',
        'M',
        'M AGTI',
        'M\nENTRETIEN 10H',
        'M (LUDO EN \nDOUBLE)',
        'M (LUDO EN DOUBLE)',
        'M (PUIS KARINE)',
        'S',
        'S?',
        'S (EFP)',
        'S(12H)',
        'S EIA',
        'S (VM 14H)',
        'S (DOUBLON\nDELPHINE)',
        'S (GCA 14H-16H30)',
        'S (10H-18H)',
        'RP/X2 GM',
        'X2 GM',
    ]

    CODE_ZCOT_GTI = [
        'F GTI X2',
        'VISITE J',
        'FORM AGTI S',
        'F GTI-2',
        'FORM AGTI (S)',
        'PRÉPA FORM (M?)',
        'FORM GTI (M) EIPP',
        'PRÉPA FORM JD ?',
        'FORMATION POWERAPPS',
        'DIR TN',
        'J AMB CADRE',
        'DOUBLE DPX',
        'POINT FORMATION KAICHI (10H)',
        'FORMATION POINT KAICHI',
        'PRÉPA FORM (JUSQUE 19H)',
        'J (FORM)',
        'J POINT KAICHI',
        'FORMATION SST',
        'Z JOURNÉE',
        'TOPO PCAT-COT (9H-12H)',
        'PRÉPA FORM\n(DE MATINÉE ?)',
        'CCU VINCENNES',
        'FORM GTI (J)',
        'F GTI J (GRÉGOIRE)',
        'FORM GIPV.S',
        'FORM.SHAREPOINT',
        'EIA DPX GM',
        'IMMERSION COS',
        'IMMERSION COS ATL',
        'VISITE ACHÈRES',
        'J FORM -2',
        'FORM MS',
        'EXO CCU A',
        'J FORM TEDDY',
        'FORM GTI (S)',
        'F GTI J (VALENTIN)',
        'FORM GM.M',
        'PRÉPA FORM + VM',
        'FORM AGTI',
        'FORM GTI S',
        'FORM AGTI M',
        'Z SOIRÉE',
        'OBSERVATEUR FORM',
        'Z MATINÉE + EXO',
        'FORMATION JD',
        'JOURNÉE COT',
        'RÉU JC',
        'TESTS RECRUT.',
        'J DINER',
        'SST',
        'M DINER',
        'GCA ?',
        'CCU A DOUBLE',
        'J (FORM VAL)',
        'REXAL3\n(VINCENNES)',
        'FORM AGTI M\nEXO DEMANDE SECOURS (10H-11H30)',
        'FORMATION',
        'FORM.SST',
        'F X2',
        'PRÉPA FORM (GTI INIT) ANTOINE TROUVE',
        'ACCUEIL',
        'EICP GTI',
        'J (VINCENNES)',
        'J',
        'RP/FX2',
        'RDV VM',
        'IMMERSION COS SE',
        'TOPO UMT \nBREHAT2',
        'FORM.TSAE1',
        'FX2',
        'FORM GIPV.M',
        'M (FORM GTI)',
        'FORM.SEE TRAINS',
        'M (TOPO PCAT-COT)',
        'ECHANGE COT - PTC',
        'J (FORM GRÉG)',
        'F EMPRISE',
        'F RP/X2',
        'J (EXO GTI) 9H DÉBUT',
        'VISITE',
        'FORM GTI M EIA',
        'J EIA',
        'F GTI -2',
        'FORM GM.S',
        'RP/F GTI X2',
        'J (VND)',
        'TOPO PCAT-COT\nPOUR SA2026',
        'PETIT DEJ PROD',
        'RP/FGTI X2',
        'M?',
        'Z MATINÉE + AC',
        'M (EFP)',
        'FORMATION EX ZD',
        'J (E-LEARNING + EIA)',
        'M (FORM GTI)\nENTRETIEN 10H',
        'SEE-TRAINS UMT',
        'JPROD',
        'EICP',
        'PRÉPA FORM',
        'CPAT',
        'J (M DOUBLE MATINÉE TEDDY)',
        'VISITE PACTN',
        'FORMATION PW.APP',
        'FORM SST',
        'EIA',
        'Z MATINÉE',
        'F GTI S2',
        'FGTI X2',
        'PRÉPA FORM (GCA)',
        'J (ASSESSMENT)',
        'FORM GTI (M)',
        'VISITE IC',
        'VALIDATION',
        'J ORAL BLANC INTERNE',
        'TOPO PCAT-COT',
        'JOURNÉE',
        'F GTI J (VENOTH)',
        'PRÉPA FORM THÉO',
        'DAC JESSICA',
        'PRÉPA FORM AURORE',
        'DLA',
        'JOURNÉE DPX',
        'FGTI -2',
        'FORM GTI M',
        'PAC TN',
        'J PACT',
        'REXAL3\n(9H-12H)',
        'J (GCA 10H-12H30)',
        'UMT',
        'EIPP',
        'J CIAT',
        'J?',


        'NU',
    ]

    import_planning_csv_to_db(
        filepath=GTI_FILE_PATH,
        repos_codes=CODE_REPOS,
        travail_codes=CODE_POSTE_GTI,
        zcot_codes=CODE_ZCOT_GTI,
        conge_codes=CODE_CONGES,
        absence_codes=CODE_ABS,
    )

    # gm_code_unique = extract_unique_codes(GM_FILE_PATH)

    # print("Codes GM uniques extraits :")
    # print(gm_code_unique)

    CODE_POSTE_GM = [
        'MJ',
        'SJ',
        'NJ',
        'ML',
        'SL',
        'NL',
    ]

    CODE_ZCOT_GM = [
        'FORM GESTION DE CRISE',
        'ECHANGE COT - PTC',
        'VISITE J',
        'F-NJ',
        'OBSERVATEUR FORM',
        'FORM  AID-GTI',
        'GM ENGIN SOIRÉE',
        'F-NL',
        'FORM',
        'MISSION',
        'F-SAGTI',
        'Z COT',
        'REMPLACEMENT EIA',
        'SOIRÉE GM ENGIN',
        'PAC TN',
        'F-MJ',
        'J + GM ENGIN',
        'SET',
        'VISITE',
        'VISITE L',
        'FORM  SST',
        'F-SL',
        'FORM ST DENIS',
        'GM E M',
        'F-SJ- EIA',
        'M GM ENGIN',
        'SL - EIA',
        'F-MAGTI',
        'F-ML',
        'C-CET',
        'EXO CRISE',
        'ZCOT',
        'ENTRETIEN',
        'CEGOS',
        'RENF S',
        'VISITE ORDO',
        'FORM CESI',
        'JOURNÉE',
        'SVCO',
        'F GM E',
        'F-SJ',
        'DBLE MJ',
        'DOUBLE',
        'MJ + VM',
        'DD',
        'SL-EIA',
        'VALIDATION',
        'RENF M',
        'MJ-EIA',
        'SOEN',
        'VMS',
        'SET VND',
        'VM',
        '3276',
        'EM',
        'ME',
        'TOPO PCAT-COT?',


        'NU',
    ]

    import_planning_csv_to_db(
        filepath=GM_FILE_PATH,
        repos_codes=CODE_REPOS,
        travail_codes=CODE_POSTE_GM,
        zcot_codes=CODE_ZCOT_GM,
        conge_codes=CODE_CONGES,
        absence_codes=CODE_ABS,
    )

    # gipv_code_unique = extract_unique_codes(GIPV_FILE_PATH)

    # print("Codes GIPV uniques extraits :")
    # print(gipv_code_unique)

    CODE_POSTE_GIPV = [
        'GIPVM1',
        'GIPVS1',
        'GIPVN1',
        'CM1',
        'CM2',
        'CM2 VM',
    ]

    CODE_ZCOT_GIPV = [
        'ZCOT',
        'ZCOTF',
        'GIPVMZ',
        'GIPVSZ',
        'FGIPVM1',
        'FGIPVS1',
        'FGIPVN1',



        'NU',
    ]

    import_planning_csv_to_db(
        filepath=GIPV_FILE_PATH,
        repos_codes=CODE_REPOS,
        travail_codes=CODE_POSTE_GIPV,
        zcot_codes=CODE_ZCOT_GIPV,
        conge_codes=CODE_CONGES,
        absence_codes=CODE_ABS,   
    )

    # giv_code_unique = extract_unique_codes(GIV_FILE_PATH)

    # print("Codes GIV uniques extraits :")
    # print(giv_code_unique)

    CODE_POSTE_GIV = [
        'GIVICSM',
        'GIVICSS',
        'GIVSOLM',
        'GIVSOLM/',
        'GIVSOLS',
        'GIVSOLS/',
    ]

    CODE_ZCOT_GIV = [
        'ZCOTE',
        'ZCOT VM',
        'ZCOTM/ VIS MA VIE AGTI',
        'ZCOTM/',
        'DAC',
        'FGIVICSM',
        'FGIVSOLM',
        'GIVSOLM?',
        'PIVIFMTE',
        'ZCOTSF',
        'ZCOTVM',
        'ZCOTTT',
        'ZCOT 10H00',
        'CESI',
        'EIA',
        'ZCOTS',
        'ZCOTLJ',
        'ZJPROD',
        'ZCOTJ'
        'ZCOTS/',
        'ZPPU',
        'ZCOTF',
        'ZCOTT',
        'ZCOT',
        'FGIVSOLS',
        'FGIVICSS',
        'VPPUS',
        'ZCOTM/S',
        'FZCOTM',
        'ZCOTM',
        'ZCOTPSL',
        'SST',
        'VINCENNES',
        'CCUA / M',
        'CCUA',
        'TESTPSL',
        'TR',
        'ZCOTJ',
        'ZCOTS/',


        'NU',
    ]

    import_planning_csv_to_db(
        filepath=GIV_FILE_PATH,
        repos_codes=CODE_REPOS,
        travail_codes=CODE_POSTE_GIV,
        zcot_codes=CODE_ZCOT_GIV,
        conge_codes=CODE_CONGES,
        absence_codes=CODE_ABS,   
    )

    # rliv_code_unique = extract_unique_codes(RLIV_FILE_PATH)

    # print("Codes RLIV uniques extraits :")
    # print(rliv_code_unique)

    CODE_POSTE_RLIV = [
        'RLIVM1P',
        'R/LIVM1P',
        'RLIVS1P',
        'R/LIVS1P',
        'RLIVN1P',
        'R/LIVN1P',
        'RLIVM2P',
        'R/LIVM2P',
        'RLIVS3P',
        'R/LIVS3P',
        'RLIVM4P',
        'RLIVS4P',
        'RLIVSP4P',
        'RLIVM6P',
        'R/LIVM6P',
        'RLIVS6P',
        'R/LIVS6P',
        'RLIVN6P',
        'R/LIVN6P',
        'RLIVM7P',
        'R/LIVM7P',
        'RLIVS8P',
        'PIM001',
        'PIM002',
        'COIVMP',
        'COIVSP',
        'COIVZP',
    ]

    CODE_ZCOT_RLIV = [
        'EVAL',
        'R/LIVMZP',
        'RLIVSZP',
        'R/LIVSZP',
        'RLIVSZ',
        'NU',
        'FORM/S',
        'FORM/M J',
        'DETACHE',
        'DETACHEE',
        'DETACHÉE',
        'DETACHEMENT',
        'FORM/M L',
        'FORMATION',
        'FMZP',
        'FORM/S J',
        'ACCUEIL',
        'FORM/S L',
        'FORM/M',
        'VMVMZ',
        'ZCOT',
        'VM',
        'FOR/IMS',
        'FORM',
        'VMVS6P',
        '?',
        'TTSZP',
        'WO',
        'SST',
        'COIVMZP',
        'COIVSZP',
        'PATO',
        'TRACTION',
        'FOR',
        'VERTIGO',
        'BFME',
        'VMVS1P',
        'RETOUR',
        'Z',
        'VMVSZP',
        'TTMZP',
        'FM6P',
        'VMV',
        'TTS1P',
        'VMVS3P',
        'VMVM6P',
        'GM',
    ]

    import_planning_csv_to_db(
        filepath=RLIV_FILE_PATH,
        repos_codes=CODE_REPOS,
        travail_codes=CODE_POSTE_RLIV,
        zcot_codes=CODE_ZCOT_RLIV,
        conge_codes=CODE_CONGES,
        absence_codes=CODE_ABS,   
    )

    exit()