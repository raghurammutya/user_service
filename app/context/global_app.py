# user_service/app/context/global_app.py

from fastapi import FastAPI
from typing import Optional

# Global application instance
_app: Optional[FastAPI] = None

def set_app(app: FastAPI) -> None:
    """Set the global FastAPI application instance"""
    global _app
    _app = app

def get_app() -> Optional[FastAPI]:
    """Get the global FastAPI application instance"""
    return _app