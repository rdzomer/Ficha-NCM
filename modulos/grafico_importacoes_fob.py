# modulos/grafico_importacoes_fob.py
from modulos.grafico_base import _gerar_grafico_base

def gerar_grafico_importacoes_fob(df, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year):
    """Gera o gráfico de importações (FOB)."""
    return _gerar_grafico_base(df, df_2024_parcial, 'Importações', ncm_formatado, last_updated_month, last_updated_year, tipo_valor='FOB')

