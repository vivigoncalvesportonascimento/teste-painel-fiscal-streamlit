# dashboard/pages/2_Resultado_Previdenciario.py
import streamlit as st
import pandas as pd
import altair as alt

# Importa as funções "gerais" que criamos
from data_loader import carregar_dados_previdenciario
from utils import format_brl_bilhoes, formatar_brl, style_negativo

# --- Título da Página ---
st.title("Resultado Previdenciário")

# --- Carregar Dados ---
df_previdenciario = carregar_dados_previdenciario()

if df_previdenciario.empty:
    st.error("Não foi possível carregar os dados. Verifique a mensagem de erro acima.")
    st.stop()

# --- Lógica da Página (Filtros e Gráficos) ---
try:
    ano_min = int(df_previdenciario['Ano'].min())
    ano_max = int(df_previdenciario['Ano'].max())
except ValueError:
    st.error("Não foi possível determinar o intervalo de anos. Verifique os dados.")
    st.stop()

anos_selecionados = st.slider(
    'Selecione o Período:',
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    key='slider_previdenciario'
)

# --- Filtrar Dados ---
mask = (
    (df_previdenciario['Ano'] >= anos_selecionados[0]) &
    (df_previdenciario['Ano'] <= anos_selecionados[1])
)
df_plot = df_previdenciario[mask].copy()

if df_plot.empty:
    st.warning("Nenhum dado disponível para o período selecionado.")
    st.stop()

# --- Preparação dos dados para o gráfico ---
df_plot['Valor_Bilhoes'] = df_plot['Valor'] / 1_000_000_000
# Usa a função do utils.py
df_plot['Label_Valor'] = df_plot['Valor_Bilhoes'].apply(format_brl_bilhoes)

# --- Gráfico ---
bars = alt.Chart(df_plot).mark_bar().encode(
    x=alt.X('Ano:O', title='Ano'),
    y=alt.Y('Valor_Bilhoes:Q', title='Valor (R$ Bilhões)'),
    color=alt.condition(
        alt.datum.Valor_Bilhoes > 0,
        alt.value('#001B44'),
        alt.value('#FFA07A')
    ),
    tooltip=[
        alt.Tooltip('Ano:O', title='Ano'),
        alt.Tooltip('Label_Valor:N', title='Valor')
    ]
)

text_labels = alt.Chart(df_plot).mark_text(
    align='center', baseline='top', dy=5
).encode(
    x=alt.X('Ano:O'),
    y=alt.Y('Valor_Bilhoes:Q'),
    text=alt.Text('Label_Valor:N'),
    color=alt.value('black')
)

chart = (bars + text_labels).properties(
    title=f"Resultado Previdenciário ({anos_selecionados[0]} - {anos_selecionados[1]})",
    height=500
).interactive()

st.altair_chart(chart, use_container_width=True)

# --- Tabela detalhada ---
with st.expander("Ver dados detalhados"):
    df_tabela = df_plot[['Ano', 'Valor']].copy()
    df_tabela.rename(
        columns={'Valor': 'Resultado Previdenciario Total'}, inplace=True)
    df_tabela = df_tabela.sort_values(by='Ano', ascending=False)

    st.dataframe(
        df_tabela.style
        # Usa a função do utils.py
        # <-- CORRIGIDO
        .map(style_negativo, subset=['Resultado Previdenciario Total'])
        .format({
            'Resultado Previdenciario Total': formatar_brl  # Usa a função do utils.py
        }),
        hide_index=True,
        width='stretch'  # <-- CORRIGIDO
    )
