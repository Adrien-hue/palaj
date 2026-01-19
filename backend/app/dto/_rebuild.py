def rebuild_dtos() -> None:
    # Imports runtime (ordre contrôlé)
    from backend.app.dto.regimes import RegimeDTO, RegimeDetailDTO
    from backend.app.dto.agents import AgentDTO, AgentDetailDTO
    from backend.app.dto.qualifications import QualificationDTO

    # Rebuild dans un ordre qui résout les refs
    RegimeDTO.model_rebuild()
    AgentDTO.model_rebuild()
    QualificationDTO.model_rebuild()

    RegimeDetailDTO.model_rebuild()
    AgentDetailDTO.model_rebuild()
