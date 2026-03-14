import requests
from langchain.tools import tool


# Precos minimos garantidos pelo governo (PGPAF/CONAB) - referencia 2024/2025
# Fonte: https://www.conab.gov.br/info-agro/precos/precos-minimos
# Valores em R$ por saca de 60kg, exceto mandioca (tonelada) e algodao (arroba)
PRECOS_MINIMOS = {
    "feijao": {"nome": "Feijao-caupi (Vigna)", "unidade": "saca 60kg", "preco_minimo": 220.00},
    "feijao-caupi": {"nome": "Feijao-caupi (Vigna)", "unidade": "saca 60kg", "preco_minimo": 220.00},
    "feijao carioca": {"nome": "Feijao carioca", "unidade": "saca 60kg", "preco_minimo": 180.00},
    "milho": {"nome": "Milho", "unidade": "saca 60kg", "preco_minimo": 31.00},
    "mandioca": {"nome": "Mandioca/macaxeira", "unidade": "tonelada", "preco_minimo": 420.00},
    "algodao": {"nome": "Algodao em pluma", "unidade": "arroba", "preco_minimo": 115.00},
    "castanha": {"nome": "Castanha-de-caju", "unidade": "kg", "preco_minimo": 7.50},
    "castanha de caju": {"nome": "Castanha-de-caju", "unidade": "kg", "preco_minimo": 7.50},
    "sisal": {"nome": "Sisal/agave", "unidade": "tonelada", "preco_minimo": 1800.00},
    "gergelim": {"nome": "Gergelim", "unidade": "saca 60kg", "preco_minimo": 180.00},
    "amendoim": {"nome": "Amendoim", "unidade": "saca 25kg", "preco_minimo": 85.00},
}


def _normalize_product(product: str) -> str:
    return product.lower().strip()


def _search_conab_prices(product_key: str) -> dict | None:
    """Tenta buscar preco atual via API publica da CONAB."""
    try:
        # CONAB API de cotacoes (endpoint publico)
        url = "https://www.conab.gov.br/info-agro/precos/precos-minimos"
        # Como a CONAB nao tem API REST padronizada, usamos os precos minimos como referencia
        # Em producao, pode-se fazer scraping da pagina ou usar CEPEA
        return None
    except Exception:
        return None


@tool
def get_commodity_price(product: str) -> str:
    """
    Consulta precos de produtos agricolas do Nordeste e o preco minimo garantido pelo governo.
    Use quando o agricultor perguntar sobre preco de venda, preco minimo ou se vale a pena vender.
    Produtos suportados: feijao, milho, mandioca, algodao, castanha de caju, sisal, gergelim, amendoim.

    Args:
        product: Nome do produto agricola (ex: 'feijao', 'milho', 'mandioca')

    Returns:
        Preco minimo garantido pelo governo com orientacao pratica
    """
    normalized = _normalize_product(product)

    # Busca por chave exata ou parcial
    found_key = None
    for key in PRECOS_MINIMOS:
        if normalized in key or key in normalized:
            found_key = key
            break

    if not found_key:
        produtos = ", ".join(PRECOS_MINIMOS.keys())
        return (
            f"Produto '{product}' nao encontrado. "
            f"Consulto precos de: {produtos}."
        )

    info = PRECOS_MINIMOS[found_key]
    nome = info["nome"]
    unidade = info["unidade"]
    preco_min = info["preco_minimo"]

    resposta = [
        f"Preco minimo garantido pelo governo (PGPAF/CONAB) para {nome}:",
        f"R$ {preco_min:.2f} por {unidade}",
        "",
        "O Programa de Garantia de Precos para a Agricultura Familiar (PGPAF) garante",
        "esse preco minimo ao agricultor familiar. Se o mercado estiver pagando menos,",
        "voce tem direito a um desconto na parcela do Pronaf equivalente a diferenca.",
        "",
        "Dica: Antes de vender, consulte a cooperativa ou sindicato local para saber",
        "o preco que o mercado esta pagando na sua regiao e compare com o minimo garantido.",
    ]

    return "\n".join(resposta)
