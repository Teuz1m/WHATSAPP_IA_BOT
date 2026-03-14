#!/bin/bash
# Uso: ./test_image.sh <caminho_da_imagem> "<legenda>"
# Exemplo: ./test_image.sh foto.jpg "essas folhas estão amarelando"

IMAGE=$1
CAPTION=${2:-"O que você vê nessa imagem?"}

if [ -z "$IMAGE" ]; then
  echo "Uso: $0 <caminho_da_imagem> \"<legenda>\""
  exit 1
fi

if [ ! -f "$IMAGE" ]; then
  echo "Arquivo não encontrado: $IMAGE"
  exit 1
fi

python3 -c "
import json, base64, sys
payload = {
    'data': {
        'key': {'remoteJid': '5511999999999@s.whatsapp.net'},
        'message': {'imageMessage': {'caption': sys.argv[2]}},
        'testBase64': base64.b64encode(open(sys.argv[1], 'rb').read()).decode()
    }
}
print(json.dumps(payload))
" "$IMAGE" "$CAPTION" > /tmp/test_image_payload.json

curl -s -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d @/tmp/test_image_payload.json

echo ""
echo "Payload enviado. Acompanhe a resposta com: docker-compose logs -f bot"
