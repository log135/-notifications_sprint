import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError

from notifications.common.config import settings
from notifications.common.retry import retry_async

logger = logging.getLogger(__name__)


async def main() -> None:
    engine = create_async_engine(settings.db_dsn, echo=True, future=True)

    async def _check_connection():
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

    await retry_async(
        _check_connection,
        max_attempts=10,
        delay=2,
        exceptions=(OperationalError,),
        logger=logger
    )

    logger.info("DB schema created successfully")
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    asyncio.run(main())
