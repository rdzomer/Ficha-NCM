# -*- coding: utf-8 -*-
import streamlit as st
st.set_page_config(page_title="Análise de Comércio Exterior", layout="wide")

import pandas as pd
from io import BytesIO
from babel.numbers import format_decimal
import re
from PyPDF2 import PdfReader
import logging
import plotly.graph_objects as go
import requests

# ====== Importações dos módulos existentes ======
try:
    from modulos.api_comex import (
        obter_data_ultima_atualizacao,
        obter_descricao_ncm,
        obter_dados_comerciais,
        obter_dados_comerciais_ano_anterior,
        obter_dados_comerciais_ano_atual,
        obter_dados_2024_por_pais,
        obter_dados_2024_por_pais_export
    )
    import modulos.processamento as proc
    import modulos.grafico_importacoes_kg as graf_kg
    import modulos.grafico_exportacoes_kg as graf_exp
    import modulos.grafico_importacoes_fob as graf_fob
    import modulos.grafico_exportacoes_fob as graf_exp_fob
    import modulos.grafico_preco_medio_fob as graf_preco_medio
    import modulos.resumo_tabelas as resumo_tabelas  # Função exibir_resumos precisa aceitar args
    from modulos.grafico_treemap_import import gerar_treemap_importacoes_2024
    from modulos.grafico_treemap_export import gerar_treemap_exportacoes_2024
    from modulos.grafico_importacoes_12meses import gerar_grafico_importacoes_12meses  # Verificar retorno
except ImportError as e:
    st.error(f"Erro fatal ao importar módulos: {e}. Verifique se os arquivos existem nos caminhos corretos ('modulos/...') e se não há erros de sintaxe neles.")
    logging.critical(f"Erro de importação: {e}", exc_info=True)
    st.stop()  # Interrompe a execução se módulos essenciais faltarem

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [APP] - %(message)s')

