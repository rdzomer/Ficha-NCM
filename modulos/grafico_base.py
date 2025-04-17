import plotly.express as px
import pandas as pd
import numpy as np  # <--- IMPORTE O NUMPY!
from babel.numbers import format_decimal

def _calcular_ticks_eixo_y(max_valor):
    """
    Calcula os ticks (valores e rótulos) para o eixo Y, de forma dinâmica.
    """
    if max_valor <= 0:
        return [0], ['0'], 1

    espacamento = max_valor * 0.1
    ordem_grandeza = 10 ** int(np.floor(np.log10(espacamento)))
    espacamento_arredondado = round(espacamento / ordem_grandeza) * ordem_grandeza

    if espacamento_arredondado * 2 > max_valor:
        espacamento_arredondado /= 2
    elif espacamento_arredondado * 6 < max_valor:
        espacamento_arredondado *= 2

    espacamento_arredondado = max(espacamento_arredondado, 1)
    tickvals = list(range(0, int(max_valor) + int(espacamento_arredondado), int(espacamento_arredondado)))
    ticktext = [format_decimal(val, locale='pt_BR') for val in tickvals]

    return tickvals, ticktext, espacamento_arredondado

def _gerar_grafico_base(df, df_2024_parcial, tipo_dado, ncm_formatado, last_updated_month, last_updated_year, tipo_valor='KG'):
    """
    Gera um gráfico de barras, agora com escala dinâmica do eixo Y.
    """
    if df.empty:
        return px.bar()

    df_plot = df.copy()
    # Remover espaços em branco dos nomes das colunas (para evitar KeyErrors)
    df_plot.columns = df_plot.columns.str.strip()

    # --- Preparação dos dados ---
    df_plot['year'] = df_plot['year'].astype(str).str.replace(r' \(Até mês \d{2}\)', '', regex=True)
    anos_validos = [str(ano) for ano in range(2010, 2026)]
    df_plot = df_plot[df_plot['year'].isin(anos_validos)]
    coluna_valor = f'{tipo_dado} ({tipo_valor})'
    df_plot[coluna_valor] = pd.to_numeric(df_plot[coluna_valor], errors='coerce').fillna(0)

    # --- Adicionar dados de 2024 Parcial ---
    if df_2024_parcial is not None and not df_2024_parcial.empty:
        df_2024_parcial = df_2024_parcial.copy()
        df_2024_parcial['year'] = f'2024 (Até mês {str(last_updated_month).zfill(2)})'
        df_2024_parcial[coluna_valor] = pd.to_numeric(df_2024_parcial[coluna_valor], errors='coerce').fillna(0)
        df_plot = pd.concat([df_plot, df_2024_parcial])

    # --- Configuração do gráfico ---
    df_plot['Cor'] = df_plot['year'].apply(
        lambda x: 'midnightblue' if x.startswith('2025') else
        ('darkorange' if x.startswith('2024 (Até') else 'steelblue')
    )

    fig = px.bar(df_plot, x='year', y=coluna_valor,
                 color='Cor',
                 color_discrete_map={'steelblue': 'steelblue', 'midnightblue': 'midnightblue', 'darkorange': 'darkorange'},
                 title=f'{tipo_dado} ({tipo_valor}) da NCM {ncm_formatado}, 2010-2025',
                 labels={'year': 'Ano', coluna_valor: f'{tipo_dado} ({tipo_valor})'})

    fig.update_layout(
        bargap=0.15,
        xaxis_title='Ano',
        yaxis_title=f'{tipo_dado} ({tipo_valor})',
        showlegend=False
    )

    fig.update_xaxes(
        tickmode='array',
        tickvals=df_plot['year'].unique(),
        tickangle=45,
        type='category'
    )

    # --- Escala Dinâmica do Eixo Y ---
    max_y = df_plot[coluna_valor].max()
    tickvals, ticktext, dtick = _calcular_ticks_eixo_y(max_y)
    fig.update_yaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext,
        dtick=dtick
    )

    return fig





