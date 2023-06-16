import streamlit as st
import pandas as pd
import requests
import plotly.express as px


st.set_page_config(layout='wide')


def format_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'


# Crindo o título
st.title("DASHBOARD DE VENDAS :shopping_trolley:")

# leitura dos dados via API
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nodeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)


query_string = {'regiao': regiao.lower(), 'ano': ano}

response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())

dados['Data da Compra'] = pd.to_datetime(
    dados['Data da Compra'], format='%d/%m/%Y')


filtro_vendedores = st.sidebar.multiselect(
    'Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]


# tabelas de Receitas

receitas_estados = dados.groupby('Local da compra')[['Preço']].sum()
receitas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    receitas_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)


receita_mensal = dados.set_index('Data da Compra').groupby(
    pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()


receita_categoria = dados.groupby('Categoria do Produto')[
    ['Preço']].sum().sort_values('Preço', ascending=False)

# Tabelas de quantidade de vendas

# tabela vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')[
                          'Preço'].agg(['sum', 'count']))

# Gráficos
fig_mapa_receita = px.scatter_geo(receitas_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por estado')


fig_receita_mensal = px.line(receita_mensal,
                             x='Mês',
                             y='Preço',
                             markers=True,
                             range_y=(0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')


fig_receita_estado = px.bar(receitas_estados.head(),
                            x='Local da compra',
                            y='Preço',
                            text_auto=True,
                            title='Top estados (receita)')
fig_receita_estado.update_layout(yaxis_title='Receita')

fig_receita_categoria = px.bar(receita_categoria,
                               text_auto=True,
                               title='Receita por Categoria')
fig_receita_categoria.update_layout(yaxis_title='Receita')


# Visualização no streamlit

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendendores'])

with aba1:
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        # somando a coluna de preços
        st.metric('Receita', format_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estado, use_container_width=True)

    with coluna2:
        # Quantidade de linhas do DF. usamos o atributo shape[0]
        st.metric('Quantidade de vendas', format_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categoria, use_container_width=True)

with aba2:
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        # somando a coluna de preços
        st.metric('Receita', format_numero(dados['Preço'].sum(), 'R$'))

    with coluna2:
        # Quantidade de linhas do DF. usamos o atributo shape[0]
        st.metric('Quantidade de vendas', format_numero(dados.shape[0]))

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        # somando a coluna de preços
        st.metric('Receita', format_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x='sum',
                                        y=vendedores[['sum']].sort_values(
                                            'sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)')
        fig_receita_vendedores.update_layout(yaxis_title='')
        st.plotly_chart(fig_receita_vendedores)

    with coluna2:
        # Quantidade de linhas do DF. usamos o atributo shape[0]
        st.metric('Quantidade de vendas', format_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                       x='count',
                                       y=vendedores[['count']].sort_values(
            'count', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        fig_vendas_vendedores.update_layout(yaxis_title='')
        st.plotly_chart(fig_vendas_vendedores)

# st.dataframe(dados)
