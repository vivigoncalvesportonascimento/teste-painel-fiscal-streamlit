# dashboard/Pagina_Inicial.py
import streamlit as st

# --- Configuração da Página (APENAS AQUI) ---
st.set_page_config(
    page_title="Painel Fiscal - Início",
    page_icon="📊",
    layout="wide"
)

# --- Conteúdo da Página ---
st.title("Painel de Análise Fiscal")
st.write("Bem-vindo(a) ao painel de análise de dados fiscais.")
st.info("⬅️ Utilize o menu na barra lateral para navegar entre as diferentes análises.")

st.header("Sobre")
st.write("""
Este painel foi criado para consolidar e visualizar os principais indicadores:
- **Resultado Fiscal:** Análise da Receita vs. Despesa Empenhada.
- **Resultado Previdenciário:** Análise do resultado previdenciário ao longo dos anos.
""")
