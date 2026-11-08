import httpx
import pytest

from app.services.research_providers import ProviderRequestError, request_with_retries


@pytest.mark.asyncio
async def test_timeout_is_retried_expected_number_of_times():
    attempts = 0

    async def timeout_once_then_succeed():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.TimeoutException("timeout")
        return {"ok": True}

    result = await request_with_retries(timeout_once_then_succeed, attempts=3)
    assert result == {"ok": True}
    assert attempts == 3


@pytest.mark.asyncio
async def test_repeated_api_failure_returns_provider_error():
    attempts = 0

    async def always_fail():
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("provider unavailable")

    with pytest.raises(ProviderRequestError):
        await request_with_retries(always_fail, attempts=3)
    assert attempts == 3


@pytest.mark.asyncio
async def test_http_status_failure_returns_provider_error():
    async def status_failure():
        request = httpx.Request("GET", "https://provider.example/search")
        response = httpx.Response(503, request=request)
        raise httpx.HTTPStatusError("unavailable", request=request, response=response)

    with pytest.raises(ProviderRequestError):
        await request_with_retries(status_failure, attempts=2)
