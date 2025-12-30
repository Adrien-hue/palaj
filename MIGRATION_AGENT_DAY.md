# MIGRATION_AGENT_DAY — Plan de refacto PALAJ

## Objectif
Revoir la modélisation “jour d’un agent” pour supprimer les ambiguïtés entre :
- Affectation (liée à une tranche)
- EtatJourAgent (qualifie la nature de la journée)
- WorkDay (présent un peu partout / duplication de logique)

But : une seule source de vérité, plus simple à maintenir, et compatible avec l’existant le temps de migrer.

---

## Legacy (existant)
### Sources / entités
- **Affectation** : lien agent -> tranche travaillée (poste/horaires via tranche)
- **EtatJourAgent** : nature de la journée (repos, congé, zcot, poste, etc.)
- **WorkDay** : agrégat/structure “jour” recréée dans plusieurs endroits (≈160 occurrences / 40 fichiers)

### Problèmes connus
- Double-vérité : la “nature de journée” peut être déduite ou contredite selon les sources
- WorkDay dupliqué / couplage fort front/back / logique dispersée
- Cas “travail hors tranche” (zcot) mal aligné avec le modèle “affectation => tranche”

---

## Nouvelle source de vérité (cible)
### Concept
- **AgentDay (aggregate)** : représente une journée unique pour un agent
  - 1 agent + 1 date
  - porte le **type de jour** + métadonnées
  - expose les **tranches** (si applicable) + “hors tranche” si besoin

### Règles métier (à figer)
- La nature de journée est déterminée par : [AgentDay.type_jour]
- Les tranches sont associées à la journée, pas l’inverse
- Support explicite des journées “hors tranche” (ex: zcot) sans bricolage

---

## Plan de migration
### Étapes
- [ ] (0) Mise en place stratégie git + doc migration (ce fichier)
- [ ] (1) Introduire les modèles/types **AgentDay** (domain + DTO)
- [ ] (2) Ajouter un “adapter/translator” legacy -> AgentDay
- [ ] (3) Migrer 1 endpoint clé (ex: planning agent) pour qu’il retourne AgentDay
- [ ] (4) Migrer progressivement les usages WorkDay
- [ ] (5) Déprécier puis supprimer WorkDay / chemins legacy

---

## État actuel de migration
### Migré
- Aucun

### Non migré / à surveiller
- Toutes les occurrences WorkDay
- Endpoints planning et vues front liées aux jours
- Calculs ou helpers de qualification journée

---

## Notes / décisions
- Feature-flag (oui/non) : TBD
- Stockage “type de jour en base” : prévu (à détailler)
- Compatibilité SQLite / migrations Alembic : à valider au moment des changements DB
