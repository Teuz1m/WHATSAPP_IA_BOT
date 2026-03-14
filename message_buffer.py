import asyncio
import json
import redis.asyncio as redis

from collections import defaultdict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from config import REDIS_URL, BUFFER_KEY_SUFIX, DEBOUNCE_SECONDS, BUFFER_TTL, OPENAI_MODEL_NAME
from evolution_api import send_whatsapp_message, get_media_base64
from chains import get_conversational_rag_chain


redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
conversational_rag_chain = get_conversational_rag_chain()
debounce_tasks = defaultdict(asyncio.Task)

IMAGE_BUFFER_KEY_SUFFIX = ':image'

def log(*args):
    print('[BUFFER]', *args, flush=True)


async def buffer_message(chat_id: str, message: str):
    buffer_key = f'{chat_id}{BUFFER_KEY_SUFIX}'

    await redis_client.rpush(buffer_key, message)
    await redis_client.expire(buffer_key, BUFFER_TTL)

    log(f'Mensagem adicionada ao buffer de {chat_id}: {message}')

    if debounce_tasks.get(chat_id):
        debounce_tasks[chat_id].cancel()
        log(f'Debounce resetado para {chat_id}')

    task = asyncio.create_task(handle_debounce(chat_id))
    task.add_done_callback(lambda t: log(f'Erro: {t.exception()}') if not t.cancelled() and t.exception() else None)
    debounce_tasks[chat_id] = task
    await asyncio.sleep(0)


async def buffer_image(chat_id: str, caption: str, message_data: dict):
    image_key = f'{chat_id}{IMAGE_BUFFER_KEY_SUFFIX}'

    payload = json.dumps({'caption': caption, 'message_data': message_data})
    await redis_client.set(image_key, payload, ex=BUFFER_TTL)

    log(f'Imagem adicionada ao buffer de {chat_id}, caption: {caption}')

    if debounce_tasks.get(chat_id):
        debounce_tasks[chat_id].cancel()
        log(f'Debounce resetado para {chat_id}')

    task = asyncio.create_task(handle_debounce(chat_id))
    task.add_done_callback(lambda t: log(f'Erro: {t.exception()}') if not t.cancelled() and t.exception() else None)
    debounce_tasks[chat_id] = task
    await asyncio.sleep(0)


async def _describe_image(base64_data: str, caption: str) -> str:
    llm = ChatOpenAI(model=OPENAI_MODEL_NAME)
    prompt_text = (
        'Você é um especialista em agricultura familiar do Nordeste brasileiro. '
        'Analise esta imagem com cuidado e descreva em detalhes o que está vendo: '
        'identifique a planta ou cultura, descreva o estado geral, e aponte qualquer '
        'problema visível como pragas, doenças, deficiências nutricionais, estresse '
        'hídrico ou outros. Seja específico e use linguagem simples.'
    )
    content = [{'type': 'text', 'text': prompt_text}]
    if caption:
        content.append({'type': 'text', 'text': f'Legenda enviada pelo agricultor: {caption}'})
    content.append({
        'type': 'image_url',
        'image_url': {'url': f'data:image/jpeg;base64,{base64_data}'},
    })
    response = await llm.ainvoke([HumanMessage(content=content)])
    return response.content


async def _get_image_as_text(chat_id: str) -> str | None:
    image_key = f'{chat_id}{IMAGE_BUFFER_KEY_SUFFIX}'
    raw = await redis_client.get(image_key)
    if not raw:
        return None

    await redis_client.delete(image_key)
    payload = json.loads(raw)
    caption = payload.get('caption', '')
    message_data = payload.get('message_data', {})

    base64_data = await get_media_base64(message_data)
    if not base64_data:
        return caption or 'O agricultor enviou uma imagem, mas não foi possível processá-la.'

    log(f'Descrevendo imagem para {chat_id}')
    description = await _describe_image(base64_data, caption)
    return (
        f'[O agricultor enviou uma foto da lavoura/planta]\n'
        f'Descrição da imagem: {description}\n'
        f'Com base nessa descrição, oriente o agricultor com recomendações práticas.'
    )


async def handle_debounce(chat_id: str):
    try:
        log(f'Iniciando debounce para {chat_id}')
        await asyncio.sleep(float(DEBOUNCE_SECONDS))

        buffer_key = f'{chat_id}{BUFFER_KEY_SUFIX}'
        messages = await redis_client.lrange(buffer_key, 0, -1)
        await redis_client.delete(buffer_key)

        image_text = await _get_image_as_text(chat_id)
        full_message = image_text or ' '.join(messages).strip()

        if not full_message:
            return

        log(f'Processando mensagem para {chat_id}')
        ai_response = conversational_rag_chain.invoke(
            input={'input': full_message},
            config={'configurable': {'session_id': chat_id}},
        )['output']

        await send_whatsapp_message(number=chat_id, text=ai_response)

    except asyncio.CancelledError:
        log(f'Debounce cancelado para {chat_id}')
    except Exception as e:
        log(f'Erro no debounce para {chat_id}: {type(e).__name__}: {e}')
