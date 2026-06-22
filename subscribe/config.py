from __future__ import annotations

import yaml
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    model_size: str = "medium"
    language: str = "auto"
    output_dir: str = "."
    device: str = "auto"

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        config_path = path or Path("config.yaml")
        if config_path.exists():
            with config_path.open() as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()
