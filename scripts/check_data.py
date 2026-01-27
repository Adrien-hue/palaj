"""
Script de vérification complète de la cohérence des données.
Exécution :
    python -m scripts.check_data
"""

from core.data_integrity_checker import DataIntegrityChecker

# === Import des services ===
from core.domain.services.agent_service import AgentService
from core.domain.services.poste_validator_service import PosteValidatorService
from core.domain.services.tranche_service import TrancheService
from core.domain.services.qualification_service import QualificationService
from core.domain.services.regime_service import RegimeService

# === Import de la BDD ===
from db.database import JsonDatabase

# === Import des repositories ===
from db.repositories.agent_repo import AgentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.tranche_repo import TrancheRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.regime_repo import RegimeRepository


def main():
    # --- Initialisation de la BDD ---
    db = JsonDatabase()

    # --- Initialisation des repositories ---
    agent_repo = AgentRepository(db)
    poste_repo = PosteRepository(db)
    tranche_repo = TrancheRepository(db)
    qualification_repo = QualificationRepository(db)
    affectation_repo = AffectationRepository(db)
    regime_repo = RegimeRepository(db)

    # --- Instanciation des services ---
    agent_service = AgentService(agent_repo)
    poste_service = PosteValidatorService(poste_repo, tranche_repo)
    tranche_service = TrancheService(tranche_repo)
    qualification_service = QualificationService(qualification_repo, agent_repo, poste_repo)
    regime_service = RegimeService(regime_repo)

    # --- Création du checker global ---
    checker = DataIntegrityChecker(
        agent_service=agent_service,
        poste_service=poste_service,
        tranche_service=tranche_service,
        qualification_service=qualification_service,
        regime_service=regime_service,
    )

    # --- Exécution et affichage du rapport ---
    is_valid = checker.run_all_checks()
    checker.print_report()

    if not is_valid:
        print("🚨 Des erreurs ont été détectées !")
    else:
        print("✅ Données cohérentes, tout est prêt.")


if __name__ == "__main__":
    main()
