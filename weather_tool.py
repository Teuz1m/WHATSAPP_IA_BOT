import requests
from langchain.tools import tool
from config import WEATHER_API_KEY


@tool
def get_weather(city: str) -> str:
    """
    Obtém informações sobre o clima atual de uma cidade.
    Use esta ferramenta quando o usuário perguntar sobre clima, temperatura ou condições meteorológicas.

    Args:
        city: Nome da cidade para consultar o clima

    Returns:
        String com informações sobre o clima atual
    """
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=pt_br"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        weather_info = f"""
Clima em {data['name']}, {data['sys']['country']}:
- Temperatura: {data['main']['temp']}°C (sensação térmica: {data['main']['feels_like']}°C)
- Condição: {data['weather'][0]['description']}
- Umidade: {data['main']['humidity']}%
- Vento: {data['wind']['speed']} m/s
- Pressão: {data['main']['pressure']} hPa
        """.strip()

        return weather_info

    except requests.exceptions.RequestException as e:
        return f"Erro ao consultar o clima: {str(e)}"
    except KeyError:
        return "Erro ao processar dados do clima. Verifique se o nome da cidade está correto."
