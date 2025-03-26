# -*- coding: utf-8 -*-
# Versão CORRIGIDA - Baseada no código original funcional, com logging e cache

import streamlit as st
import requests
import pandas as pd # Embora não usado diretamente aqui, pode ser útil no futuro
import logging
import time
import random
from datetime import datetime
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suprime avisos de requisição insegura
warnings.simplefilter('ignore', InsecureRequestWarning)

# --- Função Auxiliar de Requisição (Adaptada do Original com Logging) ---
def _fazer_requisicao(url, method='get', payload=None, max_retries=5, initial_delay=1):
    """
    Função auxiliar para requisições com retry (para 429) e backoff exponencial.
    Suporta GET e POST. Usa logging.
    """
    delay = initial_delay
    response = None # Inicializa response
    for attempt in range(max_retries):
        try:
            logging.debug(f"Tentativa {attempt + 1}/{max_retries} para {url} (Método: {method.upper()})")
            if method.lower() == 'post' and payload:
                response = requests.post(url, json=payload, verify=False, timeout=30) # Timeout maior para POST
            elif method.lower() == 'get':
                response = requests.get(url, verify=False, timeout=20)
            else:
                 logging.error(f"Método de requisição inválido: {method}")
                 return None

            response.raise_for_status() # Levanta erro para 4xx/5xx (exceto 429 tratado abaixo)
            logging.info(f"Requisição bem-sucedida para {url} (Status {response.status_code})")
            return response # Retorna o objeto response completo

        except requests.exceptions.HTTPError as e:
            # Tratamento específico para 429 (Too Many Requests)
            if response is not None and response.status_code == 429:
                logging.warning(f"Erro 429 (Too Many Requests) para {url}. Tentando novamente em {delay:.2f} segundos...")
                time.sleep(delay)
                delay *= 2 # Backoff exponencial
                delay += random.uniform(0, 0.1 * delay) # Adiciona jitter
            # Outros erros HTTP
            else:
                status_code = response.status_code if response is not None else "N/A"
                logging.error(f"Erro HTTP {status_code} ao acessar {url}: {e}")
                return None # Falha após erro HTTP não recuperável
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de Requisição (Conexão/Timeout/Outro) ao acessar {url}: {e}")
            # Pausa antes de tentar novamente em caso de erro de conexão/timeout
            time.sleep(delay)
            delay *= 1.5 # Aumenta o delay um pouco
        except Exception as e:
            logging.error(f"Erro inesperado durante a requisição para {url}: {e}", exc_info=True)
            return None # Falha por erro inesperado

    logging.error(f"Número máximo de tentativas ({max_retries}) excedido para a URL: {url}")
    return None # Retorna None após todas as tentativas falharem

# --- Funções de Obtenção de Dados (Usando URLs e Métodos CORRETOS) ---

@st.cache_data(ttl=86400) # Cache de 1 dia
def obter_data_ultima_atualizacao():
    """
    Obtém a data da última atualização da API Comex Stat (URL CORRETA).
    """
    logging.info("Obtendo data de última atualização (URL CORRETA)...")
    # URL CORRETA do código original
    url = "https://api-comexstat.mdic.gov.br/general/dates/updated"
    response = _fazer_requisicao(url, method='get') # Usa GET para este endpoint

    if response:
        try:
            data = response.json()
            # Estrutura de resposta CORRETA do código original
            update_info = data.get('data', {})
            last_update_date_str = update_info.get("updated")
            last_period_str = update_info.get("lastPeriod") # Assumindo que 'lastPeriod' existe aqui também ou adaptar

            # Tenta extrair ano/mês do lastPeriod se existir, senão usa year/monthNumber
            year = update_info.get("year")
            month = update_info.get("monthNumber")

            if last_period_str and len(last_period_str) == 6:
                 try:
                     year = int(last_period_str[:4])
                     month = int(last_period_str[4:])
                 except (ValueError, TypeError):
                     logging.warning(f"Não foi possível parsear 'lastPeriod': {last_period_str}. Usando 'year'/'monthNumber'.")
                     year = update_info.get("year") # Fallback
                     month = update_info.get("monthNumber") # Fallback

            if last_update_date_str and year and month:
                try:
                    # Garante que ano e mês sejam inteiros
                    year = int(year)
                    month = int(month)
                    logging.info(f"Data de atualização obtida: {last_update_date_str}, Último Período: {month:02d}/{year}")
                    return last_update_date_str, year, month
                except (ValueError, TypeError) as e:
                     logging.error(f"Erro ao converter ano/mês para int: {e}. Ano: {year}, Mês: {month}")
            else:
                logging.error(f"Campos necessários não encontrados na resposta da API de atualização: {data}")

        except requests.exceptions.JSONDecodeError:
            logging.error(f"Erro ao decodificar JSON da resposta de {url}")
        except Exception as e:
            logging.error(f"Erro inesperado ao processar resposta de {url}: {e}", exc_info=True)
    else:
        # _fazer_requisicao já logou o erro
        logging.error("Falha ao obter data de atualização (requisição falhou).")

    return None, None, None # Retorno em caso de falha

