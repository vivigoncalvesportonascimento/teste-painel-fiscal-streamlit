# Este arquivo centraliza todo o carregamento e manipulação inicial de dados. Usar o @st.cache_data aqui é perfeito.
# dashboard/data_loader.py
import streamlit as st
import pandas as pd
import os
from utils import DATA_PATH  # Importa a constante do nosso outro módulo


@st.cache_data
def carregar_dados_fiscal():
    """Carrega e prepara os dados do Resultado Fiscal."""
    path_receita = os.path.join(DATA_PATH, "receita.csv")
    path_despesa = os.path.join(DATA_PATH, "despesa.csv")

    try:
        # --- Lógica de limpeza do 'receita.csv' ---
        def clean_numeric_brl(value_str):
            if isinstance(value_str, str):
                value_str = value_str.strip('"').replace(
                    '.', '').replace(',', '.')
                return pd.to_numeric(value_str, errors='coerce')
            return pd.NaT

        df_receita_raw = pd.read_csv(
            path_receita, encoding='utf-8', header=None, skiprows=1)
        split_data = df_receita_raw[0].str.split(',', n=1, expand=True)
        split_rest = split_data[1].str.strip('"').str.split('","', expand=True)

        df_receita = pd.DataFrame()
        df_receita['Ano de Exercício'] = pd.to_numeric(split_data[0])
        df_receita['Valor Efetivado Ajustado'] = split_rest[1].apply(
            clean_numeric_brl)

        # --- Carregar Despesa ---
        df_despesa = pd.read_csv(
            path_despesa, encoding='latin1', sep=';', decimal=',', thousands='.')

        # --- Merge e Cálculo ---
        df = pd.merge(
            df_receita[['Ano de Exercício', 'Valor Efetivado Ajustado']],
            df_despesa[['Ano de Exercício', 'Valor Despesa Empenhada']],
            on='Ano de Exercício', how='inner'
        )
        df.rename(columns={
            'Valor Efetivado Ajustado': 'Receita Fiscal',
            'Valor Despesa Empenhada': 'Despesa Fiscal'
        }, inplace=True)

        df['Resultado Fiscal'] = df['Receita Fiscal'] - df['Despesa Fiscal']

        df['Ano de Exercício'] = df['Ano de Exercício'].astype(int)

        return df

    except FileNotFoundError as e:
        st.error(f"Arquivo não encontrado: {e.filename}.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos fiscais: {e}")
        return None


@st.cache_data
def carregar_dados_previdenciario():
    """Carrega, limpa e transforma os dados do resultado previdenciário."""
    caminho_arquivo = os.path.join(DATA_PATH, "resultado_previdenciario.csv")
    try:
        df = pd.read_csv(
            caminho_arquivo,
            encoding='latin1', sep=';', decimal=',', thousands='.'
        )
        df = df.dropna(how='all')

        if df.empty:
            st.error("O arquivo CSV previdenciário está vazio.")
            return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])

        df_melted = df.melt(
            id_vars=['Descrição'], var_name='Ano', value_name='Valor')

        try:
            df_melted['Ano'] = df_melted['Ano'].astype(int)
        except ValueError as e:
            st.error(
                f"Erro ao converter a coluna 'Ano' para número: {e}. Verifique o cabeçalho do CSV.")
            return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])

        df_melted['Valor'] = pd.to_numeric(df_melted['Valor'], errors='coerce')
        df_melted = df_melted.dropna(subset=['Valor'])

        return df_melted

    except FileNotFoundError as e:
        st.error(f"Arquivo não encontrado: {e.filename}.")
        return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])
    except Exception as e:
        st.error(
            f"Erro ao carregar ou processar o arquivo CSV previdenciário: {e}")
        return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])
