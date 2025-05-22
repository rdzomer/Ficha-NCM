# resumo_tabelas.py
# ------------------------------------------------------------
# Gera quadros‑resumo de importações e exportações (histórico,
# parciais de 2024 e 2025) e exibe em colunas Streamlit.
# ------------------------------------------------------------

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from babel.numbers import format_decimal
import datetime

# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def formatar_numero(valor):
    if pd.isna(valor):
        return ""
    try:
        return format_decimal(float(valor), "#,##0.##", locale="pt_BR")
    except (ValueError, TypeError):
        return str(valor)

def calcular_variacao(serie: pd.Series) -> list[float]:
    return [np.nan] + [
        ((curr - prev) / prev * 100) if pd.notna(prev) and prev != 0 else np.nan
        for prev, curr in zip(serie[:-1], serie[1:])
    ]

# ------------------------------------------------------------------------
# Função principal para exibição
# ------------------------------------------------------------------------
def exibir_resumos(df_hist_anual, df_2024_parcial, df_2025_parcial, last_updated_month):
    try:
        if df_hist_anual is None or df_hist_anual.empty:
            st.warning("Dados históricos não disponíveis.")
            return

        df_hist = df_hist_anual.copy()
        df_hist.rename(columns={'year': 'Ano'}, inplace=True)
        df_hist['Ano'] = df_hist['Ano'].astype(str)
        ano_atual = datetime.datetime.now().year
        df_hist = df_hist[df_hist['Ano'].astype(int).between(2019, ano_atual - 1)]

        df_2024 = df_2024_parcial.copy() if df_2024_parcial is not None else pd.DataFrame()
        df_2025 = df_2025_parcial.copy() if df_2025_parcial is not None else pd.DataFrame()

        colunas = [
            'Ano',
            'Importações (FOB)', 'Importações (KG)', 'Preço Médio Importação (US$ FOB/KG)',
            'Exportações (FOB)', 'Exportações (KG)', 'Preço Médio Exportação (US$ FOB/KG)'
        ]

        # Renomeia as linhas finais para refletir o mês mais atualizado
        month_map = {
            1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
            7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
        }
        label_mes = month_map.get(last_updated_month, f"até mês {last_updated_month}")

        if not df_2024.empty:
            df_2024['Ano'] = f"2024 (até {label_mes})"
        if not df_2025.empty:
            df_2025['Ano'] = f"2025 (até {label_mes})"

        df_concat = pd.concat([
            df_hist[colunas],
            df_2024[colunas] if not df_2024.empty else pd.DataFrame(columns=colunas),
            df_2025[colunas] if not df_2025.empty else pd.DataFrame(columns=colunas)
        ], ignore_index=True)

        df_concat.rename(columns={
            'Preço Médio Importação (US$ FOB/KG)': 'Preço Médio Importação (US$ FOB/Ton)',
            'Preço Médio Exportação (US$ FOB/KG)': 'Preço Médio Exportação (US$ FOB/Ton)'
        }, inplace=True)

        df_concat['Ano'] = df_concat['Ano'].astype(str)
        df_concat.sort_values(by='Ano', inplace=True)

        df_imp = df_concat[['Ano', 'Importações (FOB)', 'Importações (KG)', 'Preço Médio Importação (US$ FOB/Ton)']].copy()
        df_imp['Var. (%) Imp (US$ FOB)'] = calcular_variacao(df_imp['Importações (FOB)'])
        df_imp['Var. (%) Imp (kg)'] = calcular_variacao(df_imp['Importações (KG)'])
        df_imp['Var. (%) Preço Médio Imp'] = calcular_variacao(df_imp['Preço Médio Importação (US$ FOB/Ton)'])

        df_exp = df_concat[['Ano', 'Exportações (FOB)', 'Exportações (KG)', 'Preço Médio Exportação (US$ FOB/Ton)']].copy()
        df_exp['Var. (%) Exp (US$ FOB)'] = calcular_variacao(df_exp['Exportações (FOB)'])
        df_exp['Var. (%) Exp (kg)'] = calcular_variacao(df_exp['Exportações (KG)'])
        df_exp['Var. (%) Preço Médio Exp'] = calcular_variacao(df_exp['Preço Médio Exportação (US$ FOB/Ton)'])

        df_imp_final = df_imp[[ 
            'Ano', 'Importações (FOB)', 'Var. (%) Imp (US$ FOB)', 'Importações (KG)',
            'Var. (%) Imp (kg)', 'Preço Médio Importação (US$ FOB/Ton)', 'Var. (%) Preço Médio Imp'
        ]]

        df_exp_final = df_exp[[ 
            'Ano', 'Exportações (FOB)', 'Var. (%) Exp (US$ FOB)', 'Exportações (KG)',
            'Var. (%) Exp (kg)', 'Preço Médio Exportação (US$ FOB/Ton)', 'Var. (%) Preço Médio Exp'
        ]]

        df_imp_final = df_imp_final[df_imp_final['Ano'] != '2019']
        df_exp_final = df_exp_final[df_exp_final['Ano'] != '2019']

        for df_final in [df_imp_final, df_exp_final]:
            for col in df_final.columns:
                if 'Var. (%)' in col:
                    df_final[col] = df_final[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) and x != "" else "")
                elif 'Preço Médio' in col:
                    df_final[col] = df_final[col].map(
                        lambda x: f"{x * 1000:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else ""
                    )
                elif df_final[col].dtype == float or df_final[col].dtype == int:
                    df_final[col] = df_final[col].map(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else "")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Quadro Resumo das Importações")
            st.dataframe(df_imp_final.style.set_properties(**{'text-align': 'left'}),
                         use_container_width=True, hide_index=True)

        with col2:
            st.markdown("### 📊 Quadro Resumo das Exportações")
            st.dataframe(df_exp_final.style.set_properties(**{'text-align': 'left'}),
                         use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro ao gerar quadros-resumo: {e}")