@st.cache_data(ttl=3600) # Cache de 1 hora
def obter_descricao_ncm(ncm_code):
    """
    Busca a descrição de um NCM na API (URL CORRETA).
    """
    logging.info(f"Buscando descrição para NCM {ncm_code} (URL CORRETA)...")
    # URL CORRETA do código original
    url = f"https://api-comexstat.mdic.gov.br/tables/ncm/{ncm_code}"
    response = _fazer_requisicao(url, method='get') # Usa GET para este endpoint

    if response:
        try:
            data = response.json()
            # Estrutura de resposta CORRETA do código original
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                description = data['data'][0].get('text', 'Descrição não encontrada (chave ausente)')
                logging.info(f"Descrição obtida para NCM {ncm_code}.")
                return description
            else:
                logging.warning(f"NCM {ncm_code} não encontrado ou formato de resposta inesperado: {data}")
                return "NCM não encontrado"
        except requests.exceptions.JSONDecodeError:
            logging.error(f"Erro ao decodificar JSON da descrição do NCM {ncm_code}")
            return "Erro ao processar descrição"
        except (IndexError, KeyError, TypeError) as e:
             logging.error(f"Erro ao extrair descrição da resposta para NCM {ncm_code}: {e}. Resposta: {data}")
             return "Erro ao processar descrição"
        except Exception as e:
            logging.error(f"Erro inesperado ao obter descrição para NCM {ncm_code}: {e}", exc_info=True)
            return "Erro ao buscar descrição"
    else:
        logging.error(f"Falha na requisição ao buscar descrição para NCM {ncm_code}.")
        return "Erro ao buscar descrição"


