# -*- coding: utf-8 -*-
import pandas as pd
import logging
import re # Importado para formatar NCM

# Configuração básica de logging (se não configurado no app.py, pode ser útil aqui)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [PROCESSAMENTO] - %(message)s')

# Função auxiliar para formatar NCM (movida ou duplicada aqui para uso interno se necessário)
def formatar_ncm_8digitos(ncm_value):
    """Converte NCM de vários formatos para 8 dígitos (string), ou retorna vazio."""
    if pd.isna(ncm_value):
        return ""
    ncm_str = str(ncm_value).strip()
    ncm_digits = re.sub(r'\D', '', ncm_str)
    ncm_8 = ncm_digits[:8]
    return ncm_8 if len(ncm_8) == 8 else ""

def carregar_dados_excel(uploaded_file):
    """
    Lê um arquivo Excel, identifica abas relevantes (CGIM e Entidades),
    limpa e estrutura os dados.

    Retorna:
        dict: Dicionário com DataFrames ('NCMs-CGIM-DINTE' e 'Entidades') ou None em caso de erro.
    """
    if not uploaded_file:
        logging.error("Nenhum arquivo Excel fornecido para carregar.")
        return None

    try:
        # Lê todas as abas do Excel
        excel_data = pd.read_excel(uploaded_file, sheet_name=None)
        logging.info(f"Lendo {len(excel_data)} abas do Excel...")

        dados_estruturados = {
            "NCMs-CGIM-DINTE": pd.DataFrame(),
            "Entidades": pd.DataFrame()
        }
        abas_entidades_dfs = []
        nome_aba_cgim = None

        # Identifica a aba CGIM (procura por nome específico ou usa a primeira)
        if "NCMs-CGIM-DINTE" in excel_data:
            nome_aba_cgim = "NCMs-CGIM-DINTE"
        elif excel_data: # Se não achou pelo nome, pega a primeira aba
            nome_aba_cgim = list(excel_data.keys())[0]
            logging.warning(f"Aba 'NCMs-CGIM-DINTE' não encontrada. Usando a primeira aba '{nome_aba_cgim}' como aba CGIM.")
        else:
            logging.error("Arquivo Excel vazio ou sem abas.")
            return None # Retorna None se não houver abas

        # Processa cada aba
        for sheet_name, df in excel_data.items():
            logging.info(f"Processando aba: '{sheet_name}'")

            # Verifica se a aba está vazia
            if df.empty:
                logging.warning(f"Aba '{sheet_name}' está vazia.")
                continue

            # Garante que a coluna 'NCM' exista (essencial para ambas as abas)
            if 'NCM' not in df.columns:
                logging.warning(f"Coluna 'NCM' não encontrada na aba '{sheet_name}'. Pulando esta aba.")
                continue

            # Limpa e formata a coluna NCM para 8 dígitos
            df['NCM'] = df['NCM'].apply(formatar_ncm_8digitos)
            df = df.dropna(subset=['NCM']) # Remove linhas onde NCM ficou vazio após formatação
            df = df[df['NCM'] != ""] # Garante que não haja strings vazias

            # Se a aba ficou vazia após limpar NCMs, avisa e pula
            if df.empty:
                logging.warning(f"Aba '{sheet_name}' ficou vazia após limpar/filtrar NCMs para 8 dígitos.")
                continue

            # Processa a aba CGIM
            if sheet_name == nome_aba_cgim:
                dados_estruturados["NCMs-CGIM-DINTE"] = df
                logging.info(f"Aba CGIM identificada: '{sheet_name}'")

            # Processa abas de Entidades (todas as outras que têm NCM)
            else:
                df['NomeAbaEntidade'] = sheet_name # Adiciona o nome da aba como coluna
                abas_entidades_dfs.append(df)
                logging.info(f"Aba de entidade adicionada: '{sheet_name}'")

        # Concatena todas as abas de entidades em um único DataFrame
        if abas_entidades_dfs:
            dados_estruturados["Entidades"] = pd.concat(abas_entidades_dfs, ignore_index=True)

        # Verifica se a aba CGIM foi carregada
        if dados_estruturados["NCMs-CGIM-DINTE"].empty:
             logging.error(f"Aba CGIM ('{nome_aba_cgim}') não contém dados válidos de NCM após processamento.")
             # Pode retornar None ou o dicionário parcial dependendo do requisito
             # return None
             # Por enquanto, retorna o dicionário mesmo que CGIM esteja vazio, mas loga o erro.

        logging.info(f"Carregamento do Excel concluído. Aba CGIM: {'Sim' if not dados_estruturados['NCMs-CGIM-DINTE'].empty else 'Não'}. Abas de Entidades: {len(abas_entidades_dfs)}")
        return dados_estruturados

    except Exception as e:
        logging.error(f"Erro ao ler ou processar o arquivo Excel: {e}", exc_info=True)
        return None


