"""Hub configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GeoHub Developer API"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Tool discovery
    tools_dir: str = "tools"

    # API keys (consumers like AURA)
    api_keys: list[str] = []

    model_config = {"env_prefix": "GEOHUB_"}
