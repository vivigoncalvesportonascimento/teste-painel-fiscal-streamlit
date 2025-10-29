# Este arquivo conterá todas as suas funções "auxiliares" de formatação e estilo.

# dashboard/utils.py
import pandas as pd
import os

# --- Constantes ---
# Define o caminho base para os dados
# ".." significa "subir um nível" (da pasta 'dashboard' para 'painel_fiscal')
# E então ele entra em 'data-raw'
DATA_PATH = os.path.join("..", "data-raw")


# --- Funções de Formatação de Moeda ---

def formatar_brl(valor):
    """Formata um número para o padrão BRL (R$ 1.234,56)."""
    if pd.isna(valor):
        return "N/A"
    formatado = f"{valor:,.2f}"
    # Troca , por . e . por ,
    formatado_br = formatado.replace(",", "temp").replace(
        ".", ",").replace("temp", ".")
    return f"R$ {formatado_br}"


def format_brl_bilhoes(valor):
    """Formata um número em bilhões para o padrão BRL (R$ 1,23)."""
    s = f"{valor:.2f}"  # Formata com 2 casas decimais
    s = s.replace(".", ",")   # Troca ponto por vírgula
    return f"R$ {s}"


# --- Funções de Estilo (para DataFrames) ---

def style_negativo(valor, cor_positivo='black', cor_negativo='red'):
    """Aplica cor vermelha se o valor for negativo."""
    if pd.isna(valor):
        return 'color: gray'
    return f'color: {cor_negativo}' if valor < 0 else f'color: {cor_positivo}'


def style_resultado_fiscal(valor):
    """Aplica azul para positivo e vermelho para negativo."""
    if pd.isna(valor):
        return 'color: gray'
    if valor < 0:
        return 'color: red'
    elif valor > 0:
        return 'color: blue'
    return 'color: black'
