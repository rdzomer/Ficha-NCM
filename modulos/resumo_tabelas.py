# -*- coding: utf-8 -*-
# Arquivo: app.py

import streamlit as st
import pandas as pd

# --------------------------------------------
# 1) Funções de dados (obter_resumo_importacoes, obter_resumo_exportacoes)
#    (Mantenha a versão com chaves únicas)
# --------------------------------------------
def obter_resumo_importacoes():
    data = { 
        "Ano": ["2020", "2021", "2022", "2023", "2024", "2024 (Até mês 02)", "2025 (Até mês 02)"], 
        "Importações (US$ FOB)": [41205815, 43796074, 37730836, 57773750, 95552432, 16735332, 15439708], 
        "Var. (%) FOB": ["-2,72%", "6,29%", "-13,85%", "53,12%", "65,39%", "-82,49%", "-7,74%"], 
        "Importações (kg)": [7801734, 8420404, 7086950, 10653030, 20513036, 3447420, 3483839], 
        "Var. (%) KG": ["3,31%", "7,93%", "-15,84%", "50,32%", "92,56%", "-83,19%", "1,06%"], 
        "Preço médio": [5281.62, 5201.18, 5323.99, 5423.22, 4658.13, 4854.45, 4431.81], 
        "Var. (%) Preço": ["-5,83%", "-1,52%", "2,36%", "1,86%", "-14,11%", "4,21%", "-8,71%"] 
    }
    return pd.DataFrame(data)

def obter_resumo_exportacoes():
    data = { 
        "Ano": ["2020", "2021", "2022", "2023", "2024", "2024 (Até mês 02)", "2025 (Até mês 02)"], 
        "Exportações (US$ FOB)": [90116288, 130069572, 111548918, 117423324, 125616036, 16008444, 15195508], 
        "Var. (%) FOB": ["45,31%", "44,34%", "-14,24%", "5,27%", "6,98%", "-87,26%", "-5,08%"], 
        "Exportações (kg)": [14905328, 19086705, 15346077, 16605021, 17922744, 2217920, 2087938], 
        "Var. (%) KG": ["53,91%", "28,05%", "-19,60%", "8,20%", "7,94%", "-87,63%", "-5,86%"], 
        "Preço médio Exp (US$ FOB/Ton)": [6045.91, 6814.67, 7268.89, 7071.56, 7008.75, 7217.77, 7277.76], 
        "Var. (%) Preço": ["-5,59%", "12,72%", "6,67%", "-2,71%", "-0,89%", "2,98%", "0,83%"] 
    }
    return pd.DataFrame(data)

# --------------------------------------------
# 2) Funções de formatação (mantidas)
# --------------------------------------------
def formatar_ptbr_string(valor):
    if pd.isna(valor): return ""
    if isinstance(valor, (int, float)):
        try: num_str = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."); return num_str
        except (ValueError, TypeError): return str(valor)
    return str(valor)

def aplicar_formatacao_dataframe(df):
    df_formatado = df.copy()
    colunas_numericas = df.select_dtypes(include=['number']).columns
    for col in colunas_numericas:
        if col in df_formatado.columns: df_formatado[col] = df_formatado[col].apply(formatar_ptbr_string)
    return df_formatado

# --------------------------------------------
# 3) Função principal: exibir_resumos (CSS com FLEXBOX)
# --------------------------------------------
def exibir_resumos(df_2024_parcial, df_2025_parcial):
    """
    Exibe duas tabelas lado a lado usando st.dataframe,
    com CSS usando Flexbox para centralizar o conteúdo.
    """
    # CSS Injetado (Usando FLEXBOX no contêiner interno)
    st.markdown("""
    <style>
        /* Container Geral */
        .stDataFrame { width: 100% !important; }

        /* Células de Cabeçalho (TH) */
        .stDataFrame th {
            text-align: center !important;
            vertical-align: middle !important;
            background-color: #e9ecef !important;
            font-weight: bold !important;
            white-space: normal !important; word-wrap: break-word !important;
            border: 1px solid #ddd !important; padding: 8px !important;
        }

        /* Células de Dados (TD) - Estilos gerais */
        .stDataFrame td {
            vertical-align: middle !important; /* Centraliza célula verticalmente */
            white-space: normal !important; word-wrap: break-word !important;
            border: 1px solid #ddd !important; padding: 0px !important; /* REDUZIDO padding do TD */
        }

        /* --- REGRA CRÍTICA FLEXBOX --- */
        /* Transforma o DIV interno em um container Flex */
        .stDataFrame td div[data-testid="stMarkdownContainer"] {
            display: flex !important;
            align-items: center !important;    /* Centraliza verticalmente DENTRO do flex container */
            justify-content: center !important; /* Centraliza horizontalmente DENTRO do flex container */
            width: 100% !important;           /* Garante que o flex container ocupe a célula */
            height: 100%; /* Tenta fazer ocupar a altura da célula */
            padding: 8px !important; /* Adiciona padding AQUI dentro */
        }

        /* Garante que o parágrafo <p> interno se comporte bem */
        .stDataFrame td div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important; /* Remove margens do parágrafo */
            text-align: center !important; /* Centraliza o texto dentro do parágrafo */
        }

        /* Linhas pares */
        .stDataFrame tbody tr:nth-child(even) td { background-color: #f9f9f9 !important; }

        /* Oculta índice fantasma */
        .stDataFrame [data-testid="stDataFrameEmptyCell"],
        .stDataFrame [data-testid="stDataFrameIndexCell"] {
             visibility: hidden !important; border-width: 0px !important;
             padding: 0px !important; width: 0px !important;
             min-width: 0px !important; max-width: 0px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- CRIA AS COLUNAS E EXIBE DATAFRAMES (sem alterações aqui) ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Quadro Resumo das Importações")
        df_imp_original = obter_resumo_importacoes()
        if not df_imp_original.empty:
            df_imp_formatado = aplicar_formatacao_dataframe(df_imp_original)
            st.dataframe(df_imp_formatado, hide_index=True, use_container_width=True)
        else: st.info("Dados de importação não disponíveis.")
    with col2:
        st.subheader("📊 Quadro Resumo das Exportações")
        df_exp_original = obter_resumo_exportacoes()
        if not df_exp_original.empty:
            df_exp_formatado = aplicar_formatacao_dataframe(df_exp_original)
            st.dataframe(df_exp_formatado, hide_index=True, use_container_width=True)
        else: st.info("Dados de exportação não disponíveis.")

# Para testar isoladamente no Streamlit
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Tabelas Lado a Lado (Flexbox Centering)")
    exibir_resumos(None, None)