def buscar_informacoes_ncm_completo(dados_excel_estruturados, ncm_8digitos):
    """
    Busca informações de um NCM específico na estrutura de dados carregada do Excel.

    Args:
        dados_excel_estruturados (dict): Dicionário retornado por carregar_dados_excel.
        ncm_8digitos (str): Código NCM com 8 dígitos.

    Returns:
        tuple: (pd.DataFrame, pd.DataFrame)
               - DataFrame com a linha correspondente da aba CGIM (ou vazio).
               - DataFrame com as linhas correspondentes das abas de Entidades (ou vazio).
    """
    df_ncm_result = pd.DataFrame()
    df_entidades_result = pd.DataFrame()

    if not isinstance(dados_excel_estruturados, dict) or not ncm_8digitos:
        logging.warning("Dados estruturados do Excel inválidos ou NCM não fornecido para busca.")
        return df_ncm_result, df_entidades_result

    logging.info(f"Buscando NCM '{ncm_8digitos}' na estrutura do Excel...")

    # Busca na aba CGIM
    df_cgim = dados_excel_estruturados.get("NCMs-CGIM-DINTE")
    if isinstance(df_cgim, pd.DataFrame) and not df_cgim.empty and 'NCM' in df_cgim.columns:
        df_ncm_result = df_cgim[df_cgim['NCM'] == ncm_8digitos].copy()
        logging.info(f"Busca na aba CGIM: {len(df_ncm_result)} registro(s) encontrado(s).")
    else:
        logging.warning("Aba CGIM não encontrada ou inválida na estrutura de dados.")

    # Busca nas Entidades
    df_entidades = dados_excel_estruturados.get("Entidades")
    if isinstance(df_entidades, pd.DataFrame) and not df_entidades.empty and 'NCM' in df_entidades.columns:
        df_entidades_result = df_entidades[df_entidades['NCM'] == ncm_8digitos].copy()
        # Log detalhado por aba de origem, se a coluna 'NomeAbaEntidade' existir
        if 'NomeAbaEntidade' in df_entidades_result.columns:
             logging.info(f"Buscando em {len(df_entidades['NomeAbaEntidade'].unique())} aba(s) de entidade...")
             for aba, count in df_entidades_result['NomeAbaEntidade'].value_counts().items():
                  logging.info(f"  -> Encontrado na aba '{aba}': {count} registro(s).")
        logging.info(f"Total de {len(df_entidades_result)} registro(s) de entidade(s) encontrado(s).")

    else:
        logging.info("Nenhuma aba de entidade encontrada ou inválida na estrutura de dados.")

    return df_ncm_result, df_entidades_result


# --- Funções de Processamento de Dados da API ---

def _converter_colunas_numericas(df, colunas):
    """Converte colunas especificadas para numérico, tratando erros."""
    for col in colunas:
        if col in df.columns:
            # errors='coerce' transforma o que não é número em NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            logging.warning(f"Tentativa de converter coluna numérica '{col}' que não existe no DataFrame.")
            # Adiciona a coluna como float com NAs para consistência
            df[col] = pd.NA
            df[col] = df[col].astype('Float64') # Usa tipo que suporta NA
    return df

