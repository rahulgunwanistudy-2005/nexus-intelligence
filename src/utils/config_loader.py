import yaml
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, DirectoryPath, FilePath, ValidationError
from loguru import logger

# --- 1. Define Expected Schema (Validation Layer) ---
class ScraperConfig(BaseModel):
    base_url: str
    search_term: str
    headless: bool
    timeout_ms: int
    user_agent: str
    retries: int

class PathsConfig(BaseModel):
    base_data_dir: str
    bronze: str
    silver: str
    gold: str
    logs: str

class AppConfig(BaseModel):
    project_name: str
    version: str
    scraper: ScraperConfig
    paths: PathsConfig

# --- 2. The Singleton Loader ---
class ConfigManager:
    """
    Singleton class to load and validate configuration.
    Ensures config is loaded once and accessed globally.
    """
    _instance = None
    _config: AppConfig = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def load_config(self, config_path: str = "configs/base_config.yaml") -> AppConfig:
        if self._config is None:
            path = Path(config_path)
            if not path.exists():
                logger.critical(f"❌ Config file not found at: {path.absolute()}")
                raise FileNotFoundError(f"Config file missing: {path}")

            try:
                with open(path, "r") as f:
                    raw_config = yaml.safe_load(f)
                
                # VALIDATE with Pydantic
                self._config = AppConfig(**raw_config)
                logger.info(f"✅ Configuration loaded & validated: {self._config.project_name}")
                
            except ValidationError as e:
                logger.critical(f"❌ Configuration Schema Error: {e}")
                raise e
            except Exception as e:
                logger.critical(f"❌ Failed to load config: {e}")
                raise e
                
        return self._config

# Global Accessor
settings = ConfigManager().load_config()