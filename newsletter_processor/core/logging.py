import logging
import sys
from typing import Any, Dict
from pathlib import Path

def setup_logging(
    log_level: str = "INFO",
    log_file: Path = None,
    json_format: bool = True
) -> None:
    """Configure logging for the application"""
    
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if json_format else "standard",
                "stream": sys.stdout
            }
        },
        "root": {
            "handlers": ["console"],
            "level": log_level
        }
    }
    
    if log_file:
        log_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json" if json_format else "standard",
            "filename": str(log_file),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        log_config["root"]["handlers"].append("file")
    
    logging.config.dictConfig(log_config) 