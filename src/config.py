"""Configuration for the agentic AI Judo system."""

from typing import Any, Dict, Optional


class Config:
    """Configuration class for the system."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional path to a config file
        """
        self._config: Dict[str, Any] = {
            "llm": {
                "provider": "openai",  # openai or anthropic
                "model": "gpt-4o",
                "temperature": 0.0,
            },
            "video": {
                "frame_interval": 30,  # Extract frame every N seconds
                "quality_threshold": 0.7,
            },
            "pose": {
                "model": "mediapipe",
                "confidence_threshold": 0.5,
            },
            "agents": {
                "coordinator": {},
                "video_loader": {"website": "judo.tv"},
                "video_analyzer": {},
                "pose_analyzer": {},
                "technique_analyzer": {},
                "strategy_analyzer": {},
            },
            "paths": {
                "data_input": "data/input",
                "data_output": "data/output",
                "technique_db": "data/techniques.json",
            },
        }

        if config_path:
            self._load_config_file(config_path)

    def _load_config_file(self, config_path: str) -> None:
        """Load configuration from a file (JSON or YAML)."""
        try:
            import json
            with open(config_path, "r") as f:
                user_config = json.load(f)
                self._update_recursive(user_config)
        except Exception:
            # If file loading fails, use defaults
            pass

    def _update_recursive(self, updates: Dict[str, Any]) -> None:
        """Recursively update config values."""
        for key, value in updates.items():
            if key in self._config and isinstance(self._config[key], dict):
                if isinstance(value, dict):
                    self._update_recursive(value)
                else:
                    self._config[key] = value
            else:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()


# Global config instance
config = Config()
