import os
from dataclasses import dataclass, field


def _parse_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "CanIEdit API")
    env: str = os.getenv("ENV", "local").lower()
    allowed_origins: list[str] = field(
        default_factory=lambda: _parse_origins(
            os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080"
                if os.getenv("ENV", "local").lower() == "local"
                else "https://caniedit.in,https://www.caniedit.in",
            )
        )
    )


settings = Settings()
