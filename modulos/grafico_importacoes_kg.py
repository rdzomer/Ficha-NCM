import plotly.express as px  # Importe plotly.express
import pandas as pd          # Importe pandas
from .grafico_base import _gerar_grafico_base, _calcular_ticks_eixo_y  # Importe a função base

def gerar_grafico_importacoes(df, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year):
    """Gera o gráfico de importações (KG), usando a função base."""
    return _gerar_grafico_base(df, df_2024_parcial, 'Importações', ncm_formatado, last_updated_month, last_updated_year)
