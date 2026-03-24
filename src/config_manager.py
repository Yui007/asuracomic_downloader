import json
import os
from pathlib import Path
from pydantic import BaseModel, Field

CONFIG_FILE = Path("config.json")

class Settings(BaseModel):
    download_format: str = Field(default="CBZ", pattern="^(PDF|CBZ|Images)$")
    keep_images: bool = True
    threads_chapters: int = 3
    threads_images: int = 5
    retry_count: int = 3
    retry_delay: int = 2
    enable_logging: bool = False
    download_path: str = "downloads"
    chapter_list_limit: int = 20

class ConfigManager:
    def __init__(self):
        self.settings = self.load_config()

    def load_config(self) -> Settings:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return Settings(**data)
            except Exception:
                return Settings()
        return Settings()

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.settings.model_dump(), f, indent=4)

    def update_setting(self, key: str, value):
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_config()
