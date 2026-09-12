import asyncio

import pytest

from app.resilience import retry_async


@pytest.mark.asyncio
async def test_retry_async_succeeds_after_temporary_failure():

    attempts = 0

    async def operation():

        nonlocal attempts

        attempts += 1

        if attempts < 3:
            raise ConnectionError(
                "Temporary connection failure"
            )

        return "success"

    result = await retry_async(
        operation,
        max_attempts=3,
        base_delay=0,
        operation_name="test operation",
    )

    assert result == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_async_raises_after_all_attempts():

    attempts = 0

    async def operation():

        nonlocal attempts

        attempts += 1

        raise ConnectionError(
            "Connection unavailable"
        )

    with pytest.raises(ConnectionError):

        await retry_async(
            operation,
            max_attempts=3,
            base_delay=0,
            operation_name="failing operation",
        )

    assert attempts == 3


@pytest.mark.asyncio
async def test_non_retryable_error_is_not_retried():

    attempts = 0

    async def operation():

        nonlocal attempts

        attempts += 1

        raise ValueError(
            "Invalid input"
        )

    with pytest.raises(ValueError):

        await retry_async(
            operation,
            max_attempts=3,
            base_delay=0,
            operation_name="invalid operation",
        )

    assert attempts == 1


def test_invalid_max_attempts():

    async def operation():
        return "success"

    async def run():

        await retry_async(
            operation,
            max_attempts=0,
        )

    with pytest.raises(ValueError):
        asyncio.run(run())
