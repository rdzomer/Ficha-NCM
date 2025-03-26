# -*- coding: utf-8 -*-
import pandas as pd
import plotly.graph_objects as go
import logging

# Configuração básica de logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [GRAF_PRECO_MEDIO] - %(message)s')

def gerar_grafico_preco_medio(df_hist_anual, df_2024_parcial, ncm_formatado, last_updated_month):
    """
    Gera um gráfico de linhas comparando o preço médio anual (histórico)
    e, opcionalmente, o preço médio parcial do ano anterior.

    Args:
        df_hist_anual (pd.DataFrame): DataFrame com dados históricos ANUAIS.
                                      Deve conter 'Ano', 'Preço Médio Exportação (US$ FOB/KG)',
                                      'Preço Médio Importação (US$ FOB/KG)'.
        df_2024_parcial (pd.DataFrame): DataFrame com dados parciais de 2024 (1 linha).
                                        Pode conter as mesmas colunas de preço médio.
        ncm_formatado (str): String do NCM formatado para o título.
        last_updated_month (int): Mês da última atualização (para info no título, se necessário).

    Returns:
        plotly.graph_objects.Figure: Figura do Plotly ou uma figura vazia em caso de erro.
    """
    fig = go.Figure()
    logging.info(f"Gerando gráfico de preço médio para NCM {ncm_formatado}")

    try:
        # --- Validação e Preparação dos Dados ---
        df_hist = pd.DataFrame()
        df_parcial = pd.DataFrame()

        # Valida e copia histórico anual
        if isinstance(df_hist_anual, pd.DataFrame) and not df_hist_anual.empty:
            df_hist = df_hist_anual.copy()
            # Colunas esperadas no histórico
            cols_hist_esperadas = ['Ano', 'Preço Médio Exportação (US$ FOB/KG)', 'Preço Médio Importação (US$ FOB/KG)']
            for col in cols_hist_esperadas:
                if col not in df_hist.columns:
                    logging.warning(f"Coluna histórica '{col}' ausente para gráfico de preço médio.")
                    df_hist[col] = pd.NA # Adiciona como NA
                # Garante conversão numérica
                df_hist[col] = pd.to_numeric(df_hist[col], errors='coerce')
            df_hist = df_hist.dropna(subset=['Ano']) # Remove anos inválidos
        else:
            logging.warning("DataFrame histórico anual inválido ou vazio para gráfico de preço médio.")

        # Valida e copia parcial 2024
        if isinstance(df_2024_parcial, pd.DataFrame) and not df_2024_parcial.empty:
            df_parcial = df_2024_parcial.copy()
            # Colunas esperadas no parcial (podem ou não existir)
            cols_parcial_esperadas = ['Ano', 'Preço Médio Exportação (US$ FOB/KG)', 'Preço Médio Importação (US$ FOB/KG)']
            for col in cols_parcial_esperadas:
                 if col not in df_parcial.columns:
                      # Não é um erro grave se não existir no parcial
                      df_parcial[col] = pd.NA
                 # Garante conversão numérica
                 df_parcial[col] = pd.to_numeric(df_parcial[col], errors='coerce')
            df_parcial = df_parcial.dropna(subset=['Ano'])
        else:
            logging.info("DataFrame parcial 2024 inválido ou vazio, não será plotado no gráfico de preço médio.")


        # --- Adição dos Traces ---
        plotou_algo = False

        # Plotar histórico de exportação
        if not df_hist.empty and 'Ano' in df_hist.columns and 'Preço Médio Exportação (US$ FOB/KG)' in df_hist.columns and df_hist['Preço Médio Exportação (US$ FOB/KG)'].notna().any():
            fig.add_trace(go.Scatter(
                x=df_hist['Ano'],
                y=df_hist['Preço Médio Exportação (US$ FOB/KG)'],
                mode='lines+markers',
                name='Preço Médio Exp (Anual)',
                line=dict(color='royalblue', width=2),
                marker=dict(color='royalblue', size=6)
            ))
            plotou_algo = True

        # Plotar histórico de importação
        if not df_hist.empty and 'Ano' in df_hist.columns and 'Preço Médio Importação (US$ FOB/KG)' in df_hist.columns and df_hist['Preço Médio Importação (US$ FOB/KG)'].notna().any():
            fig.add_trace(go.Scatter(
                x=df_hist['Ano'],
                y=df_hist['Preço Médio Importação (US$ FOB/KG)'],
                mode='lines+markers',
                name='Preço Médio Imp (Anual)',
                line=dict(color='firebrick', width=2),
                marker=dict(color='firebrick', size=6)
            ))
            plotou_algo = True

        # Adicionar pontos parciais (ex: 2024) se existirem e forem válidos
        # (Pode ser útil para comparar o valor parcial com a linha histórica)
        # Exemplo para exportação 2024:
        if not df_parcial.empty and 'Ano' in df_parcial.columns and 'Preço Médio Exportação (US$ FOB/KG)' in df_parcial.columns and df_parcial['Preço Médio Exportação (US$ FOB/KG)'].notna().iloc[0]:
             fig.add_trace(go.Scatter(
                  x=df_parcial['Ano'],
                  y=df_parcial['Preço Médio Exportação (US$ FOB/KG)'],
                  mode='markers',
                  name=f'Preço Médio Exp ({df_parcial["Ano"].iloc[0]} Parcial)',
                  marker=dict(color='lightblue', size=10, symbol='star', line=dict(color='black', width=1))
             ))
             # plotou_algo = True # Não necessariamente indica que o gráfico principal foi plotado

        # Exemplo para importação 2024:
        if not df_parcial.empty and 'Ano' in df_parcial.columns and 'Preço Médio Importação (US$ FOB/KG)' in df_parcial.columns and df_parcial['Preço Médio Importação (US$ FOB/KG)'].notna().iloc[0]:
             fig.add_trace(go.Scatter(
                  x=df_parcial['Ano'],
                  y=df_parcial['Preço Médio Importação (US$ FOB/KG)'],
                  mode='markers',
                  name=f'Preço Médio Imp ({df_parcial["Ano"].iloc[0]} Parcial)',
                  marker=dict(color='lightcoral', size=10, symbol='star', line=dict(color='black', width=1))
             ))
             # plotou_algo = True


        # --- Layout e Finalização ---
        if plotou_algo:
            fig.update_layout(
                title=f'Preço Médio Anual (US$ FOB/KG) - NCM {ncm_formatado}',
                xaxis_title='Ano',
                yaxis_title='Preço Médio (US$ FOB/KG)',
                xaxis=dict(type='category'), # Trata anos como categorias se houver saltos
                yaxis=dict(tickformat="$.2f"), # Formata eixo Y como dólar
                hovermode="x unified",
                legend_title_text='Legenda'
            )
        else:
            # Se nada foi plotado, exibe mensagem no gráfico
            fig.update_layout(
                 title=f'Preço Médio Anual (US$ FOB/KG) - NCM {ncm_formatado}',
                 xaxis=dict(visible=False),
                 yaxis=dict(visible=False),
                 annotations=[dict(text="Dados insuficientes para gerar o gráfico de preço médio.",
                                   xref="paper", yref="paper", showarrow=False, font=dict(size=14))]
            )
            logging.warning(f"Nenhum dado válido encontrado para plotar o gráfico de preço médio (NCM: {ncm_formatado}).")

        return fig

    except Exception as e:
        logging.error(f"Erro inesperado na geração do gráfico de preço médio: {e}", exc_info=True)
        # Retorna uma figura vazia com mensagem de erro
        return go.Figure().update_layout(
            title=f"Erro ao Gerar Gráfico de Preço Médio - NCM {ncm_formatado}",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text=f"Erro: {e}", xref="paper", yref="paper", showarrow=False, font=dict(size=12))]
        )





