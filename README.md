# Chatbot IA para WhatsApp — Assistente de Agricultura Familiar

Chatbot para WhatsApp com foco em **agricultura familiar do Nordeste brasileiro**. O assistente responde dúvidas sobre cultivos, diagnostica doenças em plantas a partir de fotos, informa preços de commodities e fornece previsões climáticas voltadas para o campo.

**Stack:**

- [EvolutionAPI](https://doc.evolution-api.com/v2/pt/get-started/introduction) — integração com WhatsApp
- [FastAPI](https://fastapi.tiangolo.com/) — servidor de webhook
- [LangChain](https://www.langchain.com/) — orquestração do agente de IA
- [OpenAI GPT-4o](https://platform.openai.com/) — LLM com suporte a visão
- [ChromaDB](https://www.trychroma.com/) — banco vetorial para RAG
- [Redis](https://redis.io/) — buffer de mensagens e histórico de conversa
- Docker Compose — orquestração de serviços

---

## Funcionalidades

### Diagnóstico de Plantas por Foto
O agricultor envia uma foto da lavoura pelo WhatsApp. O GPT-4o Vision analisa a imagem e identifica pragas, doenças fúngicas, deficiências nutricionais e estresse hídrico, descrevendo o problema e orientando com linguagem simples.

### Previsão Climática Agrícola
Consulta condições meteorológicas via [Open-Meteo](https://open-meteo.com/) (gratuito, sem chave). Retorna temperatura, chuva esperada, umidade e índice UV com interpretação voltada para o manejo no campo.

### Base de Conhecimento (RAG)
Documentos colocados na pasta `rag_files/` são vetorizados automaticamente e consultados pelo agente. Indicado para publicações da EMBRAPA, calendários agrícolas, guias de manejo e receituário agronômico voltados para o Nordeste.

### Contexto de Conversa por Usuário
Cada chat do WhatsApp mantém histórico independente armazenado no Redis. O assistente lembra do contexto da conversa sem misturar informações entre agricultores diferentes.

### Buffer de Mensagens com Debounce
Mensagens enviadas em sequência rápida são agrupadas antes de processar, evitando múltiplas respostas para uma mesma dúvida fragmentada em várias mensagens.

---

## Testando sem WhatsApp (TEST_MODE)

> As funcionalidades do bot foram desenvolvidas e testadas via TEST_MODE. A integração completa com a EvolutionAPI ainda não foi validada em ambiente real.

Para testar localmente sem precisar configurar a EvolutionAPI, ative o modo de teste no `.env`:

```
TEST_MODE=true
DEBOUNCE_SECONDS=5
```

Suba os serviços:

```bash
docker-compose up --build
```

**Mensagem de texto:**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"data": {"key": {"remoteJid": "5511999999999@s.whatsapp.net"}, "message": {"conversation": "Qual o tempo em Fortaleza amanhã?"}}}'
```

**Imagem com legenda:**

Use o script `test_image.sh` passando o caminho da imagem e a legenda:

```bash
./test_image.sh foto.jpg "essas folhas estão amarelando, o que pode ser?"
```

A resposta aparece nos logs após o debounce:

```bash
docker-compose logs -f bot
```

---

## Como subir com WhatsApp (EvolutionAPI)

> ⚠️ Esta integração ainda não foi testada em ambiente real. Os passos abaixo seguem a documentação oficial da EvolutionAPI.

### 1. Clone o repositório

```bash
git clone https://github.com/pycodebr/whatsapp_ai_bot.git
cd whatsapp_ai_bot
```

### 2. Crie o `.env` a partir do `.env.example`

```bash
cp .env.example .env
```

Variáveis obrigatórias:

| Variável | Descrição |
|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI |
| `OPENAI_MODEL_NAME` | Modelo a usar (recomendado: `gpt-4o`) |
| `AUTHENTICATION_API_KEY` | Chave da EvolutionAPI |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância (deve bater com o painel) |
| `CACHE_REDIS_URI` | URI do Redis (ex: `redis://redis:6379`) |
| `AI_SYSTEM_PROMPT` | Prompt principal do assistente |
| `AI_CONTEXTUALIZE_PROMPT` | Prompt para contextualizar perguntas |

Variáveis opcionais:

| Variável | Padrão | Descrição |
|---|---|---|
| `WEATHER_API_KEY` | — | Chave OpenWeatherMap (ferramenta de clima genérico) |
| `DEBOUNCE_SECONDS` | `10` | Tempo de espera antes de processar mensagens agrupadas |
| `BUFFER_TTL` | `300` | Tempo de expiração do buffer no Redis (segundos) |
| `OPENAI_MODEL_TEMPERATURE` | `0` | Temperatura do modelo |

### 3. Adicione documentos para RAG

Coloque PDFs ou TXTs na pasta `rag_files/`. Eles serão vetorizados automaticamente no startup e movidos para `rag_files/processed/`.

Conteúdo recomendado para agricultura familiar:
- Sistemas de produção EMBRAPA para feijão-caupi, milho, mandioca
- Manejo Integrado de Pragas (MIP) para culturas do Nordeste
- Calendário agrícola por estado

### 4. Suba os containers

```bash
docker-compose up --build
```

### 5. Configure o webhook na EvolutionAPI

Acesse [http://localhost:8080/manager](http://localhost:8080/manager), conecte sua instância e configure:

- **URL do webhook:** `http://bot:8000/webhook`
- **Evento:** `MESSAGES_UPSERT`

---

### Dúvidas ou melhorias?
Fique à vontade para abrir issues ou contribuir com o projeto.
