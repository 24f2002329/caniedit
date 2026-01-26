from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.tool import ToolDefinition

TOOL_DEFINITIONS = [
    {
        "slug": "pdf_merge",
        "category": "pdf",
        "weight": 1,
        "is_premium": False,
    },
    {
        "slug": "pdf_compress",
        "category": "pdf",
        "weight": 2,
        "is_premium": False,
    },
]


def seed_tool_definitions(db: Session) -> None:
    now = datetime.utcnow()
    for definition in TOOL_DEFINITIONS:
        slug = definition["slug"]
        tool = db.query(ToolDefinition).filter(ToolDefinition.slug == slug).first()
        if not tool:
            tool = ToolDefinition(
                slug=slug,
                category=definition.get("category"),
                weight=definition.get("weight", 1),
                is_premium=definition.get("is_premium", False),
            )
            db.add(tool)
            continue
        updated = False
        category = definition.get("category")
        weight = definition.get("weight", 1)
        is_premium = definition.get("is_premium", False)
        if category is not None and tool.category != category:
            tool.category = category
            updated = True
        if tool.weight != weight:
            tool.weight = weight
            updated = True
        if tool.is_premium != is_premium:
            tool.is_premium = is_premium
            updated = True
        if updated:
            tool.touch(now)
            db.add(tool)
    db.commit()
