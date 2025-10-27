import streamlit as st
import pandas as pd
import altair as alt

# --- Configuração da Página ---
st.set_page_config(page_title="Resultado Previdenciário", layout="wide")

# --- Título da Aplicação ---
st.title("Resultado Previdenciário")

# --- Caminho do Arquivo ---
FILE_PREVIDENCIARIO = "data-raw/resultado_previdenciario.csv"


@st.cache_data
def carregar_dados_previdenciario(caminho_arquivo):
    """Carrega, limpa e transforma os dados do resultado previdenciário."""
    try:
        df = pd.read_csv(
            caminho_arquivo,
            encoding='latin1',
            sep=';',
            decimal=',',
            thousands='.'
        )

        df = df.dropna(how='all')

        if df.empty:
            st.error("O arquivo CSV está vazio ou não contém dados válidos.")
            return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])

        df_melted = df.melt(
            id_vars=['Descrição'],
            var_name='Ano',
            value_name='Valor'
        )

        try:
            df_melted['Ano'] = df_melted['Ano'].astype(int)
        except ValueError as e:
            st.error(
                f"Erro ao converter a coluna 'Ano' para número: {e}. Verifique o cabeçalho do CSV.")
            return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])

        df_melted['Valor'] = pd.to_numeric(df_melted['Valor'], errors='coerce')
        df_melted = df_melted.dropna(subset=['Valor'])

        return df_melted

    except FileNotFoundError:
        st.error(
            f"Erro: Arquivo não encontrado em '{caminho_arquivo}'. Verifique o nome e o local do arquivo.")
        return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo CSV: {e}")
        return pd.DataFrame(columns=['Descrição', 'Ano', 'Valor'])


# --- Carregar Dados ---
df_previdenciario = carregar_dados_previdenciario(FILE_PREVIDENCIARIO)

if df_previdenciario.empty:
    st.error("Não foi possível carregar os dados. Verifique a mensagem de erro acima.")
    st.stop()

# --- Filtros ---


try:
    ano_min = int(df_previdenciario['Ano'].min())
    ano_max = int(df_previdenciario['Ano'].max())
except ValueError:
    st.error("Não foi possível determinar o intervalo de anos. Verifique os dados.")
    st.stop()

# Filtro movido de st.sidebar.slider para st.slider
anos_selecionados = st.slider(
    'Selecione o Período:',
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    key='slider_previdenciario'  # Chave única
)

# --- Filtrar Dados com base no Slider ---
if not anos_selecionados:
    st.warning("Por favor, selecione um intervalo de anos.")
    st.stop()

mask = (
    (df_previdenciario['Ano'] >= anos_selecionados[0]) &
    (df_previdenciario['Ano'] <= anos_selecionados[1])
)
df_plot = df_previdenciario[mask].copy()

if df_plot.empty:
    st.warning("Nenhum dado disponível para o período selecionado.")
    st.stop()

# --- Preparação dos dados para o gráfico ---

# Calcular valores em BILHÕES
df_plot['Valor_Bilhoes'] = df_plot['Valor'] / 1_000_000_000

# Criar a string de rótulo formatada (para o gráfico)


def format_brl_bilhoes(valor):
    s = f"{valor:.2f}"  # Formata com 2 casas decimais
    s = s.replace(".", ",")   # Troca ponto por vírgula
    return f"R$ {s}"


df_plot['Label_Valor'] = df_plot['Valor_Bilhoes'].apply(format_brl_bilhoes)

# --- (INÍCIO DA ALTERAÇÃO) Funções de formatação para a tabela ---

# Função para formatar R$ (para a tabela)


def formatar_brl_total(valor):
    if pd.isna(valor):
        return "N/A"
    # Formato com separador de milhar (.) e decimal (,)
    formatado = f"{valor:,.2f}"
    # Troca , por . e . por ,
    formatado_br = formatado.replace(",", "temp").replace(
        ".", ",").replace("temp", ".")
    return f"R$ {formatado_br}"

# Função para colorir negativos (para a tabela)


def colorir_negativo(valor):
    if pd.isna(valor):
        return 'color: gray'
    return 'color: red' if valor < 0 else 'color: black'

# --- (FIM DA ALTERAÇÃO) ---


# --- Criar gráfico de barras com rótulos ---

# Camada de Barras
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

# Camada de Rótulos de Texto
text_labels = alt.Chart(df_plot).mark_text(
    align='center',
    baseline='top',
    dy=5
).encode(
    x=alt.X('Ano:O'),
    y=alt.Y('Valor_Bilhoes:Q'),
    text=alt.Text('Label_Valor:N'),
    color=alt.value('black')
)

# Combinar gráficos
chart = (bars + text_labels).properties(
    title=f"Resultado Previdenciário ({anos_selecionados[0]} - {anos_selecionados[1]})",
    height=500
).interactive()

st.altair_chart(chart, use_container_width=True)

# --- (INÍCIO DA ALTERAÇÃO) Exibir dados brutos formatados ---
with st.expander("Ver dados detalhados"):

    # 1. Selecionar e renomear colunas
    df_tabela = df_plot[['Ano', 'Valor']].copy()
    # Assume que a 'Descrição' é sempre a mesma, conforme o CSV
    df_tabela.rename(
        columns={'Valor': 'Resultado Previdenciario Total'}, inplace=True)
    df_tabela = df_tabela.sort_values(by='Ano', ascending=False)

    # 2. Aplicar estilos e formatação
    st.dataframe(
        df_tabela.style
        .applymap(colorir_negativo, subset=['Resultado Previdenciario Total'])
        .format({
            'Resultado Previdenciario Total': formatar_brl_total
        }),
        hide_index=True,  # Oculta o índice lateral
        use_container_width=True
    )
# --- (FIM DA ALTERAÇÃO) ---
