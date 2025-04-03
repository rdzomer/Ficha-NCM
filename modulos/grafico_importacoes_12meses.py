# modulos/grafico_importacoes_12meses.py (COMPLETO - VERSÃO PLOTLY COM NOME ORIGINAL)

import requests
import time
import logging
import pandas as pd
import numpy as np
import plotly.express as px # Importar Plotly Express em vez de Matplotlib
import plotly.graph_objects as go # Necessário para type hinting e verificações
import streamlit as st # Para exibir mensagens de aviso/info diretamente

# Configuração do logging (pode herdar do app principal, mas é bom garantir)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [GRAFICO_12M] - %(message)s')

# Suprimindo avisos de requisição HTTPS não verificada
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Funções Auxiliares (com melhorias de robustez e logging) ---

def _obter_dados_mensais_comex(ncm_code: str, flow: str, max_retries: int = 5, delay: int = 11) -> list:
    """
    Faz requisições à API do ComexStat para obter dados mensais (monthDetail = True)
    de 2019-01 até 2025-12, retornando a lista de dicionários com os resultados.

    Args:
        ncm_code (str): Código NCM a ser consultado.
        flow (str): 'import' ou 'export'.
        max_retries (int): Número máximo de tentativas de requisição.
        delay (int): Tempo de espera em segundos entre tentativas em caso de erro 429.

    Returns:
        list: Lista de dicionários com os dados ou lista vazia em caso de erro/sem dados.
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    body = {
        "flow": flow,
        "monthDetail": True,
        "period": {
            "from": "2019-01",
            # Busca um período amplo; o processamento focará nos últimos anos
            "to": "2025-12"
        },
        "filters": [
            {"filter": "ncm", "values": [ncm_code]}
        ],
        "details": ["ncm"], # Detalhe por NCM
        "metrics": ["metricKG"] # Métrica de Quilograma Líquido
    }

    logging.info(f"Buscando dados ({flow}) para NCM {ncm_code}...")
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=body, verify=False, timeout=60) # Adicionado timeout
            response.raise_for_status() # Lança exceção para erros HTTP (4xx ou 5xx)

            # Verifica se a resposta é JSON e contém os dados esperados
            if 'application/json' in response.headers.get('Content-Type', ''):
                data = response.json()
                # Adiciona verificação se 'data' e 'list' existem antes de acessá-los
                list_data = data.get('data', {}).get('list', [])
                if list_data is not None: # Garante que é uma lista (mesmo vazia)
                    logging.info(f"Dados ({flow}) para NCM {ncm_code} recebidos: {len(list_data)} registros.")
                    return list_data
                else:
                    logging.warning(f"API retornou 'list' como None para NCM {ncm_code} ({flow}). Tratando como vazio.")
                    return []
            else:
                logging.error(f"Resposta inesperada da API (não JSON) para NCM {ncm_code} ({flow}): {response.text[:200]}...")
                return [] # Retorna vazio se não for JSON

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                logging.warning(f"Erro 429 (API ocupada) para NCM {ncm_code} ({flow}). Tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s.")
                time.sleep(delay)
            else:
                # Log detalhado para outros erros HTTP
                logging.error(f"Erro HTTP na API ({flow}) para NCM {ncm_code}: {http_err}")
                logging.error(f"Status Code: {response.status_code}, Response: {response.text[:500]}")
                return [] # Retorna vazio em outros erros HTTP
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Erro de Conexão/Timeout na API ({flow}) para NCM {ncm_code}: {req_err}")
            if attempt < max_retries - 1:
                logging.info(f"Tentando novamente em {delay}s...")
                time.sleep(delay) # Espera antes de tentar novamente em erros de conexão
            else:
                logging.error(f"Falha de conexão persistente para NCM {ncm_code} ({flow}).")
                return [] # Retorna vazio após todas as tentativas falharem
        except Exception as e:
             # Captura qualquer outro erro inesperado durante a requisição/processamento inicial JSON
             logging.error(f"Erro inesperado ao processar requisição API ({flow}) para NCM {ncm_code}: {e}", exc_info=True)
             return [] # Retorna vazio para erros inesperados

    # Se o loop terminar sem sucesso (ex: só erro 429)
    logging.error(f"Falha ao obter dados da API para NCM {ncm_code} ({flow}) após {max_retries} tentativas.")
    return [] # Retorna vazio


def _calcular_soma_movel(df: pd.DataFrame, column: str, window: int = 12) -> pd.Series:
    """
    Calcula a soma móvel de 'column' usando uma janela definida.
    Retorna NaN onde não há dados suficientes para a janela completa.

    Args:
        df (pd.DataFrame): DataFrame com os dados, indexado por data.
        column (str): Nome da coluna para calcular a soma móvel.
        window (int): Tamanho da janela móvel (padrão: 12).

    Returns:
        pd.Series: Series contendo a soma móvel.
                   Retorna uma Series vazia se a coluna não existir ou for inválida.
    """
    # Verifica se a coluna existe
    if column not in df.columns:
        logging.error(f"Coluna '{column}' não encontrada no DataFrame para cálculo da soma móvel.")
        return pd.Series(dtype=float) # Retorna Series vazia

    # Tenta converter para numérico, preenchendo erros com 0
    numeric_column = pd.to_numeric(df[column], errors='coerce').fillna(0)

    # Calcula a soma móvel.
    # min_periods=window garante que o cálculo só é feito quando há 'window' períodos.
    # Isso resulta em NaN nos primeiros 'window-1' períodos, que serão filtrados depois.
    rolling_sum = numeric_column.rolling(window=window, min_periods=window).sum()
    logging.info(f"Soma móvel de {window} meses calculada para coluna '{column}'.")
    return rolling_sum


# --- Função Principal (Nome Original, Corpo Atualizado para Plotly) ---

def gerar_grafico_importacoes_12meses(ncm_code: str, ncm_str: str) -> go.Figure | None:
    """
    Gera o gráfico de Importações Acumuladas nos Últimos 12 Meses (em KG) usando Plotly.
    Busca dados mensais, calcula a soma móvel de 12 meses e plota um gráfico de barras.

    Args:
        ncm_code (str): Código NCM numérico (ex: "39269090").
        ncm_str (str): Representação formatada do NCM para o título (ex: "3926.90.90").

    Returns:
        plotly.graph_objects.Figure or None: Objeto Figure do Plotly se sucesso, None caso contrário.
    """
    logging.info(f"Iniciando geração do gráfico de importações acumuladas 12m para NCM {ncm_code}")

    # 1. Obter dados mensais de importação
    dados_import = _obter_dados_mensais_comex(ncm_code, 'import')

    # Retorna None cedo se não houver dados ou erro na API
    if not dados_import:
        logging.warning(f"Nenhum dado de importação retornado pela API para NCM {ncm_code}.")
        # Não mostra st.warning aqui, deixa o app.py tratar o None retornado
        return None

    try:
        # 2. Transformar em DataFrame e tratar dados iniciais
        df_import = pd.DataFrame(dados_import)
        logging.debug(f"DataFrame inicial criado com {len(df_import)} linhas.")

        # Verifica colunas essenciais
        required_cols = ['year', 'monthNumber', 'metricKG']
        if not all(col in df_import.columns for col in required_cols):
            logging.error(f"Colunas essenciais {required_cols} ausentes nos dados da API para NCM {ncm_code}.")
            return None

        # Conversão para tipos numéricos, tratando erros
        df_import['year'] = pd.to_numeric(df_import['year'], errors='coerce')
        df_import['monthNumber'] = pd.to_numeric(df_import['monthNumber'], errors='coerce')
        df_import['metricKG'] = pd.to_numeric(df_import['metricKG'], errors='coerce').fillna(0)

        # Remove linhas onde ano ou mês não puderam ser convertidos (essenciais para data)
        df_import.dropna(subset=['year', 'monthNumber'], inplace=True)
        if df_import.empty:
             logging.warning(f"DataFrame vazio após tratamento inicial (ano/mês inválidos) para NCM {ncm_code}.")
             return None
        logging.debug(f"DataFrame após tratamento numérico e dropna: {len(df_import)} linhas.")

        # Converte ano e mês para inteiros (necessário para criar data)
        df_import['year'] = df_import['year'].astype(int)
        df_import['monthNumber'] = df_import['monthNumber'].astype(int)

        # 3. Criar coluna de data (primeiro dia do mês)
        try:
            df_import['date'] = pd.to_datetime(
                df_import['year'].astype(str) + '-' +
                df_import['monthNumber'].astype(str).str.zfill(2) + '-01',
                errors='coerce' # Coerce para NaT se a data for inválida
            )
            df_import.dropna(subset=['date'], inplace=True) # Remove datas inválidas
            if df_import.empty:
                logging.warning(f"DataFrame vazio após criação/validação da coluna 'date' para NCM {ncm_code}.")
                return None
            logging.debug(f"Coluna 'date' criada. {len(df_import)} linhas restantes.")
        except Exception as e_date:
            logging.error(f"Erro ao criar coluna de data para NCM {ncm_code}: {e_date}", exc_info=True)
            return None

        # Ordena e define índice de data (importante para reindex e rolling)
        df_import.sort_values('date', inplace=True)
        df_import.set_index('date', inplace=True)

        # 4. Criar um índice com todos os meses no intervalo para preencher lacunas
        # Usa o min/max do índice (que agora é a data)
        start_date = df_import.index.min()
        end_date = df_import.index.max()

        # Garante que start_date e end_date sejam válidos
        if pd.isna(start_date) or pd.isna(end_date):
            logging.error(f"Datas min/max inválidas (NaT) encontradas após indexação para NCM {ncm_code}.")
            return None

        all_months = pd.date_range(start=start_date, end=end_date, freq='MS') # 'MS' = Month Start frequency
        # Reindexa usando o índice de data, preenchendo meses ausentes com 0
        df_import = df_import.reindex(all_months, fill_value=0)
        logging.debug(f"DataFrame reindexado para todos os meses ({len(df_import)} linhas).")


        # 5. Calcular a soma móvel de 12 meses
        # A função _calcular_soma_movel usa min_periods=12 por padrão
        df_import['soma_movel_12m'] = _calcular_soma_movel(df_import, 'metricKG', window=12)


        # 6. Filtrar para remover os primeiros meses onde a soma móvel é NaN
        # Isso ocorre porque min_periods=12 no cálculo da soma móvel.
        df_plot = df_import.dropna(subset=['soma_movel_12m']).copy() # Usa cópia para evitar SettingWithCopyWarning
        # Reset index para ter 'date' como coluna novamente para Plotly
        df_plot.reset_index(inplace=True)
        # Renomeia a coluna 'index' (criada pelo reset_index) para 'date'
        df_plot.rename(columns={'index': 'date'}, inplace=True)


        # Verifica se há dados para plotar após calcular e filtrar a soma móvel
        if df_plot.empty:
            logging.warning(f"Nenhum dado para plotar após cálculo da soma móvel de 12m (NCM {ncm_code}). Pode indicar período de dados < 12 meses.")
            # Informa o usuário via Streamlit se nenhum dado de 12m está disponível
            st.info(f"Não há dados suficientes (mínimo 12 meses consecutivos) para calcular a importação acumulada para o NCM {ncm_str}.")
            return None
        logging.debug(f"DataFrame final para plotagem ({len(df_plot)} barras).")

        # 7. Plotar o gráfico com Plotly Express
        fig = px.bar(
            df_plot,
            x='date',
            y='soma_movel_12m',
            title=f'Importações Acumuladas (12 Meses Móveis) em KG - NCM {ncm_str}',
            labels={ # Rótulos mais descritivos
                'date': 'Mês de Referência (Fim do Período de 12m)',
                'soma_movel_12m': 'Quantidade Acumulada (KG)'
            },
            color_discrete_sequence=['steelblue'] # Cor similar ao Matplotlib original
        )

        # 8. Ajustar Layout e Eixos (equivalente às formatações do matplotlib)
        fig.update_layout(
            xaxis_title=None, # Remove o título do eixo X como no original
            yaxis_title='Quantidade Acumulada (KG)',
            xaxis_tickformat='%Y-%m', # Formato do eixo X (Ano-Mês)
            yaxis_tickformat=',.0f', # Formato do eixo Y (separador de milhar ','. Sem decimais '0f')
            title_x=0.5, # Centraliza o título do gráfico
            bargap=0.2, # Espaçamento entre barras (ajuste conforme preferência visual)
            hovermode='x unified', # Melhora a dica de ferramenta (tooltip)
            # Aumenta margem inferior para acomodar rótulos rotacionados do eixo X
            margin=dict(l=60, r=30, t=50, b=100)
        )

        # Adiciona gridlines no eixo Y (similar ao ax.yaxis.grid)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.25)')

        # Rotaciona os rótulos do eixo X para melhor legibilidade
        fig.update_xaxes(tickangle=-45)

        # NOTA: A fonte ("Fonte: Comex Stat...") não é adicionada aqui.
        # Deve ser adicionada em app.py usando st.caption() após st.plotly_chart().

        logging.info(f"Gráfico Plotly de importações acumuladas 12m gerado com sucesso para NCM {ncm_code}.")
        return fig # Retorna o objeto Figure do Plotly

    # Captura exceções gerais durante o processamento do DataFrame ou Plotly
    except Exception as e:
        logging.error(f"Erro inesperado ao gerar gráfico de importações acumuladas 12m para NCM {ncm_code}: {e}", exc_info=True)
        # Informa o usuário sobre o erro via Streamlit
        st.error(f"Ocorreu um erro inesperado ao gerar o gráfico de importações acumuladas para {ncm_str}. Verifique os logs para detalhes.")
        return None



