# dashboard/pages/1_Resultado_Fiscal.py
import streamlit as st
import pandas as pd
import altair as alt

# Importa as funções "gerais" que criamos
from data_loader import carregar_dados_fiscal
from utils import formatar_brl, style_resultado_fiscal, format_brl_bilhoes

# --- Título da Página ---
st.title("Resultado Fiscal")

# --- Carregar dados (agora vem do módulo) ---
df_completo = carregar_dados_fiscal()

if df_completo is None or df_completo.empty:
    st.error("Não foi possível carregar os dados. Verifique os logs no console.")
    st.stop()


# --- Lógica da Página (Filtros e Gráficos) ---
try:
    ano_min = int(df_completo['Ano de Exercício'].min())
    ano_max = int(df_completo['Ano de Exercício'].max())

    anos_selecionados = st.slider(
        "Escolha o intervalo de anos para análise:",
        min_value=ano_min,
        max_value=ano_max,
        value=(2014, ano_max),  # Valor padrão
        step=1,
        key='slider_fiscal'
    )
except Exception as e:
    st.error(f"Erro ao configurar o filtro de anos: {e}")
    st.stop()


# Filtra os dados pelo período selecionado
df_plot = df_completo[
    (df_completo['Ano de Exercício'] >= anos_selecionados[0]) &
    (df_completo['Ano de Exercício'] <= anos_selecionados[1])
].copy()

if df_plot.empty:
    st.warning("Nenhum dado disponível para o período selecionado.")
    st.stop()

# --- Preparação dos dados para o gráfico ---
df_plot['Resultado (Milhões)'] = df_plot['Resultado Fiscal'] / 1_000_000
df_plot['label_offset'] = df_plot['Resultado (Milhões)'].apply(
    lambda x: -15 if x > 0 else 15)
# Reutiliza a função de formatação do utils.py
df_plot['label_texto'] = (df_plot['Resultado (Milhões)'] /
                          # Exemplo se quisesse Bilhões
                          1000).apply(format_brl_bilhoes)
df_plot['label_texto'] = df_plot['Resultado (Milhões)'].apply(
    lambda x: f"{x:,.2f}".replace(",", "temp").replace(".", ",").replace("temp", "."))


df_plot['cor_fundo'] = df_plot['Resultado (Milhões)'].apply(
    lambda x: '#001B44' if x > 0 else '#660000')
df_plot['Métrica'] = 'Resultado Fiscal'

# --- Gráfico ---
base_chart = alt.Chart(df_plot).encode(
    x=alt.X('Ano de Exercício:O', axis=alt.Axis(
        format='d', title='Ano de Exercício')),
    tooltip=[
        alt.Tooltip('Ano de Exercício', format='d'),
        'Métrica',
        alt.Tooltip('Resultado (Milhões):Q',
                    format=',.2f', title='Valor (Milhões)')
    ]
)

line_e_points = base_chart.mark_line(color='black', point=True).encode(
    y=alt.Y('Resultado (Milhões):Q', axis=alt.Axis(
        title='Resultado (R$ Milhões)'))
)

label_background = base_chart.mark_rect(
    height=22, width=60, cornerRadius=6, opacity=0.9
).encode(
    y=alt.Y('Resultado (Milhões):Q'),
    yOffset=alt.Y('label_offset:Q'),
    color=alt.Color('cor_fundo:N', scale=None)
)

text_labels = base_chart.mark_text(
    align='center', baseline='middle', fontSize=12,
    color='white', fontWeight='bold'
).encode(
    y=alt.Y('Resultado (Milhões):Q'),
    text=alt.Text('label_texto:N'),
    yOffset=alt.Y('label_offset:Q')
)

final_chart = alt.layer(line_e_points, label_background, text_labels).properties(
    title=f"Resultado Fiscal ({anos_selecionados[0]} - {anos_selecionados[1]})",
    height=500
).interactive()

st.altair_chart(final_chart, use_container_width=True)

# --- Tabela detalhada ---
df_tabela = df_plot[['Ano de Exercício', 'Receita Fiscal',
                     'Despesa Fiscal', 'Resultado Fiscal']].set_index('Ano de Exercício')
df_tabela = df_tabela.sort_index(ascending=False)

with st.expander("Ver dados detalhados"):
    st.dataframe(
        df_tabela.style
        # Usa a função do utils.py
        .map(style_resultado_fiscal, subset=['Resultado Fiscal'])
        .format(formatar_brl),  # Usa a função do utils.py
        width='stretch'  # <-- CORRIGIDO
    )
