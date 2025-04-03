import requests
import time
import logging

def obter_data_ultima_atualizacao():
    """
    Obtém a data da última atualização da API do ComexStat.
    Returns:
        tuple: (data_atualizacao, ano_atualizacao, mes_atualizacao) ou ("Erro", "Erro", "Erro")
    """
    url = "https://api-comexstat.mdic.gov.br/general/dates/updated"
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        last_updated_date = data.get('data', {}).get('updated', "Data não encontrada")
        last_updated_year = data.get('data', {}).get('year', "Ano não encontrado")
        last_updated_month = data.get('data', {}).get('monthNumber', "Mês não encontrado")
        return last_updated_date, last_updated_year, last_updated_month
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return "Erro", "Erro", "Erro"
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return "Erro", "Erro", "Erro"

def obter_descricao_ncm(ncm_code):
    """
    Obtém a descrição do NCM informado.
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
    Função auxiliar para requisições com retry e backoff exponencial.
    """
    import random
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
                delay *= 2
                delay += random.uniform(0, 0.1 * delay)
            else:
                print(f"Erro HTTP: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição: {e}")
            return None
    print(f"Número máximo de tentativas excedido para a URL: {url}")
    return None

def obter_dados_comerciais(ncm_code, flow):
    """
    Obtém dados de importação ou exportação para um NCM específico (2004-01 até 2025-12).
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
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    payload = {
        "flow": flow,
        "monthDetail": False,
        "period": {
            "from": "2025-01",
            "to": f"2025-{str(last_updated_month).zfill(2)}"
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

def processar_dados(dados_export, dados_import, ano_ref):
    """
    Função desatualizada se você tiver outra. 
    Mas vamos manter se for usada em outro lugar.
    """
    import pandas as pd
    if not dados_export or not dados_import:
        return pd.DataFrame(), "Dados ausentes."

    df_export = pd.DataFrame(dados_export)
    df_import = pd.DataFrame(dados_import)

    # Padronização de colunas
    df_export = df_export.rename(columns={
        'year': 'Ano',
        'coAno': 'Ano',
        'vlFob': 'Exportações (FOB)',
        'kgLiquido': 'Exportações (KG)'
    })
    df_import = df_import.rename(columns={
        'year': 'Ano',
        'coAno': 'Ano',
        'vlFob': 'Importações (FOB)',
        'kgLiquido': 'Importações (KG)'
    })

    # Mescla
    df = pd.merge(df_export, df_import, on='Ano', how='outer')
    df['Balança Comercial (FOB)'] = df['Exportações (FOB)'] - df['Importações (FOB)']
    df['Balança Comercial (KG)'] = df['Exportações (KG)'] - df['Importações (KG)']
    df = df.sort_values(by='Ano').fillna(0)

    return df, None

# ================= Novas funções para dados de 2024 por país ================= #

def obter_dados_2024_por_pais(ncm_code, max_retries=5, delay=5):
    """
    Obtém dados de importação (US$ FOB) para 2024, detalhados por país.
    Retorna uma lista de dicionários contendo "country" e "metricFOB".
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    body = {
        "flow": "import",
        "monthDetail": False,
        "period": {
            "from": "2024-01",
            "to": "2024-12"
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": ["country"],
        "metrics": ["metricFOB"]
    }
    for attempt in range(max_retries):
        response = requests.post(url, json=body, verify=False)
        if response.status_code == 200:
            return response.json().get('data', {}).get('list', [])
        elif response.status_code == 429:
            logging.warning("Muitas requisições (import). Aguardando antes de tentar novamente...")
            time.sleep(delay)
        else:
            logging.error(f"Erro {response.status_code} ao obter dados de 2024 por país (import).")
            return []
    return []

def obter_dados_2024_por_pais_export(ncm_code, max_retries=5, delay=5):
    """
    Obtém dados de exportação (US$ FOB) para 2024, detalhados por país.
    Retorna uma lista de dicionários contendo "country" e "metricFOB".
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    body = {
        "flow": "export",
        "monthDetail": False,
        "period": {
            "from": "2024-01",
            "to": "2024-12"
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": ["country"],
        "metrics": ["metricFOB"]
    }
    for attempt in range(max_retries):
        response = requests.post(url, json=body, verify=False)
        if response.status_code == 200:
            return response.json().get('data', {}).get('list', [])
        elif response.status_code == 429:
            logging.warning("Muitas requisições (export). Aguardando antes de tentar novamente...")
            time.sleep(delay)
        else:
            logging.error(f"Erro {response.status_code} ao obter dados de 2024 por país (export).")
            return []
    return []




