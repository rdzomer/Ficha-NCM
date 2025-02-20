import streamlit as st
import pandas as pd
from modulos.api_comex import obter_data_ultima_atualizacao, obter_descricao_ncm, obter_dados_comerciais, obter_dados_comerciais_ano_anterior
import modulos.processamento as proc

def main():
    st.title("📊 Análise de Comércio Exterior")

    # 📅 Obter data da última atualização
    last_updated_date, last_updated_year, last_updated_month = obter_data_ultima_atualizacao()

    if last_updated_date:
        st.info(f"📅 **Dados atualizados até: {last_updated_month}/{last_updated_year}** ({last_updated_date})")
    else:
        st.error("❌ Não foi possível obter a data da última atualização da API.")

    # ✍ Entrada do usuário para inserir código NCM
    ncm_code = st.text_input("Digite o código NCM:", "")

    if ncm_code:
        st.write(f"📌 **Código NCM selecionado:** {ncm_code}")

        # 📖 Buscar a descrição do NCM
        descricao = obter_descricao_ncm(ncm_code)
        if "Erro" in descricao:
            st.error(descricao)
            return
        else:
            st.success(f"📖 Descrição do NCM: **{descricao}**")

        # 🔹 Buscar os dados de exportação e importação de 2025
        dados_export_2025, erro_export = obter_dados_comerciais(ncm_code, "export")
        if erro_export:
            st.error(erro_export)
            return

        dados_import_2025, erro_import = obter_dados_comerciais(ncm_code, "import")
        if erro_import:
            st.error(erro_import)
            return
        
        df_2025, error_2025 = proc.processar_dados_export_import(dados_export_2025, dados_import_2025, last_updated_month)

        # 🔹 Buscar os dados de 2024 até o último mês atualizado
        dados_export_2024, erro_export_2024 = obter_dados_comerciais_ano_anterior(ncm_code, "export", last_updated_month)
        if erro_export_2024:
            st.error(erro_export_2024)
            return

        dados_import_2024, erro_import_2024 = obter_dados_comerciais_ano_anterior(ncm_code, "import", last_updated_month)
        if erro_import_2024:
            st.error(erro_import_2024)
            return

        df_2024, error_2024 = proc.processar_dados_ano_anterior(dados_export_2024, dados_import_2024, last_updated_month)

        # Exibir os resultados no Streamlit
        st.subheader("📊 Dados de 2025")
        if error_2025:
            st.warning(error_2025)
        else:
            st.dataframe(df_2025)

        st.subheader(f"📊 Dados de 2024 (Até {last_updated_month}/2024)")
        if error_2024:
            st.warning(error_2024)
        else:
            st.dataframe(df_2024)

if __name__ == "__main__":
    main()






