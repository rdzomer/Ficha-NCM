import pandas as pd
import numpy as np
import streamlit as st

def exibir_resumos(df_hist_anual, df_2024_parcial, df_2025_parcial):
    try:
        if df_hist_anual is None or df_hist_anual.empty:
            st.warning("Dados históricos não disponíveis.")
            return

        df_hist = df_hist_anual.copy()
        df_hist.rename(columns={'year': 'Ano'}, inplace=True)
        df_hist['Ano'] = df_hist['Ano'].astype(str)

        df_hist = df_hist[df_hist['Ano'].astype(int) >= 2019]

        if df_2024_parcial is not None and not df_2024_parcial.empty:
            df_2024 = df_2024_parcial.copy()
            mes_atual_2024 = int(df_2024['month'].iloc[0]) if 'month' in df_2024.columns else 3
            df_2024['Ano'] = f"2024 (Até mês {mes_atual_2024:02d})"
        else:
            df_2024 = pd.DataFrame()

        if df_2025_parcial is not None and not df_2025_parcial.empty:
            df_2025 = df_2025_parcial.copy()
            mes_atual_2025 = int(df_2025['month'].iloc[0]) if 'month' in df_2025.columns else 3
            df_2025['Ano'] = f"2025 (Até mês {mes_atual_2025:02d})"
        else:
            df_2025 = pd.DataFrame()

        colunas = [
            'Ano',
            'Importações (FOB)', 'Importações (KG)', 'Preço Médio Importação (US$ FOB/KG)',
            'Exportações (FOB)', 'Exportações (KG)', 'Preço Médio Exportação (US$ FOB/KG)'
        ]

        df_concat = pd.concat([
            df_hist[colunas],
            df_2024[colunas] if not df_2024.empty else pd.DataFrame(columns=colunas),
            df_2025[colunas] if not df_2025.empty else pd.DataFrame(columns=colunas)
        ], ignore_index=True)

        ordem_exibicao = ['2019', '2020', '2021', '2022', '2023', '2024',
                          f"2024 (Até mês {mes_atual_2024:02d})", f"2025 (Até mês {mes_atual_2025:02d})"]

        df_concat = df_concat[df_concat['Ano'].isin(ordem_exibicao)]
        df_concat['Ano'] = pd.Categorical(df_concat['Ano'], categories=ordem_exibicao, ordered=True)
        df_concat.sort_values(by='Ano', inplace=True)

        def calcular_variacao(col):
            variacoes = [np.nan] + [
                ((curr - prev) / prev * 100) if pd.notna(prev) and prev != 0 else np.nan
                for prev, curr in zip(col[:-1], col[1:])
            ]
            return variacoes

        df_imp = df_concat[['Ano', 'Importações (FOB)', 'Importações (KG)', 'Preço Médio Importação (US$ FOB/KG)']].copy()
        df_imp['Var. (%) Imp (US$ FOB)'] = calcular_variacao(df_imp['Importações (FOB)'])
        df_imp['Var. (%) Imp (kg)'] = calcular_variacao(df_imp['Importações (KG)'])
        df_imp['Var. (%) Preço Médio Imp'] = calcular_variacao(df_imp['Preço Médio Importação (US$ FOB/KG)'])

        df_exp = df_concat[['Ano', 'Exportações (FOB)', 'Exportações (KG)', 'Preço Médio Exportação (US$ FOB/KG)']].copy()
        df_exp['Var. (%) Exp (US$ FOB)'] = calcular_variacao(df_exp['Exportações (FOB)'])
        df_exp['Var. (%) Exp (kg)'] = calcular_variacao(df_exp['Exportações (KG)'])
        df_exp['Var. (%) Preço Médio Exp'] = calcular_variacao(df_exp['Preço Médio Exportação (US$ FOB/KG)'])

        df_imp_final = df_imp[[
            'Ano', 'Importações (FOB)', 'Var. (%) Imp (US$ FOB)', 'Importações (KG)',
            'Var. (%) Imp (kg)', 'Preço Médio Importação (US$ FOB/KG)', 'Var. (%) Preço Médio Imp'
        ]]

        df_exp_final = df_exp[[
            'Ano', 'Exportações (FOB)', 'Var. (%) Exp (US$ FOB)', 'Exportações (KG)',
            'Var. (%) Exp (kg)', 'Preço Médio Exportação (US$ FOB/KG)', 'Var. (%) Preço Médio Exp'
        ]]

        df_imp_final = df_imp_final[df_imp_final['Ano'] != '2019']
        df_exp_final = df_exp_final[df_exp_final['Ano'] != '2019']

        for df_final in [df_imp_final, df_exp_final]:
            for col in df_final.columns:
                if 'Var. (%)' in col:
                    df_final[col] = df_final[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) and x != "" else "")
                elif df_final[col].dtype == float or df_final[col].dtype == int:
                    df_final[col] = df_final[col].map(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else "")

            df_final.loc[df_final['Ano'].str.contains("2024 \(Até mês"), [col for col in df_final.columns if 'Var. (%)' in col]] = ""

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
