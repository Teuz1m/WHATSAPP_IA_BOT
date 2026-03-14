import requests
from langchain.tools import tool


def _geocode_city(city: str) -> tuple[float, float, str] | None:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "pt", "format": "json"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        return None
    r = results[0]
    return r["latitude"], r["longitude"], r.get("name", city)


def _agro_interpretation(precip: float, et0: float) -> str:
    if precip > 20:
        return "Chuva forte esperada. Evite aplicacao de defensivos e adubos nesse dia."
    if precip > 5:
        return "Chuva moderada esperada. Bom para plantio apos a chuva."
    if precip > 0:
        return "Chuva leve. Aproveite para verificar umidade do solo."
    if et0 and et0 > 6:
        return "Dia seco e quente. Irrigue pela manha ou final da tarde."
    return "Dia seco. Bom para colheita e operacoes no campo."


@tool
def get_agro_weather(city: str) -> str:
    """
    Obtem previsao climatica com foco agricola para uma cidade brasileira.
    Use quando o agricultor perguntar sobre chuva, temperatura, condicoes para
    irrigacao, plantio ou colheita. Retorna previsao de 7 dias com orientacao pratica.

    Args:
        city: Nome da cidade ou municipio

    Returns:
        Previsao de 7 dias com recomendacoes agricolas
    """
    try:
        coords = _geocode_city(city)
        if not coords:
            return f"Nao encontrei a cidade '{city}'. Tente o nome do municipio mais proximo."

        lat, lon, city_name = coords

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "precipitation_sum",
                "temperature_2m_max",
                "temperature_2m_min",
                "et0_fao_evapotranspiration",
                "precipitation_probability_max",
            ],
            "timezone": "America/Fortaleza",
            "forecast_days": 7,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["daily"]

        lines = [f"Previsao agricola para {city_name} - proximos 7 dias:\n"]
        for i in range(7):
            date = data["time"][i]
            tmax = data["temperature_2m_max"][i]
            tmin = data["temperature_2m_min"][i]
            precip = data["precipitation_sum"][i] or 0
            prob = data["precipitation_probability_max"][i] or 0
            et0 = data["et0_fao_evapotranspiration"][i] or 0

            dica = _agro_interpretation(precip, et0)
            lines.append(
                f"{date}: {tmin:.0f}-{tmax:.0f}C | Chuva: {precip:.1f}mm ({prob}% chance) | {dica}"
            )

        total_chuva = sum(d or 0 for d in data["precipitation_sum"])
        lines.append(f"\nTotal de chuva esperado na semana: {total_chuva:.1f}mm")

        if total_chuva < 5:
            lines.append("Semana seca. Planeje irrigacao se necessario.")
        elif total_chuva > 60:
            lines.append("Semana chuvosa. Cuidado com erosao e doencas fungicas.")
        else:
            lines.append("Chuva moderada na semana. Boas condicoes para a lavorura.")

        return "\n".join(lines)

    except requests.exceptions.RequestException as e:
        return f"Erro ao consultar previsao do tempo: {str(e)}"
