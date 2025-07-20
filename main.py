import streamlit as st
import pandas as pd
import altair as alt
from unidecode import unidecode
from thefuzz import process

planilha_de_reclamacoes = "data/2025/RR.xlsx"
vendas_das_lojas = "data/2025/vendas.json"

#NEEDS TO REVIEW DATA QUERY

@st.cache_data
def getExcelData():
    dataFrame = pd.read_excel(planilha_de_reclamacoes, sheet_name="JUN")
    dataFrame.dropna(how='all', inplace=True)
    return dataFrame

@st.cache_data
def getJsonData():
    dataFrame = pd.read_json(vendas_das_lojas)
    dataFrame['trade_name'] = dataFrame['trade_name'].str.replace('Forneria Original - ', '', regex=False)
    dataFrame = dataFrame.iloc[:-1]
    return dataFrame

# Load data
reclamacoesDataFrame = getExcelData()
vendasDataFrame = getJsonData()

# Normalize function
def normalize(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = unidecode(text)  # Remove accents
    text = ''.join(e for e in text if e.isalnum())  # Keep only alphanumeric
    return text

# Normalize store names
vendasDataFrame["store_key"] = vendasDataFrame["trade_name"].apply(normalize)
reclamacoesDataFrame["store_key"] = reclamacoesDataFrame["Nome da Unidade"].apply(normalize)

# Match vendas keys to best keys from reclamações
keys_reclamacoes = reclamacoesDataFrame["store_key"].unique().tolist()

def best_match(key):
    match, score = process.extractOne(key, keys_reclamacoes)
    return match if score > 80 else None  # Adjust threshold if needed

vendasDataFrame["matched_key"] = vendasDataFrame["store_key"].apply(best_match)

# Sidebar selectbox
st.sidebar.header("Sidebar")
with st.sidebar:
    nomeDaUnidade = st.selectbox(
        "Escolha a unidade",
        vendasDataFrame["trade_name"].unique()
    )

# Normalize selection for filtering
selected_key = normalize(nomeDaUnidade)

# Filter data
vendas_loja = vendasDataFrame[vendasDataFrame["store_key"] == selected_key]
if not vendas_loja.empty:
    matched_key = vendas_loja["matched_key"].iloc[0]
    reclamacoes_loja = reclamacoesDataFrame[reclamacoesDataFrame["store_key"] == matched_key]
else:
    reclamacoes_loja = pd.DataFrame()

# Data processing
def dataProcessing(reclamacoesDataFrame, vendasDataFrame):
    quantidadeDePedidos = vendasDataFrame['count'].sum()
    faturamentoTotal = vendasDataFrame['amount'].sum()
    quantidadeDeReclamacoes = len(reclamacoesDataFrame)
    valorTotalDeCortesia = reclamacoesDataFrame['Valor da Cortesia'].sum()
    return quantidadeDePedidos, faturamentoTotal, quantidadeDeReclamacoes, valorTotalDeCortesia

quantidadeDePedidos, faturamentoTotal, quantidadeDeReclamacoes, valorTotalDeCortesia = dataProcessing(
    reclamacoes_loja, vendas_loja
)

# Metrics
col1, col2, col3, col4 = st.columns(4, gap="small")
with col1:
    st.metric("Total de Reclamações:", f" {int(quantidadeDeReclamacoes):,}".replace(",", "."))
with col2:
    st.metric("Faturamento:", f"R$ {int(faturamentoTotal):,}".replace(",", "."))
with col3:
    st.metric("Total de Pedidos:", f"{int(quantidadeDePedidos):,}".replace(",", "."))
with col4:
    st.metric("Valor de Cortesia gerado:", f"R$ {int(valorTotalDeCortesia):,}".replace(",", "."))

st.divider()

st.markdown("Mês de Junho")
st.dataframe(reclamacoes_loja, hide_index=True)
st.dataframe(vendas_loja, hide_index=True)
if not reclamacoes_loja.empty:
    st.dataframe(reclamacoes_loja['objeto'].value_counts().reset_index().rename(columns={'count': 'quantidade'}), hide_index=True)