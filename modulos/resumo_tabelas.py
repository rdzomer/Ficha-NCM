import pandas as pd
import streamlit as st

def obter_resumo_importacoes():
    data = {
        "Ano": [
            "2020", "2021", "2022", "2023", "2024", "2024 (Até mês 02)", "2025 (Até mês 02)"
        ],
        "Importações (US$ FOB)": [
            41205815, 43796074, 37730836, 57773750, 95552432, 16735332, 15439708
        ],
        "Var. (%) Imp (US$ FOB)": [
            "-2,72%", "6,29%", "-13,85%", "53,12%", "65,39%", "-82,49%", "-7,74%"
        ],
        "Importações (kg)": [
            7801734, 8420404, 7086950, 10653030, 20513036, 3447420, 3483839
        ],
        "Var. (%) Imp (kg)": [
            "3,31%", "7,93%", "-15,84%", "50,32%", "92,56%", "-83,19%", "1,06%"
        ],
        "Preço médio Importação (US$ FOB/Ton)": [
            5281.62, 5201.18, 5323.99, 5423.22, 4658.13, 4854.45, 4431.81
        ],
        "Var. (%) Preço médio Imp": [
            "-5,83%", "-1,52%", "2,36%", "1,86%", "-14,11%", "4,21%", "-8,71%"
        ]
    }
    return pd.DataFrame(data)

def obter_resumo_exportacoes():
    data = {
        "Ano": [
            "2020", "2021", "2022", "2023", "2024", "2024 (Até mês 02)", "2025 (Até mês 02)"
        ],
        "Exportações (US$ FOB)": [
            90116288, 130069572, 111548918, 117423324, 125616036, 16008444, 15195508
        ],
        "Var. (%) Exp (US$ FOB)": [
            "45,31%", "44,34%", "-14,24%", "5,27%", "6,98%", "-87,26%", "-5,08%"
        ],
        "Exportações (kg)": [
            14905328, 19086705, 15346077, 16605021, 17922744, 2217920, 2087938
        ],
        "Var. (%) Exp (kg)": [
            "53,91%", "28,05%", "-19,60%", "8,20%", "7,94%", "-87,63%", "-5,86%"
        ],
        "Preço médio Exp (US$ FOB/Ton)": [
            6045.91, 6814.67, 7268.89, 7071.56, 7008.75, 7217.77, 7277.76
        ],
        "Var. (%) Preço médio Exp": [
            "-5,59%", "12,72%", "6,67%", "-2,71%", "-0,89%", "2,98%", "0,83%"
        ]
    }
    return pd.DataFrame(data)

def exibir_resumos(df_2024_parcial, df_2025_parcial):
    st.subheader("📋 Quadro Resumo das Importações")
    df_imp = obter_resumo_importacoes()
    st.dataframe(df_imp, hide_index=True)

    st.subheader("📋 Quadro Resumo das Exportações")
    df_exp = obter_resumo_exportacoes()
    st.dataframe(df_exp, hide_index=True)
