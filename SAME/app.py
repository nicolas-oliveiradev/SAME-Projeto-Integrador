"""SAME | Painel interativo de análise de estoque."""
from datetime import date
from pathlib import Path
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from analisador import DADOS, ErroDados, analisar
from indicadores import curva_abc, exportar_csv, movimentacoes_por_mes, tabela_produtos

st.set_page_config(page_title='SAME | Monitoramento de Estoque', page_icon='📦', layout='wide')
st.title('📦 SAME — Sistema de Análise e Monitoramento de Estoque')
st.caption('Projeto Integrador • base demonstrativa sintética • Python')

with st.sidebar:
    st.header('Configurações')
    referencia = st.date_input('Data de referência', value=date(2026, 11, 20),
                              min_value=date(2026, 6, 1), max_value=date(2100, 1, 1))
    st.markdown('**Fonte dos dados**')
    usar_upload = st.toggle('Importar arquivos CSV próprios', value=False)
    produtos_arquivo = movimentacoes_arquivo = None
    if usar_upload:
        produtos_arquivo = st.file_uploader('produtos.csv', type=['csv'])
        movimentacoes_arquivo = st.file_uploader('movimentacoes.csv', type=['csv'])
    st.info('Classificação ABC baseada no valor de consumo (saídas × custo). Não representa vendas nem lucro.')

try:
    if usar_upload:
        if not produtos_arquivo or not movimentacoes_arquivo:
            st.warning('Envie ambos os arquivos CSV para iniciar a análise.')
            st.stop()
        with tempfile.TemporaryDirectory() as pasta_temp:
            pasta = Path(pasta_temp)
            (pasta / 'produtos.csv').write_bytes(produtos_arquivo.getvalue())
            (pasta / 'movimentacoes.csv').write_bytes(movimentacoes_arquivo.getvalue())
            resultado = analisar(pasta, referencia)
            por_mes = movimentacoes_por_mes(pasta)
    else:
        resultado = analisar(DADOS, referencia)
        por_mes = movimentacoes_por_mes(DADOS)
except (ErroDados, ValueError, UnicodeDecodeError, KeyError) as erro:
    st.error(f'Não foi possível processar os dados: {erro}')
    st.stop()

produtos = tabela_produtos(resultado)
df = pd.DataFrame(produtos)
abc = pd.DataFrame(curva_abc(resultado))

col1, col2, col3, col4 = st.columns(4)
col1.metric('Produtos', len(resultado['produtos']))
col2.metric('Movimentações', resultado['movimentacoes'])
col3.metric('Estoque crítico', len(resultado['criticos']))
col4.metric('Valor de estoque', f"R$ {resultado['valor_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
st.caption(f"Entradas: {resultado['total_entradas']:,} unidades | Saídas: {resultado['total_saidas']:,} unidades | Inativos (mais de 30 dias): {len(resultado['inativos'])}")

st.subheader('Produtos monitorados')
categorias = ['Todas'] + sorted(df['Categoria'].unique().tolist())
categoria = st.selectbox('Categoria', categorias)
situacao = st.selectbox('Situação do estoque', ['Todas', 'Crítico', 'Normal'])
filtrado = df.copy()
if categoria != 'Todas':
    filtrado = filtrado[filtrado['Categoria'] == categoria]
if situacao != 'Todas':
    filtrado = filtrado[filtrado['Situação'] == situacao]
st.dataframe(filtrado, use_container_width=True, hide_index=True)
st.download_button('⬇️ Exportar produtos filtrados (CSV)', exportar_csv(filtrado.to_dict('records')),
                   file_name='relatorio_same.csv', mime='text/csv')

esq, dir = st.columns(2)
with esq:
    st.subheader('Entradas e saídas mensais')
    mensal = pd.DataFrame(por_mes)
    fig = px.bar(mensal, x='mes', y=['entradas', 'saidas'], barmode='group',
                 labels={'mes':'Mês', 'value':'Unidades', 'variable':'Tipo'})
    st.plotly_chart(fig, use_container_width=True)
with dir:
    st.subheader('Produtos por classe ABC')
    contagem = abc['classe'].value_counts().reindex(['A', 'B', 'C'], fill_value=0).reset_index()
    contagem.columns = ['Classe', 'Produtos']
    fig = px.bar(contagem, x='Classe', y='Produtos', text='Produtos')
    st.plotly_chart(fig, use_container_width=True)

st.subheader('Análise ABC por valor de consumo')
st.caption('Valor de consumo = soma das saídas de cada produto × custo unitário. Classes A até 80%, B até 95% e C acima de 95% do consumo acumulado (critério operacional adotado).')
st.dataframe(abc[['produto_id', 'nome', 'valor_consumo', 'participacao_percentual',
                  'acumulado_percentual', 'classe']].rename(columns={
    'produto_id':'ID', 'nome':'Produto', 'valor_consumo':'Consumo estimado (R$)',
    'participacao_percentual':'Participação (%)', 'acumulado_percentual':'Acumulado (%)',
    'classe':'Classe'}), use_container_width=True, hide_index=True)
st.markdown('**Limitações:** dados de exemplo simulados; não há previsão de demanda, controle de múltiplos depósitos nem movimentações financeiras reais. A data selecionada deve ser posterior ou igual à última movimentação do arquivo.')
