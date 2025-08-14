import httpx
import logging

logger = logging.getLogger(__name__)

async def request(api_url):
    async with httpx.AsyncClient() as client:
        try:
            request = await client.get(api_url)
            request.raise_for_status()
            data = request.json()
            return data
        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP error: {exc.response.status_code} for URL {api_url}")
            return {"error": f"HTTP error: {exc.response.status_code}"}
        except httpx.RequestError as exc:
            logger.error(f"Request failed: {exc} for URL {api_url}")
            return {"error": "Ошибка соединения"}
        except Exception as e:
            logger.error(f"Unexpected error: {e} for URL {api_url}")
            return {"error": "Неожиданная ошибка"}