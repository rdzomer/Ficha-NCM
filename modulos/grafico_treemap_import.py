import plotly.express as px
import pandas as pd

def gerar_treemap_importacoes_2024(df_import_2024_country, ncm_code, ncm_str):
    """
    Gera o Treemap de Importações 2024 (US$ FOB), retornando um objeto Figure.
    
    Parâmetros:
      - df_import_2024_country: DataFrame com as colunas ['country', 'metricFOB'].
      - ncm_code: Código NCM (string).
      - ncm_str: String formatada do NCM para exibição no título.
    
    Retorna:
      - fig_import: Objeto Figure do Plotly contendo o Treemap.
    """
    # Agregar por país
    df_agg = df_import_2024_country.groupby('country', as_index=False)['metricFOB'].sum()
    
    # Converter para numérico
    df_agg['metricFOB'] = pd.to_numeric(df_agg['metricFOB'], errors='coerce').fillna(0)
    
    # Representatividade
    total_import_fob = df_agg['metricFOB'].sum()
    df_agg['Representatividade (%)'] = (df_agg['metricFOB'] / total_import_fob) * 100

    # Gerar treemap
    fig_import = px.treemap(
        df_agg, 
        path=['country'], 
        values='metricFOB',
        custom_data=['Representatividade (%)'],
        title=f'Origem das Importações 2024 (US$ FOB) - {ncm_str}'
    )
    
    # Ajustar dimensões (exemplo de forma quadrada)
    fig_import.update_layout(
    margin=dict(t=40, l=10, r=10, b=40),
    width=600,
    height=600
)
    
    # Personalizar texto e hover
    fig_import.update_traces(
        # Texto interno do treemap
        textinfo='label+value',
        texttemplate='%{label}<br>US$ %{value:,.2f} (%{customdata[0]:.2f}%)',
        textfont_size=18,
        
        # Tooltip personalizado (hover)
        hovertemplate=(
            '<b>%{label}</b><br>' +                # Nome do país
            'US$ %{value:,.2f} ' +                # Valor formatado
            '(%{customdata[0]:.2f}%)<extra></extra>'  
            # Se não quiser a representatividade no tooltip,
            # remova " (%{customdata[0]:.2f}%)" 
            # e deixe algo como '<b>%{label}</b><br>US$ %{value:,.2f}<extra></extra>'
        )
    )
    
    return fig_import









