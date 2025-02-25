import requests
import time
import random

def obter_data_ultima_atualizacao():
    """
    Obtém a data da última atualização da API do ComexStat.

    Returns:
        tuple: Uma tupla contendo (data_atualizacao, ano_atualizacao, mes_atualizacao)
               no formato string. Retorna ("Erro", "Erro", "Erro") em caso de falha.
    """
    url = "https://api-comexstat.mdic.gov.br/general/dates/updated"
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Lança exceção para códigos de status de erro (4xx ou 5xx)
        data = response.json()
        last_updated_date = data.get('data', {}).get('updated', "Data não encontrada")
        last_updated_year = data.get('data', {}).get('year', "Ano não encontrado")
        last_updated_month = data.get('data', {}).get('monthNumber', "Mês não encontrado")
        return last_updated_date, last_updated_year, last_updated_month
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")  # Log do erro para debug
        return "Erro", "Erro", "Erro"
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return "Erro", "Erro", "Erro"

def obter_descricao_ncm(ncm_code):
    """
    Obtém a descrição do NCM informado.

    Args:
        ncm_code (str): O código NCM a ser consultado.

    Returns:
        str: A descrição do NCM ou uma mensagem de erro em caso de falha.
    """
    url = f"https://api-comexstat.mdic.gov.br/tables/ncm/{ncm_code}"
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            return data['data'][0].get('text', 'Descrição não encontrada')
        else:
            return 'Descrição não encontrada'
    except requests.exceptions.RequestException as e:
        return f"Erro na requisição: {e}"
    except Exception as e:
        return f"Erro inesperado: {e}"

def _fazer_requisicao(url, payload=None, max_retries=5, initial_delay=1):
    """
    Função auxiliar para fazer requisições com retry e backoff exponencial.

    Args:
        url (str): A URL da API.
        payload (dict, optional): O payload (corpo) da requisição POST.
        max_retries (int): Número máximo de tentativas.
        initial_delay (int): Tempo inicial de espera em segundos.

    Returns:
        requests.Response: O objeto de resposta da requisição, ou None em caso de falha.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            if payload:
                response = requests.post(url, json=payload, verify=False)
            else:
                response = requests.get(url, verify=False)

            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"Erro 429: Muitas requisições. Tentando novamente em {delay} segundos...")
                time.sleep(delay)
                delay *= 2  # Backoff exponencial
                delay += random.uniform(0, 0.1 * delay)  # Adiciona um "jitter" aleatório
            else:
                print(f"Erro HTTP: {e}")
                return None  # Outro erro HTTP, não tentamos novamente
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição: {e}")
            return None
    print(f"Número máximo de tentativas excedido para a URL: {url}")
    return None

def obter_dados_comerciais(ncm_code, flow):
    """
    Obtém dados de importação ou exportação para um NCM específico.

    Args:
        ncm_code (str): O código NCM a ser consultado.
        flow (str): 'import' para importações, 'export' para exportações.

    Returns:
        tuple: Uma tupla contendo (dados, erro).  'dados' é uma lista de dicionários
               com os dados da API, ou uma lista vazia em caso de erro. 'erro' é uma
               string com a mensagem de erro ou None se não houver erro.
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    body = {
        "flow": flow,
        "monthDetail": False,
        "period": {
            "from": "2004-01",
            "to": "2025-12"
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": [],
        "metrics": ["metricFOB", "metricKG"]
    }

    response = _fazer_requisicao(url, payload=body)
    if response:
        data = response.json().get('data', {}).get('list', [])
        return data, None
    else:
        return [], "Erro ao obter dados da API."

def obter_dados_comerciais_ano_anterior(ncm_code, flow, last_updated_month):
    """
    Obtém os dados acumulados de 2024 até o último mês disponível.

    Args:
        ncm_code (str): O código NCM a ser consultado.
        flow (str): 'import' para importações, 'export' para exportações.
        last_updated_month (str): O número do último mês atualizado.

    Returns:
        tuple: Uma tupla contendo (dados, erro). 'dados' é uma lista de dicionários
               com os dados da API, ou uma lista vazia em caso de erro. 'erro' é uma
               string com a mensagem de erro ou None se não houver erro.
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    payload = {
        "flow": flow,
        "monthDetail": False,
        "period": {
            "from": "2024-01",
            "to": f"2024-{str(last_updated_month).zfill(2)}"
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": [],
        "metrics": ["metricFOB", "metricKG"]
    }

    response = _fazer_requisicao(url, payload=payload)
    if response:
        data = response.json().get('data', {}).get('list', [])
        return data, None
    else:
        return [], "Erro ao obter dados da API."

def obter_dados_comerciais_ano_atual(ncm_code, flow, last_updated_month):
    """
    Obtém os dados acumulados de 2025 até o último mês disponível.

    Args:
        ncm_code (str): O código NCM a ser consultado.
        flow (str): 'import' para importações, 'export' para exportações.
        last_updated_month (str): O número do último mês atualizado.

    Returns:
        tuple: Uma tupla contendo (dados, erro). 'dados' é uma lista de dicionários
               com os dados da API, ou uma lista vazia em caso de erro. 'erro' é uma
               string com a mensagem de erro ou None se não houver erro.
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    payload = {
        "flow": flow,
        "monthDetail": False,
        "period": {
            "from": "2025-01",  # Começa em janeiro de 2025
            "to": f"2025-{str(last_updated_month).zfill(2)}"  # Até o mês atual
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": [],
        "metrics": ["metricFOB", "metricKG"]
    }

    response = _fazer_requisicao(url, payload=payload)  # Usa a função auxiliar
    if response:
        data = response.json().get('data', {}).get('list', [])
        return data, None
    else:
        return [], "Erro ao obter dados da API."
