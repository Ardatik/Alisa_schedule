import httpx

async def request(api_url):
    async with httpx.AsyncClient() as client:
        try:
            request = await client.get(api_url)
            request.raise_for_status()
            data = request.json()
            return data
        except httpx.HTTPStatusError as exc:
            return f"Ошибка при получении расписания: {exc.response.status_code}"
        except Exception as e:
            return f"Произошла ошибка: {str(e)}"