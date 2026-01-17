from fastapi import APIRouter
from app.api.v1 import projects, websocket, templates, terminal

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(terminal.router, prefix="/terminal", tags=["terminal"])
