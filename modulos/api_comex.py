# -*- coding: utf-8 -*-
# Versão Restaurada - Simples com Retry e verify=False

import streamlit as st
import requests
import pandas as pd
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from datetime import datetime
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suprime avisos de requisição insegura
warnings.simplefilter('ignore', InsecureRequestWarning)

# --- Configuração de Retentativas ---
def _create_retry_session():
    """Cria uma sessão de requests com política de retentativa."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3, # Número de tentativas
        status_forcelist=[429, 500, 502, 503, 504], # Códigos que disparam retentativa
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1 # Tempo de espera (1s, 2s, 4s...)
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# --- Função Central de Requisição ---
def _make_request(url, params=None, headers=None):
    """Faz uma requisição GET com retentativas e VERIFICAÇÃO SSL DESABILITADA."""
    session = _create_retry_session()
    logging.debug(f"Executando requisição para {url} com VERIFICAÇÃO SSL DESABILITADA.")
    try:
        response = session.get(url, params=params, headers=headers, timeout=20, verify=False) # verify=False AQUI
        response.raise_for_status() # Verifica erros HTTP após retentativas
        logging.info(f"Requisição bem-sucedida para {url} (status {response.status_code}).")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Erro HTTP persistente ao acessar {url}: {http_err} (Status: {response.status_code if 'response' in locals() else 'N/A'})")
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Erro de Conexão ao acessar {url}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout ao acessar {url}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro na requisição para {url}: {req_err}")
    except Exception as e:
        logging.error(f"Erro desconhecido durante a requisição para {url}: {e}", exc_info=True)

    return None # Retorna None em caso de qualquer erro

# --- Funções de Obtenção de Dados (com Cache) ---
# (As funções obter_data_ultima_atualizacao, obter_descricao_ncm, etc.,
# permanecem exatamente como na última versão funcional, usando _make_request acima)

@st.cache_data(ttl=86400) # Cache de 1 dia
def obter_data_ultima_atualizacao():
    """Obtém a data da última atualização dos dados da API Comex Stat."""
    logging.info("Obtendo data de última atualização da API Comex...")
    url = "https://api-comexstat.mdic.gov.br/general/update"
    data = _make_request(url)
    if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        update_info = data[0]
        last_update_date_str = update_info.get("lastUpdate")
        last_period_str = update_info.get("lastPeriod")
        if last_update_date_str and last_period_str and len(last_period_str) == 6:
            try:
                year = int(last_period_str[:4])
                month = int(last_period_str[4:])
                logging.info(f"Data de atualização obtida: {last_update_date_str}, Último Período: {month:02d}/{year}")
                return last_update_date_str, year, month
            except (ValueError, TypeError) as e:
                logging.error(f"Erro ao processar data/período da API: {e}. Data: {last_update_date_str}, Período: {last_period_str}")
        else:
            logging.error(f"Formato inesperado na resposta da API de atualização: {update_info}")
    else:
        if data is None:
             logging.error("Falha na requisição (_make_request retornou None) ao obter data de atualização.")
        else:
             logging.error(f"Resposta inválida ou vazia da API de atualização: {data}")
    return None, None, None

@st.cache_data(ttl=3600) # Cache de 1 hora
def obter_descricao_ncm(ncm_code):
    """Busca a descrição de um NCM na API."""
    logging.info(f"Buscando descrição para NCM {ncm_code}...")
    url = f"https://api-comexstat.mdic.gov.br/general/ncm/{ncm_code}"
    data = _make_request(url)
    if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        description = data[0].get("description")
        if description:
            logging.info(f"Descrição obtida para NCM {ncm_code}.")
            return description
        else:
            logging.warning(f"Campo 'description' não encontrado na resposta da API para NCM {ncm_code}.")
            return "Descrição não encontrada"
    elif data == []:
        logging.warning(f"NCM {ncm_code} não encontrado na API.")
        return "NCM não encontrado"
    else:
        if data is None:
             logging.error(f"Falha na requisição ao buscar descrição para NCM {ncm_code}.")
        else:
             logging.error(f"Erro ou resposta inesperada ao buscar descrição para NCM {ncm_code}: {data}")
        return "Erro ao buscar descrição"

@st.cache_data(ttl=3600)
def obter_dados_comerciais(ncm_code, flow_type):
    """Busca dados comerciais (histórico mensal completo) para um NCM e fluxo."""
    logging.info(f"Buscando dados comerciais (histórico) para NCM {ncm_code}, fluxo {flow_type}...")
    endpoint = "https://api-comexstat.mdic.gov.br/general"
    params = {"flow": flow_type, "type": "monthly", "ncm": ncm_code, "detailed": "false"}
    dados = []
    erro = None
    try:
        response_data = _make_request(endpoint, params)
        if response_data is not None:
            dados = response_data
            logging.info(f"Dados comerciais (histórico) obtidos para NCM {ncm_code}, fluxo {flow_type}. {len(dados)} registros.")
        else:
            erro = f"Falha ao obter dados comerciais (histórico) para NCM {ncm_code}, fluxo {flow_type} (requisição falhou)."
            logging.warning(erro)
    except Exception as e:
        erro = f"Erro inesperado ao processar dados comerciais (histórico): {e}"
        logging.error(erro + f" NCM: {ncm_code}, Fluxo: {flow_type}", exc_info=True)
    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_comerciais_ano_anterior(ncm_code, flow_type, last_updated_month):
    """Busca dados comerciais do ano anterior, até o mês correspondente ao último atualizado."""
    # TODO: Obter ano dinamicamente
    ano_anterior = 2024
    mes_final_str = f"{last_updated_month:02d}"
    periodo = f"{ano_anterior}01-{ano_anterior}{mes_final_str}"
    logging.info(f"Buscando dados ({ano_anterior} - até mês {mes_final_str}) para NCM {ncm_code}, fluxo {flow_type}...")
    endpoint = "https://api-comexstat.mdic.gov.br/general"
    params = {"flow": flow_type, "type": "monthly", "period": periodo, "ncm": ncm_code, "detailed": "false"}
    dados = []
    erro = None
    try:
        response_data = _make_request(endpoint, params)
        if response_data is not None:
            dados = response_data
            logging.info(f"Dados ({ano_anterior} - até mês {mes_final_str}) obtidos para NCM {ncm_code}, fluxo {flow_type}. {len(dados)} registros.")
        else:
            erro = f"Falha ao obter dados ({ano_anterior} - até mês {mes_final_str}) para NCM {ncm_code}, fluxo {flow_type}."
            logging.warning(erro)
    except Exception as e:
        erro = f"Erro inesperado ao processar dados ({ano_anterior} - até mês {mes_final_str}): {e}"
        logging.error(erro + f" NCM: {ncm_code}, Fluxo: {flow_type}", exc_info=True)
    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_comerciais_ano_atual(ncm_code, flow_type, last_updated_month):
    """Busca dados comerciais do ano atual, até o último mês atualizado."""
    # TODO: Obter ano dinamicamente
    ano_atual = 2025
    mes_final_str = f"{last_updated_month:02d}"
    periodo = f"{ano_atual}01-{ano_atual}{mes_final_str}"
    logging.info(f"Buscando dados ({ano_atual} - até mês {mes_final_str}) para NCM {ncm_code}, fluxo {flow_type}...")
    endpoint = "https://api-comexstat.mdic.gov.br/general"
    params = {"flow": flow_type, "type": "monthly", "period": periodo, "ncm": ncm_code, "detailed": "false"}
    dados = []
    erro = None
    try:
        response_data = _make_request(endpoint, params)
        if response_data is not None:
            dados = response_data
            logging.info(f"Dados ({ano_atual} - até mês {mes_final_str}) obtidos para NCM {ncm_code}, fluxo {flow_type}. {len(dados)} registros.")
        else:
            erro = f"Falha ao obter dados ({ano_atual} - até mês {mes_final_str}) para NCM {ncm_code}, fluxo {flow_type}."
            logging.warning(erro)
    except Exception as e:
        erro = f"Erro inesperado ao processar dados ({ano_atual} - até mês {mes_final_str}): {e}"
        logging.error(erro + f" NCM: {ncm_code}, Fluxo: {flow_type}", exc_info=True)
    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_2024_por_pais(ncm_code):
    """Busca dados de IMPORTAÇÃO de 2024 por país para um NCM."""
    logging.info(f"Buscando dados de importação 2024 por país para NCM {ncm_code}...")
    endpoint = "https://api-comexstat.mdic.gov.br/general"
    params = {"flow": "import", "type": "monthly", "period": "2024", "ncm": ncm_code, "breakdown": "country"}
    dados = []
    erro = None
    try:
        response_data = _make_request(endpoint, params)
        if response_data is not None:
            dados = response_data
            logging.info(f"Dados de importação 2024 por país obtidos para NCM {ncm_code}. {len(dados)} registros.")
        else:
            erro = "Falha ao obter dados de importação 2024 por país (requisição falhou)."
            logging.warning(erro + f" NCM: {ncm_code}")
    except Exception as e:
        erro = f"Erro inesperado ao processar dados de importação 2024 por país: {e}"
        logging.error(erro + f" NCM: {ncm_code}", exc_info=True)
    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_2024_por_pais_export(ncm_code):
    """Busca dados de EXPORTAÇÃO de 2024 por país para um NCM."""
    logging.info(f"Buscando dados de exportação 2024 por país para NCM {ncm_code}...")
    endpoint = "https://api-comexstat.mdic.gov.br/general"
    params = {"flow": "export", "type": "monthly", "period": "2024", "ncm": ncm_code, "breakdown": "country"}
    dados = []
    erro = None
    try:
        response_data = _make_request(endpoint, params)
        if response_data is not None:
            dados = response_data
            logging.info(f"Dados de exportação 2024 por país obtidos para NCM {ncm_code}. {len(dados)} registros.")
        else:
            erro = "Falha ao obter dados de exportação 2024 por país (requisição falhou)."
            logging.warning(erro + f" NCM: {ncm_code}")
    except Exception as e:
        erro = f"Erro inesperado ao processar dados de exportação 2024 por país: {e}"
        logging.error(erro + f" NCM: {ncm_code}", exc_info=True)
    return dados, erro

@st.cache_data(ttl=3600)
def obter_dados_importacao_12meses(ncm_code):
    """Busca dados mensais de importação dos últimos 12 meses disponíveis."""
    logging.info(f"Buscando dados de importação dos últimos 12 meses para NCM {ncm_code}...")
    periodo = None
    try:
        data_atualizacao, end_year, end_month = obter_data_ultima_atualizacao()
        if end_year is None or end_month is None:
            logging.error("Não foi possível obter a data de atualização para calcular os últimos 12 meses.")
            return [], "Erro ao obter data de atualização"
        end_date = datetime(end_year, end_month, 1)
        start_year = end_year if end_month > 11 else end_year - 1
        start_month = (end_month - 11) if end_month > 11 else (end_month - 11 + 12)
        periodo = f"{start_year}{start_month:02d}-{end_year}{end_month:02d}"
        logging.info(f"Período calculado para 12 meses: {periodo}")
    except Exception as e:
        logging.error(f"Erro ao calcular período de 12 meses: {e}", exc_info=True)
        return [], f"Erro ao calcular período: {e}"

    if not periodo:
         return [], "Não foi possível determinar o período de 12 meses."

    endpoint = "https://api-comexstat.mdic.gov.br/general"
    params = {"flow": "import", "type": "monthly", "period": periodo, "ncm": ncm_code, "detailed": "false"}
    dados = []
    erro = None
    try:
        response_data = _make_request(endpoint, params)
        if response_data is not None:
            dados = response_data
            logging.info(f"Dados de importação 12 meses obtidos para NCM {ncm_code}. {len(dados)} registros.")
        else:
            erro = f"Falha ao obter dados de importação 12 meses para NCM {ncm_code}."
            logging.warning(erro)
    except Exception as e:
        erro = f"Erro inesperado ao buscar dados de importação 12 meses: {e}"
        logging.error(erro + f" NCM: {ncm_code}", exc_info=True)
    return dados, erro