# ---- Barra Superior com Botões ----
st.markdown(
    """
    <style>
    .top-bar {
        background-color: #002f6c; /* Cor de fundo (azul escuro) */
        padding: 10px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px; /* Espaço após a barra */
    }
    .top-bar .title {
        font-size: 1.25rem;
        font-weight: bold;
        color: #ffffff; /* Cor do texto do título (branco) */
    }
    .top-bar .button-container {
        display: flex;
        gap: 10px; /* Espaço entre os botões */
    }
    .top-bar .button-link {
        text-decoration: none;
        background-color: #00c9c8; /* Cor do botão (teal) */
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 0.9rem;
        transition: background-color 0.3s ease;
    }
    .top-bar .button-link:hover {
        background-color: #009b9a; /* Cor do botão ao passar o mouse */
    }
    </style>
    <div class="top-bar">
        <div class="title">DASHBOARD CGIM</div>
        <div class="button-container">
            <a class="button-link" href="https://ncm-dashboard.shinyapps.io/registro-prompts/" target="_blank">
                Registro de Prompts de IA
            </a>
            <a class="button-link" href="https://exemplo.com/depreciacao-acelerada" target="_blank">
                Depreciação Acelerada
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Carrega a Planilha Excel Automaticamente do GitHub ----
excel_url = "https://github.com/rdzomer/Ficha-NCM/raw/refs/heads/main/20241011_NCMs-CGIM-DINTE.xlsx"
try:
    response = requests.get(excel_url)
    response.raise_for_status()  # Levanta erro se a resposta não for 200
    excel_bytes = BytesIO(response.content)
    st.session_state.df_excel = proc.carregar_dados_excel(excel_bytes)
    logging.info("Planilha Excel carregada com sucesso a partir do GitHub.")
except Exception as e:
    st.error("Erro ao carregar a planilha Excel do GitHub: " + str(e))
    logging.error("Erro ao carregar a planilha Excel do GitHub: " + str(e), exc_info=True)

# ------------------------
# FUNÇÕES AUXILIARES
# ------------------------

def formatar_numero(valor):
    """Formata número para o padrão brasileiro, tratando erros."""
    if pd.isna(valor):
        return ""  # Retorna string vazia para NaN ou None
    try:
        return format_decimal(float(valor), format="#,##0.##", locale='pt_BR')
    except (ValueError, TypeError):
        return str(valor)

def criar_dataframe_resumido(df):
    """Cria um DataFrame com colunas específicas para resumo."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        logging.warning("criar_dataframe_resumido recebeu DataFrame inválido ou vazio.")
        return pd.DataFrame()
    colunas_resumo_esperadas = ['Ano', 'Exportações (FOB)', 'Exportações (KG)',
                                'Importações (FOB)', 'Importações (KG)',
                                'Balança Comercial (FOB)', 'Balança Comercial (KG)']
    colunas_existentes_no_df = [col for col in colunas_resumo_esperadas if col in df.columns]
    if not colunas_existentes_no_df or 'Ano' not in colunas_existentes_no_df:
         logging.warning(f"Colunas de resumo esperadas ({colunas_resumo_esperadas}) não encontradas ou 'Ano' ausente. Colunas presentes: {df.columns.tolist()}")
         return pd.DataFrame(columns=colunas_resumo_esperadas)
    logging.info(f"Criando DataFrame resumido com colunas: {colunas_existentes_no_df}")
    return df[colunas_existentes_no_df].copy()

def exibir_dados(df, periodo, error, resumido=False):
    """Exibe um DataFrame formatado no Streamlit, com tratamento de erros."""
    st.markdown(f"#### {periodo}")
    if error:
        st.warning(f"Erro ao processar dados para '{periodo}': {error}")
        if not isinstance(df, pd.DataFrame) or df.empty:
            return
    elif not isinstance(df, pd.DataFrame) or df.empty:
        st.write(f"Nenhum dado para exibir para '{periodo}'.")
        return
    df_para_exibir = df.copy()
    if 'year' in df_para_exibir.columns:
        try:
            df_para_exibir['year'] = pd.to_numeric(df_para_exibir['year'], errors='coerce')
            df_para_exibir = df_para_exibir.sort_values(by='year', na_position='last').dropna(subset=['year'])
            df_para_exibir['year'] = df_para_exibir['year'].astype(int)
            df_para_exibir = df_para_exibir.rename(columns={'year': 'Ano'})
            logging.info(f"Coluna 'year' renomeada para 'Ano' e ordenada para '{periodo}'.")
        except Exception as e:
            logging.error(f"Erro ao ordenar/renomear 'year' para 'Ano' em '{periodo}': {e}")
            st.warning(f"Aviso: Não foi possível ordenar/renomear por ano para '{periodo}'.")
    elif 'Ano' in df_para_exibir.columns:
         try:
            df_para_exibir['Ano'] = pd.to_numeric(df_para_exibir['Ano'], errors='coerce')
            df_para_exibir = df_para_exibir.sort_values(by='Ano', na_position='last').dropna(subset=['Ano'])
            df_para_exibir['Ano'] = df_para_exibir['Ano'].astype(int)
            logging.info(f"Coluna 'Ano' ordenada para '{periodo}'.")
         except Exception as e:
            logging.error(f"Erro ao ordenar 'Ano' em '{periodo}': {e}")
            st.warning(f"Aviso: Não foi possível ordenar por ano para '{periodo}'.")
    if resumido:
        df_resumido = criar_dataframe_resumido(df_para_exibir)
        if df_resumido.empty and not df_para_exibir.empty:
             st.warning(f"Não foi possível gerar a tabela resumida para '{periodo}'. Exibindo tabela completa.")
        elif not df_resumido.empty:
             df_para_exibir = df_resumido
             logging.info(f"DataFrame resumido criado para '{periodo}'.")
    df_formatado = df_para_exibir.copy()
    if 'Ano' in df_formatado.columns:
        df_formatado['Ano'] = df_formatado['Ano'].astype(str).replace('nan', 'N/D').replace('<NA>', 'N/D')
    colunas_excluir_formatacao = ['Ano', 'month', 'monthNumber_exp', 'monthNumber_imp']
    colunas_numericas = [col for col in df_formatado.columns
                         if col not in colunas_excluir_formatacao and pd.api.types.is_numeric_dtype(df_para_exibir[col])]
    if colunas_numericas:
        try:
            df_formatado[colunas_numericas] = df_formatado[colunas_numericas].apply(lambda col: col.map(formatar_numero))
            logging.info(f"Formatação numérica aplicada às colunas: {colunas_numericas} para '{periodo}'.")
        except Exception as e:
             logging.error(f"Erro ao aplicar formatação numérica para '{periodo}': {e}", exc_info=True)
             st.warning(f"Aviso: Erro ao formatar números para '{periodo}'.")
    st.dataframe(df_formatado, use_container_width=True, hide_index=True)

def exibir_comparativo(
    df_2024_parcial,
    df_2025_parcial,
    error_2024_parcial,
    error_2025_parcial,
    resumido=False,
    last_updated_month=None
):
    """Exibe a comparação entre dados parciais de 2024 e 2025."""
    # Dicionário para converter número do mês em abreviação
    month_map = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }
    
    # Monta o título dinamicamente
    if last_updated_month and isinstance(last_updated_month, int) and last_updated_month in month_map:
        # Por exemplo, se last_updated_month=3, o título será "Comparativo Jan-Mar (Ano Atual vs Ano Anterior)"
        periodo_label = f"{month_map[1]}-{month_map[last_updated_month]}"
        st.markdown(f"### Comparativo {periodo_label} (Ano Atual vs Ano Anterior)")
    else:
        st.markdown("### Comparativo Ano Atual vs Ano Anterior (Mesmo Período)")
    
    if error_2024_parcial:
        st.warning(f"Erro ao obter/processar dados parciais de 2024: {error_2024_parcial}")
    if error_2025_parcial:
        st.warning(f"Erro ao obter/processar dados parciais de 2025: {error_2025_parcial}")
    
    df_24_valido = isinstance(df_2024_parcial, pd.DataFrame) and not df_2024_parcial.empty
    df_25_valido = isinstance(df_2025_parcial, pd.DataFrame) and not df_2025_parcial.empty
    
    if not df_24_valido or not df_25_valido:
        st.warning("Não há dados suficientes para comparação (um ou ambos os períodos estão vazios ou inválidos).")
        return
    
    df_comp_24 = df_2024_parcial.copy()
    df_comp_25 = df_2025_parcial.copy()
    
    if 'Ano' not in df_comp_24.columns or 'Ano' not in df_comp_25.columns:
        st.error("Erro interno: Coluna 'Ano' não encontrada nos DataFrames parciais para comparação.")
        return
    
    try:
        df_comparativo = pd.concat([df_comp_24, df_comp_25], ignore_index=True)
    except Exception as e:
        st.error(f"Erro ao concatenar DataFrames para comparação: {e}")
        return
    
    try:
        df_comparativo = df_comparativo.sort_values(by='Ano').reset_index(drop=True)
    except Exception:
        st.warning("Coluna 'Ano' não encontrada ou inválida para ordenar o comparativo.")
    
    # Exibe a tabela usando a função exibir_dados (que já existe)
    exibir_dados(df_comparativo, "Comparativo Agregado", None, resumido)


def obter_dados_tuple(ncm_code, tipo, last_updated_month):
    """
    Busca dados de exportação e importação da API Comex usando funções cacheadas.
    Retorna (dados_export, dados_import, erro_exp, erro_imp).
    """
    logging.info(f"Obtendo dados tipo '{tipo}' para NCM {ncm_code}, mês {last_updated_month}...")
    dados_export, dados_import = [], []
    erro_exp, erro_imp = None, None
    try:
        if tipo == "historico_anual":
            dados_export, erro_exp = obter_dados_comerciais(ncm_code, "export")
            dados_import, erro_imp = obter_dados_comerciais(ncm_code, "import")
        elif tipo == "2024_parcial":
            dados_export, erro_exp = obter_dados_comerciais_ano_anterior(ncm_code, "export", last_updated_month)
            dados_import, erro_imp = obter_dados_comerciais_ano_anterior(ncm_code, "import", last_updated_month)
        elif tipo == "2025_parcial":
            dados_export, erro_exp = obter_dados_comerciais_ano_atual(ncm_code, "export", last_updated_month)
            dados_import, erro_imp = obter_dados_comerciais_ano_atual(ncm_code, "import", last_updated_month)
        else:
            erro_msg = f"Tipo de dados '{tipo}' inválido solicitado."
            erro_exp, erro_imp = erro_msg, erro_msg
            logging.error(erro_msg)
        log_msg = f"Busca tipo '{tipo}' para NCM {ncm_code}: "
        log_msg += f"Exp: {len(dados_export) if isinstance(dados_export, list) else 'Erro/Inválido'} regs (Erro: {erro_exp}), "
        log_msg += f"Imp: {len(dados_import) if isinstance(dados_import, list) else 'Erro/Inválido'} regs (Erro: {erro_imp})"
        logging.info(log_msg)
    except Exception as e:
        logging.error(f"Erro inesperado em obter_dados_tuple para tipo '{tipo}', NCM {ncm_code}: {e}", exc_info=True)
        erro_exp = erro_exp or f"Erro inesperado na busca: {e}"
        erro_imp = erro_imp or f"Erro inesperado na busca: {e}"
    dados_export = dados_export if isinstance(dados_export, list) else []
    dados_import = dados_import if isinstance(dados_import, list) else []
    return dados_export, dados_import, erro_exp, erro_imp

