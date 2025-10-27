import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Configuração da Página ---
st.set_page_config(page_title="Resultado Fiscal", layout="wide")

# --- Título da Aplicação ---
st.title("Resultado Fiscal")

# --- Caminhos dos Arquivos ---
FILE_RECEITA = "data-raw/receita.csv"
FILE_DESPESA = "data-raw/despesa.csv"


@st.cache_data
def carregar_dados(path_receita, path_despesa):
    """Carrega e prepara os dados."""
    try:
        # --- (INÍCIO DA ALTERAÇÃO) ---
        # O novo arquivo 'receita.csv' está malformado.
        # Precisamos carregá-lo manualmente, limpando as strings.

        # Função auxiliar para limpar os números (ex: "20.433.680.479,00")
        def clean_numeric_brl(value_str):
            if isinstance(value_str, str):
                # Remover aspas extras se houver
                value_str = value_str.strip('"')
                value_str = value_str.replace('.', '')  # Tira milhares
                value_str = value_str.replace(',', '.')  # Troca decimal
                return pd.to_numeric(value_str, errors='coerce')
            return pd.NaT

        # 1. Ler o 'receita.csv' pulando o cabeçalho quebrado
        df_receita_raw = pd.read_csv(
            path_receita,
            encoding='utf-8',  # Corrigido para utf-8
            header=None,       # Ignorar cabeçalho do arquivo
            skiprows=1         # Pular linha 0 (cabeçalho quebrado)
        )

        # 2. A coluna 0 contém a string (ex: 2002,"...","...")
        # Separar o ano (que não tem aspas) do resto
        split_data = df_receita_raw[0].str.split(',', n=1, expand=True)

        # 3. Separar o resto (que tem aspas)
        # A string em split_data[1] é ex: '"VALOR1","VALOR2"'
        # Remover aspas das pontas (strip('"')) e dividir por '","'
        split_rest = split_data[1].str.strip('"').str.split('","', expand=True)

        # 4. Montar o DataFrame limpo
        df_receita = pd.DataFrame()
        df_receita['Ano de Exercício'] = pd.to_numeric(split_data[0])
        # A coluna [0] do split_rest é "Valor Previsto Inicial"
        # A coluna [1] do split_rest é "Valor Efetivado Ajustado"
        df_receita['Valor Efetivado Ajustado'] = split_rest[1].apply(
            clean_numeric_brl)

        # --- (FIM DA ALTERAÇÃO) ---

        # --- Carregar Despesa (Lógica antiga mantida) ---
        df_despesa = pd.read_csv(
            path_despesa, encoding='latin1', sep=';', decimal=',', thousands='.')
        # --- Fim ---

        # Colunas necessárias
        colunas_receita_necessarias = [
            'Ano de Exercício', 'Valor Efetivado Ajustado']
        colunas_despesa_necessarias = [
            'Ano de Exercício', 'Valor Despesa Empenhada']

        # Assegurar tipos (já feito na limpeza da receita, mas vamos garantir)
        df_receita['Ano de Exercício'] = df_receita['Ano de Exercício'].astype(
            int)
        df_despesa['Ano de Exercício'] = df_despesa['Ano de Exercício'].astype(
            int)

        df_receita['Valor Efetivado Ajustado'] = pd.to_numeric(
            df_receita['Valor Efetivado Ajustado'], errors='coerce')
        df_despesa['Valor Despesa Empenhada'] = pd.to_numeric(
            df_despesa['Valor Despesa Empenhada'], errors='coerce')

        # Pegar apenas as colunas que importam
        df_receita = df_receita[colunas_receita_necessarias].copy()
        df_despesa = df_despesa[colunas_despesa_necessarias].copy()

        # Merge (Lógica antiga mantida)
        df = pd.merge(df_receita, df_despesa,
                      on='Ano de Exercício', how='inner')

        df.rename(columns={
            'Valor Efetivado Ajustado': 'Receita Fiscal',
            'Valor Despesa Empenhada': 'Despesa Fiscal'
        }, inplace=True)

        df['Resultado Fiscal'] = df['Receita Fiscal'] - df['Despesa Fiscal']

        return df

    except FileNotFoundError as e:
        st.error(f"Arquivo não encontrado: {e.filename}.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos: {e}")
        return None


