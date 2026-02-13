import asyncio
import logging
from typing import Callable, Type, Tuple, Optional


async def retry_async(
        func: Callable,
        max_attempts: int = 10,
        delay: float = 1,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        logger: Optional[logging.Logger] = None,
        *args,
        **kwargs
):
    if logger is None:
        logger = logging.getLogger(__name__)

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            if attempt == max_attempts:
                logger.error(f"Все {max_attempts} попыток не удались. Последняя ошибка: {e}")
                raise
            logger.warning(f"Попытка {attempt}/{max_attempts} не удалась: {e}. Повтор через {delay}с...")
            await asyncio.sleep(delay)
