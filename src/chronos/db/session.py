from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chronos.db.engine import get_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_db)]
