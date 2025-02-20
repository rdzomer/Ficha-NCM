import pandas as pd

def processar_dados_export_import(dados_export, dados_import, last_updated_month):
    """ Processa os dados de exportação e importação e calcula métricas adicionais. """

    if not dados_export and not dados_import:
        return pd.DataFrame(), "Erro: Dados de exportação ou importação estão vazios."

    df_export = pd.DataFrame(dados_export) if dados_export else pd.DataFrame()
    df_import = pd.DataFrame(dados_import) if dados_import else pd.DataFrame()

    if not df_export.empty:
        df_export.rename(columns={'metricFOB': 'Exportações (FOB)', 'metricKG': 'Exportações (KG)'}, inplace=True)

    if not df_import.empty:
        df_import.rename(columns={
            'metricFOB': 'Importações (FOB)',
            'metricFreight': 'Importações (Frete USD)',
            'metricInsurance': 'Importações (Seguro USD)',
            'metricCIF': 'Importações (CIF USD)',
            'metricKG': 'Importações (KG)'
        }, inplace=True)

    if not df_export.empty and not df_import.empty:
        df_combined = pd.merge(df_export, df_import, on='year', how='outer')
    elif not df_export.empty:
        df_combined = df_export.copy()
        df_combined['Importações (FOB)'] = 0
        df_combined['Importações (KG)'] = 0
    elif not df_import.empty:
        df_combined = df_import.copy()
        df_combined['Exportações (FOB)'] = 0
        df_combined['Exportações (KG)'] = 0
    else:
        return pd.DataFrame(), "Erro: Nenhum dado válido para combinar."

    # 🔸 Convertendo colunas para valores numéricos
    colunas_numericas = ['Exportações (FOB)', 'Exportações (KG)', 'Importações (FOB)', 
                         'Importações (Frete USD)', 'Importações (Seguro USD)', 
                         'Importações (CIF USD)', 'Importações (KG)']
    
    for coluna in colunas_numericas:
        if coluna in df_combined.columns:
            df_combined[coluna] = pd.to_numeric(df_combined[coluna], errors='coerce').fillna(0)

    # 📊 Cálculo da Balança Comercial e dos Preços Médios
    df_combined['Balança Comercial (FOB)'] = df_combined['Exportações (FOB)'] - df_combined['Importações (FOB)']
    df_combined['Balança Comercial (KG)'] = df_combined['Exportações (KG)'] - df_combined['Importações (KG)']

    df_combined['Preço Médio Exportação (US$ FOB/Ton)'] = (
        df_combined['Exportações (FOB)'] / (df_combined['Exportações (KG)'] / 1000)
    ).replace([float('inf'), -float('inf')], 0)  # Evita divisão por zero

    df_combined['Preço Médio Importação (US$ FOB/Ton)'] = (
        df_combined['Importações (FOB)'] / (df_combined['Importações (KG)'] / 1000)
    ).replace([float('inf'), -float('inf')], 0)  # Evita divisão por zero

    df_combined.fillna(0, inplace=True)

    df_combined['year'] = df_combined['year'].astype(str)
    df_combined['year'] = df_combined['year'].replace('2025', f"2025 (Até mês {str(last_updated_month).zfill(2)}")

    return df_combined, None

def processar_dados_ano_anterior(dados_export, dados_import, last_updated_month):
    """ Processa os dados acumulados de 2024 até o último mês disponível para comparação com 2025. """

    if not dados_export and not dados_import:
        return pd.DataFrame(), "Erro: Nenhum dado foi encontrado para 2024."

    df_export = pd.DataFrame(dados_export) if dados_export else pd.DataFrame()
    df_import = pd.DataFrame(dados_import) if dados_import else pd.DataFrame()

    if not df_export.empty:
        df_export.rename(columns={'metricFOB': 'Exportações (FOB)', 'metricKG': 'Exportações (KG)'}, inplace=True)

    if not df_import.empty:
        df_import.rename(columns={
            'metricFOB': 'Importações (FOB)',
            'metricFreight': 'Importações (Frete USD)',
            'metricInsurance': 'Importações (Seguro USD)',
            'metricCIF': 'Importações (CIF USD)',
            'metricKG': 'Importações (KG)'
        }, inplace=True)

    if not df_export.empty and not df_import.empty:
        df_combined = pd.merge(df_export, df_import, on='year', how='outer')
    elif not df_export.empty:
        df_combined = df_export.copy()
        df_combined['Importações (FOB)'] = 0
        df_combined['Importações (KG)'] = 0
    elif not df_import.empty:
        df_combined = df_import.copy()
        df_combined['Exportações (FOB)'] = 0
        df_combined['Exportações (KG)'] = 0
    else:
        return pd.DataFrame(), "Erro: Nenhum dado válido para combinar."

    # 🔌 Conversão das colunas numéricas
    colunas_numericas = ['Exportações (FOB)', 'Exportações (KG)', 'Importações (FOB)', 
                        'Importações (Frete USD)', 'Importações (Seguro USD)', 
                        'Importações (CIF USD)', 'Importações (KG)']
    
    for coluna in colunas_numericas:
        if coluna in df_combined.columns:
            df_combined[coluna] = pd.to_numeric(df_combined[coluna], errors='coerce').fillna(0)

    df_combined['Balança Comercial (FOB)'] = df_combined['Exportações (FOB)'] - df_combined['Importações (FOB)']
    df_combined['Balança Comercial (KG)'] = df_combined['Exportações (KG)'] - df_combined['Importações (KG)']

    df_combined['Preço Médio Exportação (US$ FOB/Ton)'] = (
        df_combined['Exportações (FOB)'] / (df_combined['Exportações (KG)'] / 1000)
    ).replace([float('inf'), -float('inf')], 0)

    df_combined['Preço Médio Importação (US$ FOB/Ton)'] = (
        df_combined['Importações (FOB)'] / (df_combined['Importações (KG)'] / 1000)
    ).replace([float('inf'), -float('inf')], 0)

    df_combined.fillna(0, inplace=True)

    df_combined['year'] = df_combined['year'].astype(str)
    df_combined['year'] = df_combined['year'].replace('2024', f"2024 (Até mês {str(last_updated_month).zfill(2)})")

    return df_combined, None