@st.cache_data(ttl=3600)
def obter_dados_comerciais(ncm_code, flow_type):
    """
    Busca dados comerciais (histórico mensal completo) usando POST e payload CORRETO.
    Nota: O período original era 2004-2025. Ajustar se necessário.
    """
    logging.info(f"Buscando dados comerciais (histórico) para NCM {ncm_code}, fluxo {flow_type} (POST)...")
    url = "https://api-comexstat.mdic.gov.br/general"
    # Payload CORRETO do código original
    payload = {
        "flow": flow_type,
        "monthDetail": False, # Ajuste conforme necessidade (original era False)
        "period": {
            "from": "2004-01", # Período original
            "to": "2025-12"   # Período original
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": [], # Ajuste se precisar de detalhes (ex: 'country')
        "metrics": ["metricFOB", "metricKG"]
    }
    response = _fazer_requisicao(url, method='post', payload=payload)
    dados = []
    erro = None
    if response:
        try:
            # Estrutura de resposta CORRETA do código original
            data_list = response.json().get('data', {}).get('list', [])
            dados = data_list
            logging.info(f"Dados comerciais (histórico) obtidos para NCM {ncm_code}, fluxo {flow_type}. {len(dados)} registros.")
        except requests.exceptions.JSONDecodeError:
            erro = f"Erro ao decodificar JSON de dados comerciais para NCM {ncm_code}, fluxo {flow_type}."
            logging.error(erro)
        except Exception as e:
            erro = f"Erro inesperado ao processar dados comerciais: {e}"
            logging.error(erro + f" NCM: {ncm_code}, Fluxo: {flow_type}", exc_info=True)
    else:
        erro = f"Falha ao obter dados comerciais (histórico) para NCM {ncm_code}, fluxo {flow_type} (requisição POST falhou)."
        logging.warning(erro) # Já logado em _fazer_requisicao, mas bom ter aqui

    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_comerciais_ano_anterior(ncm_code, flow_type, last_updated_month):
    """
    Busca dados comerciais do ano anterior (2024) até o mês atualizado (POST).
    """
    # TODO: Tornar o ano dinâmico se necessário
    ano_anterior = datetime.now().year - 1 # Ou fixo 2024 se preferir
    mes_final_str = f"{last_updated_month:02d}" # Garante 2 dígitos
    periodo_from = f"{ano_anterior}-01"
    periodo_to = f"{ano_anterior}-{mes_final_str}"

    logging.info(f"Buscando dados ({periodo_from} a {periodo_to}) para NCM {ncm_code}, fluxo {flow_type} (POST)...")
    url = "https://api-comexstat.mdic.gov.br/general"
    # Payload CORRETO do código original, adaptado para o período
    payload = {
        "flow": flow_type,
        "monthDetail": False,
        "period": {
            "from": periodo_from,
            "to": periodo_to
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": [],
        "metrics": ["metricFOB", "metricKG"]
    }
    response = _fazer_requisicao(url, method='post', payload=payload)
    dados = []
    erro = None
    if response:
        try:
            data_list = response.json().get('data', {}).get('list', [])
            dados = data_list
            logging.info(f"Dados ({ano_anterior} - até mês {mes_final_str}) obtidos para NCM {ncm_code}, fluxo {flow_type}. {len(dados)} registros.")
        except requests.exceptions.JSONDecodeError:
            erro = f"Erro JSON dados ano anterior NCM {ncm_code}, fluxo {flow_type}."
            logging.error(erro)
        except Exception as e:
            erro = f"Erro inesperado processar dados ano anterior: {e}"
            logging.error(erro + f" NCM: {ncm_code}, Fluxo: {flow_type}", exc_info=True)
    else:
        erro = f"Falha ao obter dados ({ano_anterior} - até mês {mes_final_str}) para NCM {ncm_code}, fluxo {flow_type} (POST falhou)."
        logging.warning(erro)

    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_comerciais_ano_atual(ncm_code, flow_type, last_updated_month):
    """
    Busca dados comerciais do ano atual até o último mês atualizado (POST).
    """
    # TODO: Tornar o ano dinâmico se necessário
    ano_atual = datetime.now().year # Ou fixo 2025 se preferir
    mes_final_str = f"{last_updated_month:02d}" # Garante 2 dígitos
    periodo_from = f"{ano_atual}-01"
    periodo_to = f"{ano_atual}-{mes_final_str}"

    logging.info(f"Buscando dados ({periodo_from} a {periodo_to}) para NCM {ncm_code}, fluxo {flow_type} (POST)...")
    url = "https://api-comexstat.mdic.gov.br/general"
    # Payload CORRETO do código original, adaptado para o período
    payload = {
        "flow": flow_type,
        "monthDetail": False,
        "period": {
            "from": periodo_from,
            "to": periodo_to
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": [],
        "metrics": ["metricFOB", "metricKG"]
    }
    response = _fazer_requisicao(url, method='post', payload=payload)
    dados = []
    erro = None
    if response:
        try:
            data_list = response.json().get('data', {}).get('list', [])
            dados = data_list
            logging.info(f"Dados ({ano_atual} - até mês {mes_final_str}) obtidos para NCM {ncm_code}, fluxo {flow_type}. {len(dados)} registros.")
        except requests.exceptions.JSONDecodeError:
            erro = f"Erro JSON dados ano atual NCM {ncm_code}, fluxo {flow_type}."
            logging.error(erro)
        except Exception as e:
            erro = f"Erro inesperado processar dados ano atual: {e}"
            logging.error(erro + f" NCM: {ncm_code}, Fluxo: {flow_type}", exc_info=True)
    else:
        erro = f"Falha ao obter dados ({ano_atual} - até mês {mes_final_str}) para NCM {ncm_code}, fluxo {flow_type} (POST falhou)."
        logging.warning(erro)

    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_2024_por_pais(ncm_code):
    """
    Obtém dados de IMPORTAÇÃO (US$ FOB) para 2024, detalhados por país (POST).
    """
    logging.info(f"Buscando dados de importação 2024 por país para NCM {ncm_code} (POST)...")
    url = "https://api-comexstat.mdic.gov.br/general"
    # Payload CORRETO do código original
    payload = {
        "flow": "import",
        "monthDetail": False,
        "period": {
            "from": "2024-01",
            "to": "2024-12" # Ano completo
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": ["country"], # Detalhe por país
        "metrics": ["metricFOB"]
    }
    response = _fazer_requisicao(url, method='post', payload=payload)
    dados = []
    erro = None
    if response:
        try:
            data_list = response.json().get('data', {}).get('list', [])
            dados = data_list
            logging.info(f"Dados de importação 2024 por país obtidos para NCM {ncm_code}. {len(dados)} registros.")
        except requests.exceptions.JSONDecodeError:
            erro = f"Erro JSON dados import 2024 por país NCM {ncm_code}."
            logging.error(erro)
        except Exception as e:
            erro = f"Erro inesperado processar dados import 2024 por país: {e}"
            logging.error(erro + f" NCM: {ncm_code}", exc_info=True)
    else:
        erro = f"Falha ao obter dados import 2024 por país para NCM {ncm_code} (POST falhou)."
        logging.warning(erro)

    # Retorna dados e erro para consistência com outras funções
    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_2024_por_pais_export(ncm_code):
    """
    Obtém dados de EXPORTAÇÃO (US$ FOB) para 2024, detalhados por país (POST).
    """
    logging.info(f"Buscando dados de exportação 2024 por país para NCM {ncm_code} (POST)...")
    url = "https://api-comexstat.mdic.gov.br/general"
    # Payload CORRETO do código original
    payload = {
        "flow": "export",
        "monthDetail": False,
        "period": {
            "from": "2024-01",
            "to": "2024-12" # Ano completo
        },
        "filters": [{"filter": "ncm", "values": [ncm_code]}],
        "details": ["country"], # Detalhe por país
        "metrics": ["metricFOB"]
    }
    response = _fazer_requisicao(url, method='post', payload=payload)
    dados = []
    erro = None
    if response:
        try:
            data_list = response.json().get('data', {}).get('list', [])
            dados = data_list
            logging.info(f"Dados de exportação 2024 por país obtidos para NCM {ncm_code}. {len(dados)} registros.")
        except requests.exceptions.JSONDecodeError:
            erro = f"Erro JSON dados export 2024 por país NCM {ncm_code}."
            logging.error(erro)
        except Exception as e:
            erro = f"Erro inesperado processar dados export 2024 por país: {e}"
            logging.error(erro + f" NCM: {ncm_code}", exc_info=True)
    else:
        erro = f"Falha ao obter dados export 2024 por país para NCM {ncm_code} (POST falhou)."
        logging.warning(erro)

    # Retorna dados e erro para consistência
    return dados, erro

# Função obter_dados_importacao_12meses (se necessária, adaptar para POST)
# Se você precisar da função que busca os últimos 12 meses, me diga
# e eu a adaptarei para usar o método POST e o payload correto.

# Remover a função processar_dados daqui se ela não for mais usada neste módulo
# def processar_dados(dados_export, dados_import, ano_ref): ...





