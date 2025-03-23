import aiohttp
import asyncio
import sys
from bot.config import n8n_aiagent_webhook

sys.stdout.reconfigure(encoding='utf-8')

####################### AI AGENT IN N8N (OLEDBOT) ####################################

async def ai_agent_n8n(query=None):
    url = f"{n8n_aiagent_webhook}"
    headers = {"Content-Type": "application/json"}
    data = {"text": query}

    # connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers) as response:
                response_data = await response.json()
                if response.status == 200:
                    print("Запрос успешно отправлен.")
                    return response_data  # Возвращаем ответ от n8n
                else:
                    print(f"Ошибка при отправке запроса: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            print(f"Ошибка при отправке запроса: {e}")
            return None

# Асинхронно вызываем функцию и печатаем результат
# response = asyncio.run(ai_agent_n8n("aйфон 13"))
# print("Ответ от n8n:", response)
