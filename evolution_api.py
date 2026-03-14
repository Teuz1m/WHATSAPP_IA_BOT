import httpx

from config import (
    EVOLUTION_API_URL,
    EVOLUTION_INSTANCE_NAME,
    EVOLUTION_AUTHENTICATION_API_KEY,
    TEST_MODE,
)


async def get_media_base64(message_data: dict) -> str | None:
    if TEST_MODE:
        return message_data.get('testBase64')

    url = f'{EVOLUTION_API_URL}/chat/getBase64FromMediaMessage/{EVOLUTION_INSTANCE_NAME}'
    headers = {
        'apikey': EVOLUTION_AUTHENTICATION_API_KEY,
        'Content-Type': 'application/json',
    }
    payload = {'message': message_data}
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('base64')
    return None


async def send_whatsapp_message(number, text):
    if TEST_MODE:
        print(f'\n{"="*60}')
        print(f'[TEST MODE] Resposta para {number}:')
        print(text)
        print('='*60)
        return

    url = f'{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}'
    headers = {
        'apikey': EVOLUTION_AUTHENTICATION_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'number': number,
        'text': text,
    }
    async with httpx.AsyncClient() as client:
        await client.post(
            url=url,
            json=payload,
            headers=headers,
        )