def exibir_excel(ncm_code):
    """Exibe informações do NCM buscadas no arquivo Excel carregado."""
    if "df_excel" not in st.session_state or not isinstance(st.session_state.df_excel, dict) or not st.session_state.df_excel:
        logging.info("Dados estruturados do Excel não carregados ou ausentes no session_state. Pulando exibição do Excel.")
        st.info("Planilha Excel da CGIM não está disponível.")
        return
    st.subheader("📋 Dados da Planilha CGIM (Excel)")
    resultado_ncm = pd.DataFrame()
    resultado_entidades = pd.DataFrame()
    try:
        logging.info(f"Chamando proc.buscar_informacoes_ncm_completo para NCM: {ncm_code}")
        resultado_ncm, resultado_entidades = proc.buscar_informacoes_ncm_completo(st.session_state.df_excel, ncm_code)
        logging.info(f"Resultado NCM (tipo): {type(resultado_ncm)}, Vazio?: {resultado_ncm.empty if isinstance(resultado_ncm, pd.DataFrame) else 'N/A'}")
        if isinstance(resultado_ncm, pd.DataFrame) and not resultado_ncm.empty:
            logging.info(f"Resultado NCM (colunas): {resultado_ncm.columns.tolist()}")
        logging.info(f"Resultado Entidades (tipo): {type(resultado_entidades)}, Vazio?: {resultado_entidades.empty if isinstance(resultado_entidades, pd.DataFrame) else 'N/A'}")
        if isinstance(resultado_entidades, pd.DataFrame) and not resultado_entidades.empty:
            logging.info(f"Resultado Entidades (colunas): {resultado_entidades.columns.tolist()}")
    except Exception as e:
        st.error(f"Erro ao buscar informações do NCM {ncm_code} no Excel: {str(e)}")
        logging.error(f"Erro em buscar_informacoes_ncm_completo para NCM {ncm_code}: {e}", exc_info=True)
        return
    with st.container(border=True):
        st.markdown("##### Departamento Responsável")
        if isinstance(resultado_ncm, pd.DataFrame) and not resultado_ncm.empty:
            ncm_row = resultado_ncm.iloc[0]
            ncm_info = f"""
            <div style="font-size: 0.95em; line-height: 1.5; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <strong>Departamento:</strong> {ncm_row.get("Departamento Responsável", "N/D")}<br>
                <strong>Coordenação-Geral:</strong> {ncm_row.get("Coordenação-Geral Responsável", "N/D")}<br>
                <strong>Agrupamento:</strong> {ncm_row.get("Agrupamento", "N/D")}<br>
                <strong>Setores:</strong> {ncm_row.get("Setores", "N/D")}<br>
                <strong>Subsetores:</strong> {ncm_row.get("Subsetores", "N/D")}<br>
                <strong>Produtos:</strong> {ncm_row.get("Produtos", "N/D")}
            </div>
            """
            st.markdown(ncm_info, unsafe_allow_html=True)
        else:
            st.info(f"Informações do departamento para o NCM {ncm_code} não encontradas na planilha.")
    with st.container(border=True):
        st.markdown("##### Informações das Entidades Associadas")
        if isinstance(resultado_entidades, pd.DataFrame) and not resultado_entidades.empty:
            entidade_info_html = ""
            for _, row in resultado_entidades.iterrows():
                def mailto_link(email_value, default_text="N/D"):
                    email_str = str(email_value).strip()
                    if pd.notna(email_value) and '@' in email_str:
                        return f"<a href='mailto:{email_str}' target='_blank'>{email_str}</a>"
                    return default_text
                sigla = row.get('Sigla Entidade', 'N/D')
                nome_entidade = row.get('Entidade', row.get('NomeAbaEntidade', 'Nome não disponível'))
                dirigente = row.get('Nome do Dirigente', 'N/D')
                cargo_dirigente = row.get('Cargo', 'N/D')
                email_dirigente = mailto_link(row.get('E-mail'))
                tel_dirigente = str(row.get('Telefone', 'N/D'))
                cel_dirigente = str(row.get('Celular', 'N/D'))
                contato_imp = row.get('Contato Importante', 'N/D')
                cargo_contato = row.get('Cargo (Contato Importante)', 'N/D')
                email_contato = mailto_link(row.get('E-mail (Contato Importante)'))
                tel_contato = str(row.get('Telefone (Contato Importante)', 'N/D'))
                cel_contato = str(row.get('Celular (Contato Importante)', 'N/D'))
                entidade_info_html += f"""
                <div style="font-size: 0.9em; line-height: 1.4; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                    <strong>{sigla} - {nome_entidade}</strong><br>
                    <span style="margin-left: 10px;">Dirigente: {dirigente} ({cargo_dirigente})</span><br>
                    <span style="margin-left: 10px;">Email: {email_dirigente} | Tel: {tel_dirigente} | Cel: {cel_dirigente}</span><br>
                    <br>
                    <span style="margin-left: 10px; color: #444;">Contato Importante: {contato_imp} ({cargo_contato})</span><br>
                    <span style="margin-left: 10px; color: #444;">Email: {email_contato} | Tel: {tel_contato} | Cel: {cel_contato}</span>
                </div>
                """
            st.markdown(entidade_info_html, unsafe_allow_html=True)
        else:
            st.info(f"Não há informações de entidades associadas ao NCM {ncm_code} na planilha.")

