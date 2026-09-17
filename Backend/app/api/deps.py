"""FastAPI dependency injection utilities."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

# Common DB Session Dependency
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
