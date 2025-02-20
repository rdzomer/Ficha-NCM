import requests

def obter_data_ultima_atualizacao():
    """ Obtém a data da última atualização da API do ComexStat """
    url = "https://api-comexstat.mdic.gov.br/general/dates/updated"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            last_updated_date = data.get('data', {}).get('updated', "Data não encontrada")
            last_updated_year = data.get('data', {}).get('year', "Ano não encontrado")
            last_updated_month = data.get('data', {}).get('monthNumber', "Mês não encontrado")
            return last_updated_date, last_updated_year, last_updated_month
        else:
            return None, None, None
    except Exception as e:
        return None, None, None

def obter_descricao_ncm(ncm_code):
    """ Obtém a descrição do NCM informado """
    url = f"https://api-comexstat.mdic.gov.br/tables/ncm/{ncm_code}"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0].get('text', 'Descrição não encontrada')
            else:
                return 'Descrição não encontrada'
        else:
            return f"Erro na requisição: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Erro ao realizar a requisição: {str(e)}"

def obter_dados_comerciais(ncm_code, flow):
    """ Obtém dados de importação ou exportação para um NCM específico """
    url = "https://api-comexstat.mdic.gov.br/general"
    body = {
        "flow": flow,  # "import" para importações, "export" para exportações
        "monthDetail": False,  # Buscar dados anuais
        "period": {
            "from": "2004-01",
            "to": "2025-12"
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],  # Filtro pelo código NCM
        "details": [],
        "metrics": ["metricFOB", "metricKG"]
    }

    try:
        response = requests.post(url, json=body, verify=False)
        if response.status_code == 401:
            return None, "Erro 401: Acesso à API não autorizado!"
        if response.status_code == 200:
            data = response.json().get('data', {}).get('list', [])
            return data, None
        else:
            return [], f"Erro na requisição: {response.status_code} - {response.text}"
    except Exception as e:
        return [], f"Erro ao obter dados: {str(e)}"

def obter_dados_comerciais_ano_anterior(ncm_code, flow, last_updated_month):
    """ Obtém os dados acumulados de 2024 até o último mês disponível para comparação com 2025. """

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

    try:
        response = requests.post(url, json=payload, verify=False)

        if response.status_code == 401:
            return [], "Erro 401: Acesso à API não autorizado!"
        if response.status_code == 200:
            data = response.json().get('data', {}).get('list', [])
            return data, None
        else:
            return [], f"Erro na requisição: {response.status_code} - {response.text}"

    except Exception as e:
        return [], f"Erro ao obter dados: {str(e)}"