# --- Função para formatar ---
def formatar_milhoes_brl(valor):
    if pd.isna(valor):
        return ""
    formatado = f"{valor:,.2f}"
    return formatado.replace(",", "temp").replace(".", ",").replace("temp", ".")


# --- Carregar dados ---
df_completo = carregar_dados(FILE_RECEITA, FILE_DESPESA)

if df_completo is not None and not df_completo.empty:

    # --- FILTRO DE ANOS (Linha do tempo) ---

    ano_min = int(df_completo['Ano de Exercício'].min())
    ano_max = int(df_completo['Ano de Exercício'].max())

    # Selecinar o Ano (slider)
    anos_selecionados = st.slider(
        "Escolha o intervalo de anos para análise:",
        min_value=ano_min,
        max_value=ano_max,
        value=(2014, ano_max),
        step=1,
        key='slider_fiscal'
    )

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
    df_plot['label_texto'] = df_plot['Resultado (Milhões)'].apply(
        formatar_milhoes_brl)
    df_plot['cor_fundo'] = df_plot['Resultado (Milhões)'].apply(
        lambda x: '#001B44' if x > 0 else '#660000')
    df_plot['Métrica'] = 'Resultado Fiscal'

    # --- Base do gráfico ---
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

    # --- Camadas do gráfico ---
    line_e_points = base_chart.mark_line(color='black', point=True).encode(
        y=alt.Y('Resultado (Milhões):Q', axis=alt.Axis(
            title='Resultado (R$ Milhões)'))
    )

    # Fundo colorido atrás dos rótulos
    label_background = base_chart.mark_rect(
        height=22,
        width=60,
        cornerRadius=6,
        opacity=0.9
    ).encode(
        y=alt.Y('Resultado (Milhões):Q'),
        yOffset=alt.Y('label_offset:Q'),
        color=alt.Color('cor_fundo:N', scale=None)
    )

    # Texto do rótulo
    text_labels = base_chart.mark_text(
        align='center',
        baseline='middle',
        fontSize=12,
        color='white',
        fontWeight='bold'
    ).encode(
        y=alt.Y('Resultado (Milhões):Q'),
        text=alt.Text('label_texto:N'),
        yOffset=alt.Y('label_offset:Q')
    )

    # Camadas combinadas
    chart_resultado = alt.layer(line_e_points, label_background, text_labels)

    final_chart = chart_resultado.properties(
        title=f"Resultado Fiscal ({anos_selecionados[0]} - {anos_selecionados[1]})",
        height=500
    ).interactive()

    st.altair_chart(final_chart, use_container_width=True)

    # --- Tabela detalhada ---
    def formatar_brl(valor):
        if pd.isna(valor):
            return "N/A"
        formatado = f"{valor:,.2f}"
        return f"R$ {formatado.replace(',', 'temp').replace('.', ',').replace('temp', '.')}"

    def colorir_resultado(valor):
        if pd.isna(valor):
            return 'color: gray'
        if valor < 0:
            return 'color: red'
        elif valor > 0:
            return 'color: blue'
        return 'color: black'

    df_tabela = df_plot[['Ano de Exercício', 'Receita Fiscal',
                         'Despesa Fiscal', 'Resultado Fiscal']].set_index('Ano de Exercício')
    df_tabela = df_tabela.sort_index(ascending=False)

    with st.expander("Ver dados detalhados"):
        st.dataframe(
            df_tabela.style
            .map(colorir_resultado, subset=['Resultado Fiscal'])
            .format(formatar_brl),
            use_container_width=True
        )

else:
    st.error(
        "Não foi possível gerar o gráfico. Verifique os erros de carregamento acima.")
