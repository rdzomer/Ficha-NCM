#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para processamento de dados de importação/exportação.
"""

import pandas as pd

def processar_dados_export_import(dados_export, dados_import, last_updated_month):
    """
    Processa os dados de importação e exportação e retorna um DataFrame consolidado.
    
    Args:
        dados_export (list): Dados de exportação da API.
        dados_import (list): Dados de importação da API.
        last_updated_month (str): Último mês disponível para dados.

    Returns:
        pd.DataFrame: DataFrame consolidado com os dados processados.
    """
    df_export = pd.DataFrame(dados_export)
    df_import = pd.DataFrame(dados_import)

    # Fusão dos datasets
    df = pd.merge(df_export, df_import, on="year", suffixes=("_EXP", "_IMP"))
    
    return df


def processar_dados_ano_anterior(dados_export, dados_import, last_updated_month):
    """Processa dados do ano anterior."""
    df_export = pd.DataFrame(dados_export)
    df_import = pd.DataFrame(dados_import)
    df = pd.merge(df_export, df_import, on="year", suffixes=("_EXP", "_IMP"))
    return df

def processar_dados_ano_atual(dados_export, dados_import, last_updated_month):
    """Processa dados do ano atual."""
    df_export = pd.DataFrame(dados_export)
    df_import = pd.DataFrame(dados_import)
    df = pd.merge(df_export, df_import, on="year", suffixes=("_EXP", "_IMP"))
    return df
