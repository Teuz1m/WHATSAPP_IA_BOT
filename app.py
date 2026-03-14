from fastapi import FastAPI, Request

from message_buffer import buffer_message, buffer_image


app = FastAPI()

@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    msg_data = data.get('data', {})
    chat_id = msg_data.get('key', {}).get('remoteJid')

    if not chat_id or '@g.us' in chat_id:
        return {'status': 'ok'}

    message_content = msg_data.get('message', {})
    text = message_content.get('conversation') or message_content.get('extendedTextMessage', {}).get('text')
    image_msg = message_content.get('imageMessage')

    if text:
        await buffer_message(chat_id=chat_id, message=text)
    elif image_msg:
        caption = image_msg.get('caption', '')
        await buffer_image(chat_id=chat_id, caption=caption, message_data=msg_data)

    return {'status': 'ok'}
