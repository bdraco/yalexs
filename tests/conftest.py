import httpx
import pytest_asyncio


@pytest_asyncio.fixture
async def httpx_client():
    async with httpx.AsyncClient(http2=True) as client:
        yield client
