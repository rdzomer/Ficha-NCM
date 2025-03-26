# modulos/grafico_exportacoes_kg.py (COMPLETO)
import plotly.express as px  # Importe plotly.express
import pandas as pd          # Importe pandas
from .grafico_base import _gerar_grafico_base, _calcular_ticks_eixo_y  # Importe a função base

def gerar_grafico_exportacoes(df, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year):
    """Gera o gráfico de exportações (KG), usando a função base."""
    return _gerar_grafico_base(df, df_2024_parcial, 'Exportações', ncm_formatado, last_updated_month, last_updated_year, tipo_valor='KG')