import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


T = TypeVar("T")

logger = logging.getLogger(__name__)


# Exceptions that are normally temporary and worth retrying.
RETRYABLE_EXCEPTIONS = (
    PlaywrightTimeoutError,
    PlaywrightError,
    TimeoutError,
    ConnectionError,
)


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    operation_name: str = "operation",
) -> T:
    """
    Retry an asynchronous operation when a transient
    network/browser failure occurs.

    Uses exponential backoff:

        Attempt 1 fails → wait 1 second
        Attempt 2 fails → wait 2 seconds
        Attempt 3 fails → raise the error

    Args:
        operation:
            Async function to execute.

        max_attempts:
            Maximum number of attempts.

        base_delay:
            Initial retry delay in seconds.

        operation_name:
            Human-readable name used in logs.

    Returns:
        The successful operation result.

    Raises:
        Exception:
            The final exception if all retry attempts fail,
            or immediately for non-retryable exceptions.
    """

    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1"
        )

    if base_delay < 0:
        raise ValueError(
            "base_delay cannot be negative"
        )

    last_exception: Exception | None = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            return await operation()

        except Exception as exc:

            last_exception = exc

            # Do not retry errors that are unlikely to
            # succeed on a second attempt.
            if not isinstance(
                exc,
                RETRYABLE_EXCEPTIONS,
            ):
                logger.error(
                    "%s failed with a non-retryable "
                    "error: %s",
                    operation_name,
                    exc,
                )
                raise

            # All attempts have been exhausted.
            if attempt == max_attempts:
                logger.error(
                    "%s failed after %d attempts: %s",
                    operation_name,
                    max_attempts,
                    exc,
                )
                break

            delay = (
                base_delay
                * (2 ** (attempt - 1))
            )

            logger.warning(
                "%s failed on attempt %d/%d: %s. "
                "Retrying in %.1f seconds...",
                operation_name,
                attempt,
                max_attempts,
                exc,
                delay,
            )

            await asyncio.sleep(delay)

    if last_exception is not None:
        raise last_exception

    raise RuntimeError(
        f"{operation_name} failed unexpectedly."
    )
