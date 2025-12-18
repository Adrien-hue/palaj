# core/application/services/qualification_service.py
from typing import List

from core.application.ports import (
    AgentRepositoryPort,
    PosteRepositoryPort,
    QualificationRepositoryPort,
)
from core.domain.entities import Qualification

class QualificationService:
    """
    Service applicatif :
    - Coordonne les repositories Qualification / Agent / Poste
    - Enrichit les entités si nécessaire
    - Délègue la validation métier au QualificationValidatorService
    """

    def __init__(
        self,
        agent_repo: AgentRepositoryPort,
        poste_repo: PosteRepositoryPort,
        qualification_repo: QualificationRepositoryPort,
    ):
        self.agent_repo = agent_repo
        self.poste_repo = poste_repo
        self.qualification_repo = qualification_repo

    # =========================================================
    # 🔹 Chargement
    # =========================================================
    def list_qualifications(self) -> List[Qualification]:
        """Retourne toutes les qualifications (niveau entité)."""
        return self.qualification_repo.list_all()

    def list_for_agent(self, agent_id: int) -> List[Qualification]:
        """Retourne toutes les qualifications d'un agent."""
        return self.qualification_repo.list_for_agent(agent_id)

    def list_for_poste(self, poste_id: int) -> List[Qualification]:
        """Retourne toutes les qualifications d'un poste."""
        return self.qualification_repo.list_for_poste(poste_id)
    
    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_qualification_complet(self, agent_id: int, poste_id: int) -> Qualification | None:
        """
        Récupère une qualification enrichi avec son agent et son poste.
        """
        qualification = self.qualification_repo.get_for_agent_and_poste(agent_id, poste_id)
        if not qualification:
            return None

        qualification.set_agent(self.agent_repo.get_by_id(qualification.agent_id))
        
        qualification.set_poste(self.poste_repo.get_by_id(qualification.poste_id))

        return qualification

    def list_qualifications_complets(self) -> List[Qualification]:
        """Retourne tous les régimes sous forme d'entités métier."""
        qualifications = self.qualification_repo.list_all()

        for q in qualifications:
            q.set_agent(self.agent_repo.get_by_id(q.agent_id))
        
            q.set_poste(self.poste_repo.get_by_id(q.poste_id))

        return qualifications
    
    # =========================================================
    # 🔹 Vérifications
    # =========================================================
    def is_qualified(self, agent_id: int, poste_id: int) -> bool:
        """Vérifie si un agent est qualifié pour un poste."""
        return self.qualification_repo.is_qualified(agent_id, poste_id)