def exibir_treemap(ncm_code, ncm_formatado, tipo_flow):
    """Busca dados e exibe o Treemap de importações ou exportações de 2024 por país."""
    titulo = f"📊 Treemap - {'Origem Importações' if tipo_flow == 'import' else 'Destino Exportações'} 2024 (US$ FOB)"
    st.subheader(titulo)
    dados = None
    func_gerar_grafico = None
    tipo_str = ""
    try:
        if tipo_flow == 'import':
            tipo_str = "importações"
            func_gerar_grafico = gerar_treemap_importacoes_2024
            dados = obter_dados_2024_por_pais(ncm_code)
            logging.info(f"Dados brutos obtidos para Treemap {tipo_flow} NCM {ncm_code}: Tipo {type(dados)}, Conteúdo inicial: {str(dados)[:200]}...")
        elif tipo_flow == 'export':
            tipo_str = "exportações"
            func_gerar_grafico = gerar_treemap_exportacoes_2024
            dados = obter_dados_2024_por_pais_export(ncm_code)
            logging.info(f"Dados brutos obtidos para Treemap {tipo_flow} NCM {ncm_code}: Tipo {type(dados)}, Conteúdo inicial: {str(dados)[:200]}...")
        else:
            st.error("Tipo de fluxo inválido para Treemap.")
            logging.error(f"Tipo de fluxo inválido '{tipo_flow}' para Treemap.")
            return
        if not isinstance(dados, list) or not dados:
            st.info(f"Nenhum dado de {tipo_str} 2024 por país disponível para gerar o Treemap (NCM: {ncm_formatado}).")
            logging.info(f"Dados vazios, None ou tipo inválido ({type(dados)}) para Treemap {tipo_flow} NCM {ncm_code}.")
            return
        df_treemap = pd.DataFrame(dados)
        colunas_necessarias = ["country", "metricFOB"]
        if not all(col in df_treemap.columns for col in colunas_necessarias):
            st.warning(f"Os dados de {tipo_str} por país retornados não possuem as colunas esperadas ({', '.join(colunas_necessarias)}).")
            logging.warning(f"Colunas ausentes para Treemap {tipo_flow} NCM {ncm_code}. Colunas presentes: {df_treemap.columns.tolist()}")
            return
        df_treemap['metricFOB'] = pd.to_numeric(df_treemap['metricFOB'], errors='coerce').fillna(0)
        if df_treemap.empty or df_treemap['metricFOB'].sum() <= 0:
             st.info(f"Dados de {tipo_str} 2024 por país estão vazios ou zerados para o Treemap (NCM: {ncm_formatado}).")
             logging.info(f"DataFrame vazio ou métrica zerada/negativa para Treemap {tipo_flow} NCM {ncm_code}.")
             return
        if func_gerar_grafico is None:
             st.error(f"Erro interno: Função para gerar gráfico de {tipo_str} não definida.")
             logging.error(f"func_gerar_grafico é None para tipo {tipo_flow}")
             return
        fig = func_gerar_grafico(df_treemap, ncm_code, ncm_formatado)
        if isinstance(fig, go.Figure):
             st.plotly_chart(fig, use_container_width=True)
             logging.info(f"Treemap de {tipo_str} exibido para NCM {ncm_code}.")
        else:
             st.warning(f"Não foi possível gerar o gráfico Treemap de {tipo_str}.")
             logging.warning(f"Função 'gerar_treemap..._{tipo_str}_2024' não retornou uma figura Plotly válida para NCM {ncm_code}.")
    except ImportError as e:
         st.error(f"Erro: Módulo ou função para gerar Treemap de {tipo_str} não importado(a) corretamente: {e}")
         logging.error(f"ImportError ao tentar gerar Treemap {tipo_flow} para NCM {ncm_code}.", exc_info=True)
    except AttributeError as e:
         st.error(f"Erro: Função para gerar Treemap de {tipo_str} não encontrada ou inválida: {e}")
         logging.error(f"Erro de atributo ao gerar Treemap {tipo_flow} para NCM {ncm_code}: {e}", exc_info=True)
    except ValueError as e:
        st.error(f"Erro de valor ao processar dados do Treemap de {tipo_str}: {e}")
        logging.error(f"ValueError ao gerar Treemap {tipo_flow} para NCM {ncm_code}: {e}", exc_info=True)
    except Exception as e:
        st.error(f"Erro inesperado ao gerar Treemap de {tipo_str}: {e}")
        logging.error(f"Erro INESPERADO na função exibir_treemap ({tipo_flow}, NCM {ncm_code}): {e}", exc_info=True)

