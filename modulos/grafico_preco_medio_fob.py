import plotly.graph_objects as go
import pandas as pd
import numpy as np

def _calcular_ticks_eixo_y(max_value):
    """Calcula intervalos seguros para diferentes faixas de valores do eixo Y."""
    if max_value == 0:
        return [0, 0.5], ['0.00', '0.50']
    step = max_value / 5
    ticks = [i * step for i in range(6)]
    return ticks, [f"{tick:.4f}" for tick in ticks]

def gerar_grafico_preco_medio(df_2025, df_2024_parcial, ncm_formatado, last_updated_month):
    """
    Gera o gráfico de Preço Médio (US$ FOB/KG) para os anos de 2025 e dados parciais de 2024.

    Parâmetros:
      df_2025         : DataFrame com dados completos de 2025.
      df_2024_parcial : DataFrame com dados parciais de 2024.
      ncm_formatado   : String do NCM formatado utilizada no título do gráfico.
      last_updated_month : Mês da última atualização (para exibir no rótulo de 2024 parcial).

    Retorna:
      Uma figura Plotly.
    """
    if df_2025 is None or df_2025.empty:
        return go.Figure()

    try:
        # --- Cópia dos DataFrames para evitar alterar os originais ---
        df_2025 = df_2025.copy()

        # Se os valores estiverem como string (ex.: "1.234,56"), descomente as linhas abaixo:
        # df_2025['Exportações (FOB)'] = df_2025['Exportações (FOB)'].apply(lambda x: float(str(x).replace('.', '').replace(',', '.')))
        # df_2025['Exportações (KG)']  = df_2025['Exportações (KG)'].apply(lambda x: float(str(x).replace('.', '').replace(',', '')))
        # df_2025['Importações (FOB)'] = df_2025['Importações (FOB)'].apply(lambda x: float(str(x).replace('.', '').replace(',', '.')))
        # df_2025['Importações (KG)']  = df_2025['Importações (KG)'].apply(lambda x: float(str(x).replace('.', '').replace(',', '')))

        # --- Cálculo do preço médio para 2025 ---
        df_2025['Preco Export'] = df_2025['Exportações (FOB)'] / df_2025['Exportações (KG)']
        df_2025['Preco Import'] = df_2025['Importações (FOB)'] / df_2025['Importações (KG)']

        # --- Processamento do DataFrame parcial de 2024 ---
        df_2024_proc = pd.DataFrame()
        if df_2024_parcial is not None and not df_2024_parcial.empty:
            df_2024_proc = df_2024_parcial.copy()
            # Se necessário, converta os valores como acima para float antes do cálculo
            df_2024_proc['Preco Export'] = df_2024_proc['Exportações (FOB)'] / df_2024_proc['Exportações (KG)']
            df_2024_proc['Preco Import'] = df_2024_proc['Importações (FOB)'] / df_2024_proc['Importações (KG)']
            df_2024_proc['year'] = f"2024 (Até mês {str(last_updated_month).zfill(2)})"

        # --- Combinação dos dados ---
        # Se a coluna "year" não existir em df_2025, adicione-a:
        if 'year' not in df_2025.columns:
            df_2025['year'] = '2025'
        df_plot = pd.concat([
            df_2025[['year', 'Preco Export', 'Preco Import']],
            df_2024_proc[['year', 'Preco Export', 'Preco Import']]
        ], ignore_index=True)

        # Ordenação: trata o rótulo parcial de 2024 de forma especial
        df_plot['ano_num'] = df_plot['year'].apply(
            lambda x: 2026 if '2024 (Até' in str(x)
                      else (2025 if '2025' in str(x)
                      else int(str(x)[:4]))
        )
        df_plot = df_plot.sort_values('ano_num')

        # --- Criação do gráfico ---
        fig = go.Figure()
        for serie, cor, nome in [('Preco Export', 'blue', 'Exportação'),
                                 ('Preco Import', 'red', 'Importação')]:
            fig.add_trace(go.Scatter(
                x=df_plot['year'],
                y=df_plot[serie],
                name=nome,
                mode='lines+markers',
                line=dict(color=cor),
                marker=dict(size=8)
            ))

        fig.update_layout(
            title=f'Preço Médio - NCM {ncm_formatado}',
            xaxis_title='Ano',
            yaxis_title='US$ FOB/KG',
            xaxis=dict(type='category', tickangle=-45),
            legend=dict(orientation="h", y=1.1),
            height=500
        )
        return fig

    except Exception as e:
        print(f"Erro na geração do gráfico: {str(e)}")
        return go.Figure()