def processar_dados_export_import(dados_export, dados_import, last_updated_month):
    """
    Processa dados históricos de exportação e importação, CONSOLIDA POR ANO,
    e calcula balança e preço médio anual.

    Retorna: (pd.DataFrame, str | None) DataFrame ANUAL e erro.
    """
    logging.info("Processando e agregando dados históricos (export/import) por ano...")
    df_final_anual = pd.DataFrame()
    error = None
    try:
        # 1. Converter listas para DataFrames ou criar vazios
        df_exp = pd.DataFrame(dados_export) if dados_export else pd.DataFrame()
        df_imp = pd.DataFrame(dados_import) if dados_import else pd.DataFrame()

        # 2. Garantir colunas essenciais e CONVERTER PARA NUMÉRICO
        colunas_metricas = ['metricFOB', 'metricKG']
        colunas_tempo = ['year', 'monthNumber']
        colunas_exp = colunas_tempo + colunas_metricas
        colunas_imp = colunas_tempo + colunas_metricas

        # Adiciona colunas faltantes e converte métricas para numérico
        for df, cols_esperadas, nome in [(df_exp, colunas_exp, 'Exportação'), (df_imp, colunas_imp, 'Importação')]:
            for col in cols_esperadas:
                if col not in df.columns:
                    df[col] = pd.NA # Adiciona como NA se não existir
                    logging.warning(f"Coluna '{col}' ausente nos dados de {nome}. Adicionada com NA.")
            # Converte métricas para numérico ANTES de qualquer operação
            df = _converter_colunas_numericas(df, colunas_metricas)
            # Converte ano/mês para Int64 que suporta NA
            for col_t in colunas_tempo:
                 if col_t in df.columns:
                      # errors='coerce' transforma não numéricos em NA
                      df[col_t] = pd.to_numeric(df[col_t], errors='coerce').astype('Int64')

        # 3. Renomear colunas ANTES do merge
        df_exp = df_exp.rename(columns={'metricFOB': 'Exportações (FOB)', 'metricKG': 'Exportações (KG)'})
        df_imp = df_imp.rename(columns={'metricFOB': 'Importações (FOB)', 'metricKG': 'Importações (KG)'})

        # 4. Merge dos dados mensais (garantindo que 'year' e 'monthNumber' existam e sejam tipos compatíveis)
        cols_merge = ['year', 'monthNumber']
        # Verifica se as colunas de merge existem em ambos e se os DFs não estão vazios
        if all(col in df_exp.columns for col in cols_merge) and not df_exp.empty and \
           all(col in df_imp.columns for col in cols_merge) and not df_imp.empty:
            try:
                df_mensal = pd.merge(
                    df_exp[cols_merge + ['Exportações (FOB)', 'Exportações (KG)']], # Seleciona colunas relevantes
                    df_imp[cols_merge + ['Importações (FOB)', 'Importações (KG)']], # Seleciona colunas relevantes
                    on=cols_merge,
                    how='outer' # Mantém todos os meses/anos de ambos
                )
                logging.info(f"Merge mensal realizado. {len(df_mensal)} linhas.")
            except Exception as merge_error:
                 logging.error(f"Erro durante o merge mensal: {merge_error}", exc_info=True)
                 error = f"Erro no merge: {merge_error}"
                 df_mensal = pd.DataFrame() # Define como vazio para evitar erros subsequentes
        # Fallback: Se um DF estiver vazio ou merge falhar, tenta usar o outro
        elif not df_exp.empty:
            df_mensal = df_exp[cols_merge + ['Exportações (FOB)', 'Exportações (KG)']].copy()
            # Adiciona colunas de importação com NA (serão preenchidas depois)
            df_mensal['Importações (FOB)'] = pd.NA
            df_mensal['Importações (KG)'] = pd.NA
            df_mensal = _converter_colunas_numericas(df_mensal, ['Importações (FOB)', 'Importações (KG)']) # Garante tipo numérico
            logging.warning("Dados de importação ausentes ou inválidos, usando apenas exportação para base mensal.")
        elif not df_imp.empty:
            df_mensal = df_imp[cols_merge + ['Importações (FOB)', 'Importações (KG)']].copy()
            # Adiciona colunas de exportação com NA
            df_mensal['Exportações (FOB)'] = pd.NA
            df_mensal['Exportações (KG)'] = pd.NA
            df_mensal = _converter_colunas_numericas(df_mensal, ['Exportações (FOB)', 'Exportações (KG)']) # Garante tipo numérico
            logging.warning("Dados de exportação ausentes ou inválidos, usando apenas importação para base mensal.")
        else:
            df_mensal = pd.DataFrame() # Ambos vazios
            logging.warning("Ambos DataFrames (export/import) estão vazios.")
            error = error or "Dados de exportação e importação vazios." # Mantém erro anterior se houver

        # 5. Preencher NaNs com 0 APÓS o merge e ANTES da agregação
        colunas_valores = ['Exportações (FOB)', 'Exportações (KG)', 'Importações (FOB)', 'Importações (KG)']
        if not df_mensal.empty:
            for col in colunas_valores:
                if col in df_mensal.columns:
                    # Garante que a coluna seja numérica antes de fillna
                    df_mensal[col] = pd.to_numeric(df_mensal[col], errors='coerce')
                    df_mensal[col] = df_mensal[col].fillna(0)
                else:
                     df_mensal[col] = 0 # Adiciona coluna com zeros se faltar
                     logging.warning(f"Coluna '{col}' não encontrada no DF mensal. Adicionada com zeros.")
        else:
             # Se df_mensal está vazio, cria um DF vazio com as colunas esperadas para evitar erros no groupby
             df_mensal = pd.DataFrame(columns=['year'] + colunas_valores)


        # 6. === AGREGAÇÃO POR ANO ===
        # Verifica se 'year' existe e se o DF não está vazio
        if 'year' in df_mensal.columns and not df_mensal.empty:
            # Remove linhas onde 'year' é NA antes de agrupar
            df_mensal_valid_years = df_mensal.dropna(subset=['year'])

            if not df_mensal_valid_years.empty:
                # Define as colunas a serem somadas (APENAS as que existem e são numéricas)
                colunas_para_somar = [col for col in colunas_valores if col in df_mensal_valid_years.columns and pd.api.types.is_numeric_dtype(df_mensal_valid_years[col])]

                if not colunas_para_somar:
                     error_agg = "Nenhuma coluna numérica de valor encontrada para agregação anual."
                     logging.error(error_agg)
                     error = error or error_agg # Combina erros
                     df_final_anual = pd.DataFrame() # Retorna vazio
                else:
                    # Agrupa por ano e soma as colunas numéricas
                    df_final_anual = df_mensal_valid_years.groupby('year')[colunas_para_somar].sum().reset_index()
                    logging.info(f"Dados agregados por ano. {len(df_final_anual)} anos encontrados.")

                    # 7. Calcular Balança Comercial e Preço Médio ANUAL (APÓS agregação)
                    # Garante que as colunas existam e sejam numéricas antes do cálculo
                    if 'Exportações (FOB)' in df_final_anual.columns and 'Importações (FOB)' in df_final_anual.columns:
                        df_final_anual['Balança Comercial (FOB)'] = df_final_anual['Exportações (FOB)'] - df_final_anual['Importações (FOB)']
                    if 'Exportações (KG)' in df_final_anual.columns and 'Importações (KG)' in df_final_anual.columns:
                        df_final_anual['Balança Comercial (KG)'] = df_final_anual['Exportações (KG)'] - df_final_anual['Importações (KG)']

                    # Calcula Preço Médio com segurança (divisão por zero)
                    if 'Exportações (FOB)' in df_final_anual.columns and 'Exportações (KG)' in df_final_anual.columns:
                        df_final_anual['Preço Médio Exportação (US$ FOB/KG)'] = df_final_anual.apply(
                            lambda row: (row['Exportações (FOB)'] / row['Exportações (KG)']) if pd.notna(row['Exportações (KG)']) and row['Exportações (KG)'] != 0 else 0, axis=1
                        )
                    if 'Importações (FOB)' in df_final_anual.columns and 'Importações (KG)' in df_final_anual.columns:
                        df_final_anual['Preço Médio Importação (US$ FOB/KG)'] = df_final_anual.apply(
                            lambda row: (row['Importações (FOB)'] / row['Importações (KG)']) if pd.notna(row['Importações (KG)']) and row['Importações (KG)'] != 0 else 0, axis=1
                        )

                    # Ordena por ano
                    df_final_anual = df_final_anual.sort_values(by='year').reset_index(drop=True)
            else:
                 error_agg = "DataFrame mensal não contém anos válidos para agregação."
                 logging.error(error_agg)
                 error = error or error_agg
                 df_final_anual = pd.DataFrame()

        else:
            # Se 'year' não existe ou df_mensal estava vazio desde o início
            error_agg = "Coluna 'year' não encontrada ou DataFrame mensal vazio, não foi possível agregar por ano."
            logging.error(error_agg)
            error = error or error_agg # Combina erros
            df_final_anual = pd.DataFrame()

    except Exception as e:
        error_proc = f"Erro inesperado ao processar dados históricos: {e}"
        logging.error(error_proc, exc_info=True)
        error = error or error_proc # Combina erros
        df_final_anual = pd.DataFrame() # Garante retorno de DF vazio

    # Garante que a coluna 'year' seja do tipo Int64 se existir
    if 'year' in df_final_anual.columns:
        df_final_anual['year'] = df_final_anual['year'].astype('Int64')

    return df_final_anual, error