def exibir_api(ncm_code, last_updated_month, last_updated_year):
    """Orquestra a busca e exibição de dados e gráficos da API Comex."""
    st.subheader("📊 Dados da API Comex e Gráficos")
    exibir_resumida = st.checkbox("Exibir tabelas comparativas resumidas", key="chk_resumida", value=True)
    dados_export_hist, dados_import_hist, err_exp_hist, err_imp_hist = obter_dados_tuple(ncm_code, "historico_anual", last_updated_month)
    dados_export_24p, dados_import_24p, err_exp_24p, err_imp_24p = obter_dados_tuple(ncm_code, "2024_parcial", last_updated_month)
    dados_export_25p, dados_import_25p, err_exp_25p, err_imp_25p = obter_dados_tuple(ncm_code, "2025_parcial", last_updated_month)
    df_hist_anual, df_2024_parcial, df_2025_parcial = None, None, None
    error_hist, error_2024_parcial, error_2025_parcial = None, None, None
    try:
        df_hist_anual, error_hist_proc = proc.processar_dados_export_import(dados_export_hist, dados_import_hist, last_updated_month)
        periodo_hist = "Série Temporal (Anual)"
        error_hist = error_hist_proc or err_exp_hist or err_imp_hist
        df_2024_parcial, error_2024_proc = proc.processar_dados_ano_anterior(dados_export_24p, dados_import_24p, last_updated_month)
        periodo_2024_parcial = f"2024 (Jan a {last_updated_month:02d})"
        error_2024_parcial = error_2024_proc or err_exp_24p or err_imp_24p
        df_2025_parcial, error_2025_proc = proc.processar_dados_ano_atual(dados_export_25p, dados_import_25p, last_updated_month)
        periodo_2025_parcial = f"2025 (Jan a {last_updated_month:02d})"
        error_2025_parcial = error_2025_proc or err_exp_25p or err_imp_25p
    except AttributeError as e:
         st.error(f"Erro: Uma função de processamento não foi encontrada no módulo 'processamento': {e}.")
         logging.error(f"Erro de atributo no módulo 'proc' durante processamento API: {e}", exc_info=True)
         error_hist = error_hist or f"Erro de processamento: {e}"
         error_2024_parcial = error_2024_parcial or f"Erro de processamento: {e}"
         error_2025_parcial = error_2025_parcial or f"Erro de processamento: {e}"
    except Exception as e:
         st.error(f"Erro inesperado durante o processamento dos dados da API: {e}")
         logging.error(f"Erro inesperado no processamento dos dados da API: {e}", exc_info=True)
         error_hist = error_hist or f"Erro inesperado de processamento: {e}"
         error_2024_parcial = error_2024_parcial or f"Erro inesperado de processamento: {e}"
         error_2025_parcial = error_2025_parcial or f"Erro inesperado de processamento: {e}"
    with st.container(border=True):
        st.markdown("##### Dados Históricos e Comparativos")
    exibir_dados(df_hist_anual, periodo_hist, error_hist, resumido=False)
    st.divider()
    exibir_comparativo(
        df_2024_parcial,
        df_2025_parcial,
        error_2024_parcial,
        error_2025_parcial,
        exibir_resumida,
        st.session_state.last_updated_month
    )
    try:
        df_24_valido = isinstance(df_2024_parcial, pd.DataFrame) and not df_2024_parcial.empty
        df_25_valido = isinstance(df_2025_parcial, pd.DataFrame) and not df_2025_parcial.empty
        if df_24_valido and df_25_valido:
             #resumo_tabelas.exibir_resumos(df_2024_parcial, df_2025_parcial)
             logging.info("Quadros-resumo exibidos.")
        else:
             st.info("Não foi possível exibir os quadros-resumo (dados parciais ausentes ou inválidos).")
             logging.warning(f"Quadros-resumo pulados. DF24 válido: {df_24_valido}, DF25 válido: {df_25_valido}")
    except TypeError as e:
         if "positional arguments but" in str(e):
              st.error("Erro: A função 'exibir_resumos' no módulo 'resumo_tabelas' não está configurada para receber os dados necessários.")
              logging.error(f"TypeError em resumo_tabelas.exibir_resumos: {e}.", exc_info=True)
         else:
              st.warning(f"Erro ao chamar a função de quadros-resumo: {e}")
              logging.warning(f"Falha ao chamar resumo_tabelas.exibir_resumos: {e}", exc_info=True)
    except AttributeError as e:
         st.warning(f"Função 'exibir_resumos' não encontrada ou erro no módulo 'resumo_tabelas': {e}")
         logging.warning(f"Falha ao chamar resumo_tabelas.exibir_resumos: {e}", exc_info=True)
    except Exception as e:
        st.warning(f"Não foi possível exibir os quadros-resumo: {e}")
        logging.warning(f"Falha ao chamar resumo_tabelas.exibir_resumos: {e}", exc_info=True)
    st.markdown("### Gráficos de Desempenho")
    if isinstance(df_hist_anual, pd.DataFrame) and not df_hist_anual.empty:
        ncm_formatado = f"{str(ncm_code)[:4]}.{str(ncm_code)[4:6]}.{str(ncm_code)[6:]}"
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            try:
                st.markdown("##### Importações (KG)")
                fig_import_kg = graf_kg.gerar_grafico_importacoes(df_hist_anual, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year)
                if isinstance(fig_import_kg, go.Figure):
                     st.plotly_chart(fig_import_kg, use_container_width=True)
                else:
                     st.warning("Gráfico de Importações (KG) não pôde ser gerado.")
            except AttributeError as e:
                 st.error(f"Erro: Função 'gerar_grafico_importacoes' não encontrada em 'graf_kg': {e}")
                 logging.error(f"Erro de atributo em graf_kg.gerar_grafico_importacoes: {e}", exc_info=True)
            except Exception as e:
                 st.error(f"Erro ao gerar gráfico de Importações (KG): {e}")
                 logging.error(f"Erro em gerar_grafico_importacoes (KG): {e}", exc_info=True)
            try:
                st.markdown("##### Importações (US$ FOB)")
                fig_import_fob = graf_fob.gerar_grafico_importacoes_fob(df_hist_anual, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year)
                if isinstance(fig_import_fob, go.Figure):
                     st.plotly_chart(fig_import_fob, use_container_width=True)
                else:
                     st.warning("Gráfico de Importações (FOB) não pôde ser gerado.")
            except AttributeError as e:
                 st.error(f"Erro: Função 'gerar_grafico_importacoes_fob' não encontrada em 'graf_fob': {e}")
                 logging.error(f"Erro de atributo em graf_fob.gerar_grafico_importacoes_fob: {e}", exc_info=True)
            except Exception as e:
                 st.error(f"Erro ao gerar gráfico de Importações (FOB): {e}")
                 logging.error(f"Erro em gerar_grafico_importacoes_fob: {e}", exc_info=True)
            try:
                st.markdown("##### Preço Médio (US$ FOB/KG)")
                fig_preco_medio = graf_preco_medio.gerar_grafico_preco_medio(df_hist_anual, df_2024_parcial, ncm_formatado, last_updated_month)
                if isinstance(fig_preco_medio, go.Figure):
                     st.plotly_chart(fig_preco_medio, use_container_width=True)
                else:
                     st.warning("Gráfico de Preço Médio não pôde ser gerado.")
            except AttributeError as e:
                 st.error(f"Erro: Função 'gerar_grafico_preco_medio' não encontrada em 'graf_preco_medio': {e}")
                 logging.error(f"Erro de atributo em graf_preco_medio.gerar_grafico_preco_medio: {e}", exc_info=True)
            except Exception as e:
                 st.error(f"Erro ao gerar gráfico de Preço Médio: {e}")
                 logging.error(f"Erro em gerar_grafico_preco_medio: {e}", exc_info=True)
        with col_graf2:
            try:
                st.markdown("##### Exportações (KG)")
                fig_export_kg = graf_exp.gerar_grafico_exportacoes(df_hist_anual, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year)
                if isinstance(fig_export_kg, go.Figure):
                     st.plotly_chart(fig_export_kg, use_container_width=True)
                else:
                     st.warning("Gráfico de Exportações (KG) não pôde ser gerado.")
            except AttributeError as e:
                 st.error(f"Erro: Função 'gerar_grafico_exportacoes' não encontrada em 'graf_exp': {e}")
                 logging.error(f"Erro de atributo em graf_exp.gerar_grafico_exportacoes: {e}", exc_info=True)
            except Exception as e:
                 st.error(f"Erro ao gerar gráfico de Exportações (KG): {e}")
                 logging.error(f"Erro em gerar_grafico_exportacoes (KG): {e}", exc_info=True)
            try:
                st.markdown("##### Exportações (US$ FOB)")
                fig_export_fob = graf_exp_fob.gerar_grafico_exportacoes_fob(df_hist_anual, df_2024_parcial, ncm_formatado, last_updated_month, last_updated_year)
                if isinstance(fig_export_fob, go.Figure):
                     st.plotly_chart(fig_export_fob, use_container_width=True)
                else:
                     st.warning("Gráfico de Exportações (FOB) não pôde ser gerado.")
            except AttributeError as e:
                 st.error(f"Erro: Função 'gerar_grafico_exportacoes_fob' não encontrada em 'graf_exp_fob': {e}")
                 logging.error(f"Erro de atributo em graf_exp_fob.gerar_grafico_exportacoes_fob: {e}", exc_info=True)
            except Exception as e:
                 st.error(f"Erro ao gerar gráfico de Exportações (FOB): {e}")
                 logging.error(f"Erro em gerar_grafico_exportacoes_fob: {e}", exc_info=True)
            try:
                st.markdown("##### Importações Acumuladas (12 Meses - KG)")
                fig_12m = gerar_grafico_importacoes_12meses(ncm_code, ncm_formatado)
                if fig_12m is not None:
                    if isinstance(fig_12m, go.Figure):
                         st.plotly_chart(fig_12m, use_container_width=True)
                         st.caption("Fonte: Comex Stat/MDIC. Elaboração própria.")
                         logging.info("Gráfico 12 meses (Plotly) exibido.")
                    else:
                         st.warning("Gráfico de importações 12 meses não pôde ser exibido (formato não reconhecido).")
                         logging.warning(f"Tipo retornado por gerar_grafico_importacoes_12meses: {type(fig_12m)}")
                else:
                    logging.info("Gráfico 12 meses não gerado (retornou None).")
            except NameError:
                 st.error("Erro: A função 'gerar_grafico_importacoes_12meses' não foi importada corretamente.")
                 logging.error("NameError ao chamar gerar_grafico_importacoes_12meses.")
            except AttributeError as e:
                 st.error(f"Erro: Função 'gerar_grafico_importacoes_12meses' não encontrada no módulo importado: {e}")
                 logging.error(f"Erro de atributo em gerar_grafico_importacoes_12meses: {e}", exc_info=True)
            except Exception as e:
                 st.error(f"Erro ao gerar/exibir gráfico de Importações 12 Meses: {e}")
                 logging.error(f"Erro em gerar_grafico_importacoes_12meses: {e}", exc_info=True)
        
        cols = st.columns(2)
        with cols[0]:
            exibir_treemap(ncm_code, ncm_formatado, tipo_flow='import')
        with cols[1]:
            exibir_treemap(ncm_code, ncm_formatado, tipo_flow='export')
    elif not error_hist:
        st.warning("Não há dados históricos da API disponíveis para gerar os gráficos.")

