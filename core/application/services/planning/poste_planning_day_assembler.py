from datetime import date, timedelta
from typing import Dict, List

from core.domain.entities import Agent, Tranche
from core.domain.entities.agent_day import AgentDay
from core.domain.enums.day_type import DayType
from core.domain.models.poste_planning import PostePlanningDay, PostePlanningTranche


class PostePlanningDayAssembler:
    def assemble(
        self,
        *,
        start_date: date,
        end_date: date,
        tranches: List[Tranche],
        agents_by_id: Dict[int, Agent],
        agent_days: List[AgentDay],
    ) -> List[PostePlanningDay]:
        # Index: date -> tranche_id -> list[agent_id]
        idx: Dict[date, Dict[int, List[int]]] = {}

        for ad in agent_days:
            tranche_ids = ad.tranche_ids
            if not tranche_ids:
                continue

            day_map = idx.setdefault(ad.day_date, {})
            for tranche_id in tranche_ids:
                day_map.setdefault(tranche_id, []).append(ad.agent_id)

        # Build all days with all tranches
        days: List[PostePlanningDay] = []
        cur = start_date
        while cur <= end_date:
            tranches_out: List[PostePlanningTranche] = []

            day_tranche_map = idx.get(cur, {})
            for t in tranches:
                agent_ids = day_tranche_map.get(t.id, [])
                # dedupe keeping order
                seen = set()
                uniq_agent_ids = [x for x in agent_ids if not (x in seen or seen.add(x))]

                agents = [agents_by_id[a_id] for a_id in uniq_agent_ids if a_id in agents_by_id]
                tranches_out.append(PostePlanningTranche(tranche=t, agents=agents))

            # Pour une vue poste, on met des valeurs stables
            days.append(
                PostePlanningDay(
                    day_date=cur,
                    day_type=DayType.WORKING,
                    description=None,
                    is_off_shift=False,
                    tranches=tranches_out,
                )
            )
            cur += timedelta(days=1)

        return days
