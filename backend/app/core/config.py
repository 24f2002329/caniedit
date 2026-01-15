import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "CanIEdit API")
    allowed_origins: str = os.getenv(
        "ALLOWED_ORIGINS",
        "https://caniedit.in,https://api.caniedit.in,https://www.caniedit.in",
    )


settings = Settings()