def analisar_ncm(ncm_code, can_analyze_api, last_updated_month, last_updated_year):
    ncm_formatado = f"{ncm_code[:4]}.{ncm_code[4:6]}.{ncm_code[6:8]}"
    st.header(f"🔍 Análise Detalhada - NCM {ncm_formatado}")
    if st.session_state.ncms_filtradas:
         if st.button("⬅️ Voltar para a lista de NCMs", key="back_button"):
             st.session_state.selected_ncm = None
             logging.info("Botão 'Voltar' clicado.")
             if hasattr(st, "experimental_rerun"):
                 st.experimental_rerun()
    else:
         if st.button("🧹 Limpar Busca", key="clear_button"):
              st.session_state.selected_ncm = None
              logging.info("Botão 'Limpar Busca' clicado.")
              if hasattr(st, "experimental_rerun"):
                  st.experimental_rerun()
    with st.spinner(f"Buscando descrição para NCM {ncm_formatado}..."):
        try:
            descricao = obter_descricao_ncm(ncm_code)
            if descricao and "Erro" not in descricao:
                st.subheader(f"📖 {descricao}")
                logging.info(f"Descrição obtida para NCM {ncm_code}: {descricao}")
            else:
                st.warning(f"Não foi possível obter a descrição para o NCM {ncm_formatado}. (API: {descricao})")
                logging.warning(f"Falha ao obter descrição para NCM {ncm_code}. Resposta API: {descricao}")
        except Exception as e:
             st.error(f"Erro crítico ao obter descrição do Ncm: {e}")
             logging.error(f"Erro crítico em obter_descricao_ncm para {ncm_code}: {e}", exc_info=True)
    try:
        if isinstance(st.session_state.df_excel, dict) and st.session_state.df_excel:
            exibir_excel(ncm_code)
        else:
            st.info("Planilha Excel não carregada ou inválida, pulando seção de dados do Excel.")
            logging.info("Dados do Excel não exibidos (não carregados ou inválidos no session_state).")
    except Exception as e:
         st.error(f"Erro ao exibir dados do Excel para NCM {ncm_code}: {e}")
         logging.error(f"Erro em exibir_excel para {ncm_code}: {e}", exc_info=True)
    if can_analyze_api:
        with st.spinner(f"Carregando dados da API e gráficos para NCM {ncm_formatado}..."):
            try:
                exibir_api(ncm_code, last_updated_month, last_updated_year)
            except Exception as e:
                 st.error(f"Erro ao exibir dados da API e gráficos para NCM {ncm_code}: {e}")
                 logging.error(f"Erro em exibir_api para {ncm_code}: {e}", exc_info=True)
    else:
         st.warning("Análise de dados da API Comex indisponível (data de atualização não obtida).")

         
