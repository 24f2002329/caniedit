from dataclasses import dataclass
import os

from sqlalchemy.orm import Session

from app.db.models.plan import Plan


@dataclass(frozen=True)
class PlanDefinition:
	slug: str
	name: str
	daily_merge_limit: int


DEFAULT_PLAN_SLUG = "starter"


def _env_limit(key: str, default: int) -> int:
	try:
		return int(os.getenv(key, str(default)))
	except ValueError:
		return default


PLAN_DEFINITIONS = [
	PlanDefinition("starter", "Starter", _env_limit("PLAN_STARTER_DAILY_LIMIT", 20)),
	PlanDefinition("individual", "Individual", _env_limit("PLAN_INDIVIDUAL_DAILY_LIMIT", 100)),
	PlanDefinition("team", "Team", _env_limit("PLAN_TEAM_DAILY_LIMIT", 200)),
	PlanDefinition("business", "Business", _env_limit("PLAN_BUSINESS_DAILY_LIMIT", 9999)),
]


def seed_default_plans(db: Session) -> None:
	existing = {plan.slug: plan for plan in db.query(Plan).all()}
	changed = False
	for definition in PLAN_DEFINITIONS:
		plan = existing.get(definition.slug)
		if plan:
			if plan.name != definition.name or plan.daily_merge_limit != definition.daily_merge_limit:
				plan.name = definition.name
				plan.daily_merge_limit = definition.daily_merge_limit
				db.add(plan)
				changed = True
			continue
		plan = Plan(
			slug=definition.slug,
			name=definition.name,
			daily_merge_limit=definition.daily_merge_limit,
		)
		db.add(plan)
		changed = True
	if changed:
		db.commit()
