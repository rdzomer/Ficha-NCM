import requests
import time
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

logging.basicConfig(level=logging.INFO)

# Suprimindo avisos de requisição HTTPS não verificada
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _obter_dados_mensais_comex(ncm_code, flow, max_retries=5, delay=11):
    """
    Faz requisições à API do ComexStat para obter dados mensais (monthDetail = True)
    de 2019-01 até 2025-12, retornando a lista de dicionários com os resultados.
    """
    url = "https://api-comexstat.mdic.gov.br/general"
    body = {
        "flow": flow,
        "monthDetail": True,
        "period": {
            "from": "2019-01",
            "to": "2025-12"
        },
        "filters": [
            {"filter": "ncm", "values": [ncm_code]}
        ],
        "details": ["ncm"],
        "metrics": ["metricKG"]
    }
    
    for attempt in range(max_retries):
        response = requests.post(url, json=body, verify=False)
        if response.status_code == 200:
            data = response.json().get('data', {}).get('list', [])
            return data
        elif response.status_code == 429:
            logging.error(f"Erro 429 (Muitas requisições). Aguardando {delay}s antes de tentar novamente.")
            time.sleep(delay)
        else:
            logging.error(f"Erro na requisição ({flow}): {response.status_code}")
            logging.error(response.text)
            return []
        time.sleep(delay)
    return []

def _calcular_soma_movel(df, column, window=12):
    """
    Calcula a soma móvel de 'column' usando uma janela de 12 meses.
    """
    return df[column].rolling(window=window, min_periods=1).sum()

def gerar_grafico_importacoes_12meses(ncm_code, ncm_str):
    """
    Gera o gráfico de Importações Acumuladas nos Últimos 12 Meses (em KG),
    retornando o objeto Figure do matplotlib para ser exibido via st.pyplot.
    """
    # 1. Obter dados mensais de importação
    dados_import = _obter_dados_mensais_comex(ncm_code, 'import')
    if not dados_import:
        logging.info("Nenhum dado encontrado para os filtros especificados.")
        return None  # Retornamos None caso não haja dados

    # 2. Transformar em DataFrame
    df_import = pd.DataFrame(dados_import)
    df_import['year'] = pd.to_numeric(df_import['year'], errors='coerce')
    df_import['monthNumber'] = pd.to_numeric(df_import['monthNumber'], errors='coerce')
    df_import['metricKG'] = pd.to_numeric(df_import['metricKG'], errors='coerce').fillna(0)

    # 3. Criar coluna de data e ordenar
    df_import['date'] = pd.to_datetime(
        df_import['year'].astype(int).astype(str) + '-' + 
        df_import['monthNumber'].astype(int).astype(str).str.zfill(2)
    )
    df_import.sort_values('date', inplace=True)
    df_import.set_index('date', inplace=True)

    # 4. Criar um DF com todos os meses no intervalo (para preencher meses ausentes com 0)
    start_date = '2019-01'
    end_date = df_import.index.max().strftime('%Y-%m')  # data mais recente
    all_months = pd.date_range(start=start_date, end=end_date, freq='MS')
    df_all_months = pd.DataFrame(index=all_months)

    df_import = df_all_months.join(df_import[['metricKG']]).fillna(0)

    # 5. Calcular a soma móvel de 12 meses
    df_import['soma_movel'] = _calcular_soma_movel(df_import, 'metricKG', 12)

    # 6. Filtrar para exibir a partir de 2019-12 até o fim
    filter_start_date = '2019-12'
    df_import_filtered = df_import.loc[filter_start_date:]

    # 7. Plotar o gráfico com matplotlib
    fig, ax = plt.subplots(figsize=(12, 6))
    df_import_filtered['soma_movel'].plot(
        kind='bar', color='steelblue', ax=ax, width=0.8
    )

    # Formatando o eixo Y (milhares com ponto)
    ax.get_yaxis().set_major_formatter(
        mticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.'))
    )

    # Adicionando listras horizontais
    ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=.25)

    # Formatando o eixo X
    ax.set_xticks(range(len(df_import_filtered)))
    ax.set_xticklabels(df_import_filtered.index.strftime('%Y-%m'), rotation=45, ha='right')

    ax.set_title(f'Importações Acumuladas nos Últimos 12 Meses (em KG) - NCM {ncm_str}')
    ax.set_xlabel('')
    ax.set_ylabel('Quantidade (KG)')

    # Adicionando a fonte no rodapé do gráfico
    plt.figtext(0.5, -0.05, "Fonte: Comex Stat/MDIC. Elaboração própria.", 
                ha="center", fontsize=8)

    plt.tight_layout()

    return fig  # Retorna o objeto Figure