def main():
    st.title("📊 Análise de Comércio Exterior")
    if 'selected_ncm' not in st.session_state:
        st.session_state.selected_ncm = None
    if 'df_excel' not in st.session_state:
        st.session_state.df_excel = None
    if 'ncms_filtradas' not in st.session_state:
        st.session_state.ncms_filtradas = []
    if 'last_updated_date' not in st.session_state:
        st.session_state.last_updated_date = None
        st.session_state.last_updated_year = None
        st.session_state.last_updated_month = None
    if st.session_state.last_updated_date is None:
        try:
            date, year, month = obter_data_ultima_atualizacao()
            if date and isinstance(year, (int, str)) and str(year).isdigit() and isinstance(month, (int, str)) and str(month).isdigit():
                st.session_state.last_updated_date = str(date)
                st.session_state.last_updated_year = int(year)
                st.session_state.last_updated_month = int(month)
                logging.info(f"Data de atualização obtida e armazenada: {date}, {month}/{year}")
            else:
                st.error(f"❌ Erro: Resposta inválida ao obter data de atualização da API Comex. Data: {date}, Ano: {year}, Mês: {month}")
                logging.error(f"Resposta inválida de obter_data_ultima_atualizacao: Data={date}, Ano={year}, Mês={month}")
        except Exception as e:
             st.error(f"❌ Erro crítico ao obter data de atualização da API: {e}")
             logging.error(f"Erro crítico em obter_data_ultima_atualizacao: {e}", exc_info=True)
    if st.session_state.last_updated_date:
         st.success(f"📅 Dados da API Comex atualizados até: {st.session_state.last_updated_month:02d}/{st.session_state.last_updated_year} (Ref: {st.session_state.last_updated_date})")
    else:
         st.warning("⚠️ Não foi possível obter a data de atualização da API. A análise pode estar indisponível ou usar dados antigos.")
    # --- Seção de Upload e Processamento de Arquivos ---
    with st.expander("📁 Carregar Arquivos (Pauta PDF)", expanded=True):
        col1 = st.columns(1)[0]
        with col1:
            uploaded_pdf = st.file_uploader("1. Carregar PDF da Pauta", type=['pdf'], key="pdf_uploader")
        process_button_clicked = st.button("Processar Arquivos e Filtrar NCMs", key="process_button",
                                           disabled=(not uploaded_pdf),
                                           use_container_width=True)
        if process_button_clicked:
            with st.spinner("Processando arquivos... Por favor, aguarde."):
                try:
                    pdf_bytes = uploaded_pdf.getvalue()
                    ncms_pdf_pontuados = extrair_ncms_pdf(pdf_bytes)
                    ncms_pdf_8digitos = {formatar_ncm_8digitos(ncm) for ncm in ncms_pdf_pontuados if formatar_ncm_8digitos(ncm)}
                    logging.info(f"{len(ncms_pdf_8digitos)} NCMs únicos (8 dígitos) extraídos do PDF.")
                    if "df_excel" not in st.session_state or not st.session_state.df_excel:
                        st.error("Planilha Excel não carregada. Verifique o link ou a conexão com o GitHub.")
                        return
                    dados_excel_carregados = st.session_state.df_excel
                    df_departamentos = dados_excel_carregados.get("NCMs-CGIM-DINTE")
                    if not isinstance(df_departamentos, pd.DataFrame) or df_departamentos.empty:
                         msg_erro_excel = "Aba CGIM ('NCMs-CGIM-DINTE' ou primeira aba) não encontrada, está vazia ou inválida no Excel."
                         st.error(f"Erro de Processamento: {msg_erro_excel}")
                         raise ValueError(msg_erro_excel)
                    if 'NCM' not in df_departamentos.columns:
                         msg_erro_excel = "Coluna 'NCM' não encontrada na aba CGIM do Excel."
                         st.error(f"Erro de Processamento: {msg_erro_excel}")
                         raise KeyError(msg_erro_excel)
                    ncms_excel = set(df_departamentos['NCM'].dropna())
                    logging.info(f"{len(ncms_excel)} NCMs únicos (8 dígitos) extraídos da aba CGIM do Excel.")
                    ncms_comuns = sorted(list(ncms_pdf_8digitos.intersection(ncms_excel)))
                    logging.info(f"{len(ncms_comuns)} NCMs comuns encontrados entre PDF e Excel.")
                    if ncms_comuns:
                        st.session_state.ncms_filtradas = ncms_comuns
                        st.success(f"✅ Arquivos processados! {len(ncms_comuns)} NCMs da CGIM encontradas na pauta.")
                        st.session_state.selected_ncm = None
                    else:
                        st.warning("⚠️ Nenhuma NCM comum encontrada entre a planilha CGIM e o PDF da pauta.")
                        st.session_state.ncms_filtradas = []
                        st.session_state.selected_ncm = None
                    
                except KeyError as e:
                     st.error(f"Erro de Processamento: Coluna não encontrada - {e}. Verifique o nome/conteúdo da coluna na planilha Excel.")
                     logging.error(f"KeyError ao processar arquivos: {e}", exc_info=True)
                     st.session_state.ncms_filtradas = []
                     st.session_state.df_excel = None
                except ValueError as e:
                     if "Aba CGIM" not in str(e):
                          st.error(f"Erro de Processamento: {e}.")
                     logging.error(f"ValueError ao processar arquivos: {e}", exc_info=True)
                     st.session_state.ncms_filtradas = []
                     st.session_state.df_excel = None
                except Exception as e:
                    st.error(f"Erro inesperado ao processar os arquivos: {str(e)}")
                    logging.error(f"Erro inesperado ao processar arquivos: {e}", exc_info=True)
                    st.session_state.ncms_filtradas = []
                    st.session_state.df_excel = None
    if st.session_state.ncms_filtradas:
        st.header("📋 NCMs da CGIM na Pauta (Clique para analisar)")
        num_cols = 5
        cols = st.columns(num_cols)
        for idx, ncm in enumerate(st.session_state.ncms_filtradas):
            col_index = idx % num_cols
            ncm_fmt_button = f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}"
            with cols[col_index]:
                if st.button(ncm_fmt_button, key=f"btn_{ncm}", help=f"Analisar NCM {ncm_fmt_button}", use_container_width=True):
                    st.session_state.selected_ncm = ncm
                    logging.info(f"Botão NCM {ncm} clicado. Selecionado: {st.session_state.selected_ncm}")
                    if hasattr(st, "experimental_rerun"):
                     st.experimental_rerun()
    if st.session_state.selected_ncm:
        can_analyze_api = st.session_state.last_updated_month is not None and st.session_state.last_updated_year is not None
        analisar_ncm(st.session_state.selected_ncm, can_analyze_api, st.session_state.last_updated_month, st.session_state.last_updated_year)
    elif not st.session_state.ncms_filtradas:
        st.header("🔍 Ou Faça uma Busca Manual de NCM")
        ncm_input = st.text_input("Digite o código NCM (com ou sem pontos):", key="manual_ncm_input", max_chars=10)
        buscar_manual_button = st.button("Buscar NCM Manualmente", key="manual_search_button")
        if buscar_manual_button and ncm_input:
            ncm_clean = formatar_ncm_8digitos(ncm_input)
            if len(ncm_clean) == 8:
                 can_analyze_api = st.session_state.last_updated_month is not None and st.session_state.last_updated_year is not None
                 with st.spinner(f"Buscando dados para NCM {ncm_clean}..."):
                      analisar_ncm(ncm_clean, can_analyze_api, st.session_state.last_updated_month, st.session_state.last_updated_year)
            else:
                 st.warning("NCM inválido. Digite um NCM com 8 dígitos (pontos são opcionais).")

