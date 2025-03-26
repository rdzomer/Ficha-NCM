#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Funções para leitura e processamento da planilha Excel.
"""

import pandas as pd
import streamlit as st

def buscar_informacoes_ncm_completo(ncm_code, file_excel):
    """
    Busca informações detalhadas da planilha Excel com base no código NCM.
    
    Parte 1: Aba "NCMs-CGIM-DINTE"
        - Retorna: 'Departamento Responsável', 'Coordenação-Geral Responsável', 
                   'Agrupamento', 'Setores', 'Subsetores', 'Produtos'
         
    Parte 2: Abas de Entidades (ABITAM, IABR, ABAL, etc.)
        - Retorna colunas T:AE (Sigla Entidade, Entidade, Nome do Dirigente, etc.)
        - Se o NCM aparecer em várias abas, retorna em linhas distintas.
    """
    try:
        # --- Parte 1: Aba "NCMs-CGIM-DINTE" ---
        df_cgim = pd.read_excel(file_excel, sheet_name="NCMs-CGIM-DINTE")
        df_cgim['NCM'] = df_cgim['NCM'].astype(str)
        resultado_ncm = df_cgim[df_cgim['NCM'] == str(ncm_code)]
        
        if not resultado_ncm.empty:
            resultado_ncm = resultado_ncm[[
                'Departamento Responsável', 
                'Coordenação-Geral Responsável', 
                'Agrupamento', 
                'Setores', 
                'Subsetores', 
                'Produtos'
            ]]
        else:
            resultado_ncm = "🔹 Produto não encontrado na aba 'NCMs-CGIM-DINTE'."
        
        # --- Parte 2: Outras abas de entidades ---
        abas_entidades = ["ABITAM", "IABR", "ABAL", "ABCOBRE", "ABRAFE", "IBÁ", "SICETEL", "SINDIFER"]
        lista_resultados = []
        
        for aba in abas_entidades:
            try:
                # Lê a coluna A (NCM) e as colunas T:AE
                df_aba = pd.read_excel(file_excel, sheet_name=aba, usecols="A,T:AE")
                df_aba['NCM'] = df_aba['NCM'].astype(str)
                df_filtrado = df_aba[df_aba['NCM'] == str(ncm_code)]
                
                if not df_filtrado.empty:
                    df_filtrado = df_filtrado.copy()
                    df_filtrado.loc[:, "Aba"] = aba  # Adiciona a origem
                    lista_resultados.append(df_filtrado)
            except Exception as e:
                print(f"⚠️ Erro ao ler aba '{aba}': {e}")  # Log em caso de problema
        
        if lista_resultados:
            resultado_entidades = pd.concat(lista_resultados, ignore_index=True)
        else:
            resultado_entidades = "🔹 Nenhuma informação encontrada nas abas de entidades."
        
        return resultado_ncm, resultado_entidades

    except Exception as error:
        st.error(f"Erro ao processar a planilha: {error}")
        return pd.DataFrame(), pd.DataFrame()  # Retorna DataFrames vazios em caso de erro


