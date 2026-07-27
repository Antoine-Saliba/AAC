"""API route definitions.
 
Module 1 scope: this router is intentionally empty. Task CRUD endpoints are
added in a later module, at which point main.py will include this router via
`app.include_router(router)`.
"""
 
from fastapi import APIRouter
 
router = APIRouter(prefix="/tasks", tags=["tasks"])