def _processar_dados_parciais(dados_export, dados_import, ano, last_updated_month):
    """
    Processa dados parciais de exportação e importação para um ano específico,
    retornando um DataFrame de UMA LINHA com os totais do período.

    Retorna: (pd.DataFrame, str | None) DataFrame de uma linha e erro.
    """
    logging.info(f"Processando dados parciais para {ano}...")
    df_agg = pd.DataFrame()
    error = None
    try:
        df_exp = pd.DataFrame(dados_export) if dados_export else pd.DataFrame()
        df_imp = pd.DataFrame(dados_import) if dados_import else pd.DataFrame()

        colunas_metricas = ['metricFOB', 'metricKG']

        # Garante colunas e converte para numérico
        df_exp = _converter_colunas_numericas(df_exp, colunas_metricas)
        df_imp = _converter_colunas_numericas(df_imp, colunas_metricas)

        # Renomeia
        df_exp = df_exp.rename(columns={'metricFOB': 'Exportações (FOB)', 'metricKG': 'Exportações (KG)'})
        df_imp = df_imp.rename(columns={'metricFOB': 'Importações (FOB)', 'metricKG': 'Importações (KG)'})

        # Seleciona apenas as colunas de valor existentes para somar
        exp_cols_sum = [col for col in ['Exportações (FOB)', 'Exportações (KG)'] if col in df_exp.columns]
        imp_cols_sum = [col for col in ['Importações (FOB)', 'Importações (KG)'] if col in df_imp.columns]

        # Soma os valores para o período (já devem ser numéricos ou NA)
        # .sum() ignora NA por padrão
        exp_totals = df_exp[exp_cols_sum].sum()
        imp_totals = df_imp[imp_cols_sum].sum()

        # === CORREÇÃO ValueError: Cria DataFrame de uma linha diretamente ===
        # Concatena as Series de totais
        all_totals = pd.concat([exp_totals, imp_totals])
        # Converte a Series resultante em um DataFrame de uma linha
        df_agg = pd.DataFrame([all_totals]) # Chave: [all_totals] cria lista com um item

        # Adiciona coluna 'Ano'
        df_agg['Ano'] = ano
        logging.info(f"Dados parciais para {ano} agregados com sucesso.")

        # Calcula Balança e Preço Médio para esta única linha (com segurança)
        # Preenche NaNs com 0 APÓS a agregação para cálculos
        df_agg = df_agg.fillna(0)

        if 'Exportações (FOB)' in df_agg.columns and 'Importações (FOB)' in df_agg.columns:
             df_agg['Balança Comercial (FOB)'] = df_agg['Exportações (FOB)'] - df_agg['Importações (FOB)']
        if 'Exportações (KG)' in df_agg.columns and 'Importações (KG)' in df_agg.columns:
             df_agg['Balança Comercial (KG)'] = df_agg['Exportações (KG)'] - df_agg['Importações (KG)']

        if 'Exportações (FOB)' in df_agg.columns and 'Exportações (KG)' in df_agg.columns:
             df_agg['Preço Médio Exportação (US$ FOB/KG)'] = df_agg.apply(
                 lambda row: (row['Exportações (FOB)'] / row['Exportações (KG)']) if row['Exportações (KG)'] != 0 else 0, axis=1
             )
        if 'Importações (FOB)' in df_agg.columns and 'Importações (KG)' in df_agg.columns:
             df_agg['Preço Médio Importação (US$ FOB/KG)'] = df_agg.apply(
                 lambda row: (row['Importações (FOB)'] / row['Importações (KG)']) if row['Importações (KG)'] != 0 else 0, axis=1
             )

    except Exception as e:
        error = f"Erro ao processar dados parciais para {ano}: {e}"
        logging.error(error, exc_info=True)
        # Retorna DF vazio com colunas esperadas para consistência
        cols_esperadas = ['Exportações (FOB)', 'Exportações (KG)', 'Importações (FOB)', 'Importações (KG)', 'Ano',
                          'Balança Comercial (FOB)', 'Balança Comercial (KG)',
                          'Preço Médio Exportação (US$ FOB/KG)', 'Preço Médio Importação (US$ FOB/KG)']
        df_agg = pd.DataFrame(columns=cols_esperadas)

    # Garante que 'Ano' seja Int64
    if 'Ano' in df_agg.columns:
        df_agg['Ano'] = df_agg['Ano'].astype('Int64')

    return df_agg, error


def processar_dados_ano_anterior(dados_export, dados_import, last_updated_month):
    """Processa dados parciais do ano anterior."""
    # TODO: Obter o ano dinamicamente a partir da data de atualização da API
    # Exemplo: Se a API está em Fev/2025, o ano anterior é 2024.
    ano_anterior = 2024 # Temporariamente fixo
    return _processar_dados_parciais(dados_export, dados_import, ano_anterior, last_updated_month)

def processar_dados_ano_atual(dados_export, dados_import, last_updated_month):
    """Processa dados parciais do ano atual."""
    # TODO: Obter o ano dinamicamente a partir da data de atualização da API
    # Exemplo: Se a API está em Fev/2025, o ano atual é 2025.
    ano_atual = 2025 # Temporariamente fixo
    return _processar_dados_parciais(dados_export, dados_import, ano_atual, last_updated_month)