@st.cache_data
def extrair_ncms_pdf(pdf_file_bytes):
    """Extrai NCMs no formato xxxx.xx.xx de bytes de um arquivo PDF."""
    ncms_encontradas = set()
    logging.info("Iniciando extração de NCMs do PDF...")
    try:
        pdf_stream = BytesIO(pdf_file_bytes)
        reader = PdfReader(pdf_stream)
        num_paginas = len(reader.pages)
        logging.info(f"Lendo PDF com {num_paginas} páginas.")
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:
                    matches = re.findall(r'\b(\d{4}\.\d{2}\.\d{2})\b', text)
                    if matches:
                         ncms_encontradas.update(matches)
            except Exception as e_page:
                 logging.warning(f"Erro ao extrair texto da página {i+1} do PDF: {e_page}")
        logging.info(f"Extração de NCMs do PDF concluída. {len(ncms_encontradas)} NCMs únicos (com pontos) encontrados.")
    except Exception as e:
        st.error(f"Erro crítico ao ler o arquivo PDF: {e}")
        logging.error(f"Erro crítico ao ler PDF: {e}", exc_info=True)
        return []
    return list(ncms_encontradas)

def formatar_ncm_8digitos(ncm_value):
    """Converte NCM de vários formatos para 8 dígitos (string), ou retorna vazio."""
    if pd.isna(ncm_value):
        return ""
    ncm_str = str(ncm_value).strip()
    ncm_digits = re.sub(r'\D', '', ncm_str)
    ncm_8 = ncm_digits[:8]
    return ncm_8 if len(ncm_8) == 8 else ""

def analisar_ncm(ncm_code, can_analyze_api, last_updated_month, last_updated_year):
    """
    Função central para exibir a análise detalhada de um NCM selecionado ou buscado.
    """
    ncm_formatado = f"{ncm_code[:4]}.{ncm_code[4:6]}.{ncm_code[6:8]}"
    st.header(f"🔍 Análise Detalhada - NCM {ncm_formatado}")
    if st.session_state.ncms_filtradas:
         if st.button("⬅️ Voltar para a lista de NCMs", key="back_button"):
             st.session_state.selected_ncm = None
             logging.info("Botão 'Voltar' clicado.")
             if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
    else:
         if st.button("🧹 Limpar Busca", key="clear_button"):
              st.session_state.selected_ncm = None
              logging.info("Botão 'Limpar Busca' clicado.")
              if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
    with st.spinner(f"Buscando descrição para NCM {ncm_formatado}..."):
        try:
            descricao = obter_descricao_ncm(ncm_code)
            if descricao and "Erro" not in descricao:
                st.subheader(f"📖 {descricao}")
                logging.info(f"Descrição obtida para NCM {ncm_code}: {descricao}")
            else:
                st.warning(f"Não foi possível obter a descrição para o NCM {ncm_formatado}. (API: {descricao})")
                logging.warning(f"Falha ao obter descrição para NCM {ncm_code}. Resposta API: {descricao}")
        except Exception as e:
             st.error(f"Erro crítico ao obter descrição do Ncm: {e}")
             logging.error(f"Erro crítico em obter_descricao_ncm para {ncm_code}: {e}", exc_info=True)
    try:
        if isinstance(st.session_state.df_excel, dict) and st.session_state.df_excel:
            exibir_excel(ncm_code)
        else:
            st.info("Planilha Excel não carregada ou inválida, pulando seção de dados do Excel.")
            logging.info("Dados do Excel não exibidos (não carregados ou inválidos no session_state).")
    except Exception as e:
         st.error(f"Erro ao exibir dados do Excel para NCM {ncm_code}: {e}")
         logging.error(f"Erro em exibir_excel para {ncm_code}: {e}", exc_info=True)
    if can_analyze_api:
        with st.spinner(f"Carregando dados da API e gráficos para NCM {ncm_formatado}..."):
            try:
                exibir_api(ncm_code, last_updated_month, last_updated_year)
            except Exception as e:
                 st.error(f"Erro ao exibir dados da API e gráficos para NCM {ncm_code}: {e}")
                 logging.error(f"Erro em exibir_api para {ncm_code}: {e}", exc_info=True)
    else:
         st.warning("Análise de dados da API Comex indisponível (data de atualização não obtida).")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
         logging.critical(f"Erro fatal não capturado na execução principal: {e}", exc_info=True)
         try:
              st.error(f"Ocorreu um erro crítico inesperado na aplicação: {e}")
         except:
              pass




