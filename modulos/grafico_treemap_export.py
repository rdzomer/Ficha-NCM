import plotly.express as px
import pandas as pd

def gerar_treemap_exportacoes_2024(df_export_2024_country, ncm_code, ncm_str):
    """
    Gera o Treemap de Exportações 2024 (US$ FOB), retornando um objeto Figure.
    
    Parâmetros:
      - df_export_2024_country: DataFrame com as colunas ['country', 'metricFOB'].
      - ncm_code: Código NCM (string).
      - ncm_str: String formatada do NCM para exibição no título.
    
    Retorna:
      - fig_export: Objeto Figure do Plotly contendo o Treemap.
    """

    # 1. Agregar por país para somar o valor total de metricFOB
    df_agg = df_export_2024_country.groupby('country', as_index=False)['metricFOB'].sum()
    
    # 2. Converter metricFOB para numérico (caso esteja como string)
    df_agg['metricFOB'] = pd.to_numeric(df_agg['metricFOB'], errors='coerce').fillna(0)
    
    # 3. Calcular a representatividade
    total_export_fob = df_agg['metricFOB'].sum()
    df_agg['Representatividade (%)'] = (df_agg['metricFOB'] / total_export_fob) * 100

    # 4. Gerar o treemap
    fig_export = px.treemap(
        df_agg,
        path=['country'],
        values='metricFOB',
        custom_data=['Representatividade (%)'],
        title=f'Destino das Exportações 2024 (US$ FOB) - {ncm_str}'
    )
    
    # 5. Ajustar dimensões (exemplo: 700×600 para forma mais quadrada)
    fig_export.update_layout(
        margin=dict(t=40, l=10, r=10, b=40),
        width=700,
        height=600
    )
    
    # 6. Personalizar o texto interno e o tooltip (hover)
    fig_export.update_traces(
        textinfo='label+value',
        texttemplate='%{label}<br>US$ %{value:,.2f} (%{customdata[0]:.2f}%)',
        textfont_size=18,
        hovertemplate=(
            '<b>%{label}</b><br>' +                # Nome do país
            'US$ %{value:,.2f} ' +                # Valor formatado
            '(%{customdata[0]:.2f}%)<extra></extra>'
            # Remova "(%{customdata[0]:.2f}%)" se não quiser mostrar representatividade
        )
    )
    
    return fig_export

