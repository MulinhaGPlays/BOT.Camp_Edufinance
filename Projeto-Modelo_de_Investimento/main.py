import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import quantstats as qs
import seaborn as sns
from dateutil.relativedelta import relativedelta
from pandas_datareader import data as pdr

tickers = pd.read_excel("composicao_ibov.xlsx")

#pegando lista de tickers

intervalo_tempo = tickers.columns

lista_tickers = []

for mes in intervalo_tempo:

    tickers_no_ano = tickers[mes]

    tickers_no_ano = tickers_no_ano.dropna()

    tickers_no_ano = tickers_no_ano + ".SA"

    lista_tickers.append(tickers_no_ano)


lista_tickers_finais = pd.concat(lista_tickers)

lista_tickers_finais = lista_tickers_finais.drop_duplicates()

lista_tickers_finais = list(lista_tickers_finais)

#puxando dados de cotação ajustada

dados_cotacoes = pdr.get_data_yahoo(symbols = lista_tickers_finais, start="2015-06-30", end= "2022-08-12" )['Adj Close']

#resample pra mensal

ultima_linha = dados_cotacoes.iloc[-1:]
dados_cotacoes_mensais = dados_cotacoes.resample("M").last()

#adicionando uma linha
dados_cotacoes_mensais = dados_cotacoes_mensais.append(ultima_linha)

#excluindo uma linha
dados_cotacoes_mensais = dados_cotacoes_mensais.drop("2022-08-31", axis = 0)

#extraindo datas das carteiras

datas_carteiras = list(dados_cotacoes_mensais.index)[6:]

#preenchendo NAs com zero para calcular retorno

dados_cotacoes_mensais = dados_cotacoes_mensais.fillna(0)

#calculando retorno mensal

for i, nome_empresa in enumerate(dados_cotacoes_mensais.columns):

    if i == 0:

      retornos = dados_cotacoes_mensais[nome_empresa].pct_change()

      retornos = retornos.replace([np.inf, -np.inf, -1], 0)

      df_retornos = pd.DataFrame(data = {nome_empresa: retornos}, index = dados_cotacoes_mensais.index)

    else:
    
      df_retornos[nome_empresa] = dados_cotacoes_mensais[nome_empresa].pct_change().replace([np.inf, -np.inf, -1], 0)
      
#calculando retorno 6 meses

for i, nome_empresa in enumerate(dados_cotacoes_mensais.columns):

    if i == 0:

      retornos = dados_cotacoes_mensais[nome_empresa].pct_change(periods = 6)

      retornos = retornos.replace([np.inf, -np.inf, -1], 0)

      df_retornos_6m = pd.DataFrame(data = {nome_empresa: retornos}, index = dados_cotacoes_mensais.index)

    else:
    
      df_retornos_6m[nome_empresa] = dados_cotacoes_mensais[nome_empresa].pct_change(periods = 6).replace([np.inf, -np.inf, -1], 0)
      
df_retornos = df_retornos.loc["2015-12-31": ]
df_retornos_6m = df_retornos_6m.loc["2015-12-31": ]

dados_cotacoes_mensais = dados_cotacoes_mensais.reset_index()

df_retornos = df_retornos.reset_index()
df_retornos_6m = df_retornos_6m.reset_index()


dados_cotacoes_mensais = pd.melt(dados_cotacoes_mensais, id_vars= "Date", var_name= "cod", value_name= "cotacao")
df_retornos = pd.melt(df_retornos, id_vars= "Date", var_name= "cod", value_name= "retorno_1m")
df_retornos_6m = pd.melt(df_retornos_6m, id_vars= "Date", var_name= "cod", value_name= "retorno_6m")

dados_cotacoes_mensais = dados_cotacoes_mensais.dropna()
df_retornos = df_retornos.dropna()
df_retornos_6m = df_retornos_6m.dropna()

lista_retornos = []

#Logica: Pega os codigos de negociação -> Acha os retornos 6M -> Filtra os 10 maiores -> Calcula o retorno de 1 mês dessa carteira -> Repete

for indice, mes in enumerate(datas_carteiras):

    #pegando empresas do ibov mes a mes

    empresas_ibov = tickers[intervalo_tempo[indice]]

    empresas_ibov = list(empresas_ibov.dropna().values) 

    empresas_ibov = [empresa + ".SA" for empresa in empresas_ibov] #quero x a cada y

    #pegando retornos 6 meses pra criar o ranking

    retornos_empresas_ibov_esse_ano = df_retornos_6m[(df_retornos_6m["cod"].isin(empresas_ibov)) & (df_retornos_6m['Date'] == mes)]

    #pegando os 10 maiores retornos

    dez_maiores_retornos = retornos_empresas_ibov_esse_ano.sort_values(by = "retorno_6m", ascending = False).head(10)

    tickers_dez_maiores_retornos = dez_maiores_retornos["cod"].to_list()

    #calculando retorno da carteira 

    if indice != (len(datas_carteiras) - 1): #A carteira de sexta não tem retorno

      retornos_12m_seguintes = df_retornos[(df_retornos["cod"].isin(tickers_dez_maiores_retornos)) & (df_retornos['Date'] == datas_carteiras[indice + 1])]

      retorno_mes = np.mean(retornos_12m_seguintes['retorno_1m'])

      df_retorno_modelo = pd.DataFrame(data = {"retorno": retorno_mes}, index = [(mes + relativedelta(months=1))])

      lista_retornos.append(df_retorno_modelo)


retornos_modelo = pd.concat(lista_retornos)

#pegando dados do ibov

ibovespa = pdr.get_data_yahoo(symbols = '^BVSP', start="2015-12-30", end= "2022-08-12" )['Adj Close']

retornos_ibovespa = ibovespa.resample("M").last().pct_change().dropna()

retornos_modelo['ibovespa'] = retornos_ibovespa.values

retornos_modelo.style.format({
    'retorno': '{:,.2%}'.format,
    'ibovespa': '{:,.2%}'.format
})

qs.extend_pandas()

retornos_modelo['retorno'].plot_monthly_heatmap()

retornos_modelo['ibovespa'].plot_monthly_heatmap()

#olha pra mim agora: se você chegar em alguma empresa do mercado financeiro, ou tem vontade de trabalhar como analista, existe alguma chance de você chegar 
#na entrevista de emprego com esse conhecimento em Python e você não passar? Você sabendo programar um modelo desse, com uma boa visualização de dados, você
#passa pra qualquer lugar. 

serie_long_short = retornos_modelo['retorno'] - retornos_modelo['ibovespa']

serie_long_short.plot_monthly_heatmap()

#meses batendo o mercado 

retornos_modelo_bateu_mercado = retornos_modelo.copy()

retornos_modelo_bateu_mercado['bateu_mercado'] = retornos_modelo['retorno'] > retornos_modelo['ibovespa']

print(retornos_modelo_bateu_mercado)

proporcao_meses_bateu_o_mercado = sum(retornos_modelo_bateu_mercado['bateu_mercado']/len(retornos_modelo_bateu_mercado['bateu_mercado']))
print(proporcao_meses_bateu_o_mercado)

#retorno anual

retorno_anual = retornos_modelo.copy()
retorno_anual['retorno'] = retorno_anual['retorno'] + 1 
retorno_anual['ibovespa'] = retorno_anual['ibovespa'] + 1

retorno_anual["ano"] = retorno_anual.index.year

retorno_anual["retorno_acumulado_ano"] = retorno_anual.groupby('ano')['retorno'].cumprod() - 1
retorno_anual["retorno_acumulado_ibov"] = retorno_anual.groupby('ano')['ibovespa'].cumprod() - 1

retorno_anual = retorno_anual.reset_index()

retorno_anual = (retorno_anual.groupby(['ano']).tail(1))[['ano', 'retorno_acumulado_ano', 'retorno_acumulado_ibov']]

retorno_anual.style.format({
    'retorno_acumulado_ano': '{:,.2%}'.format,
    'retorno_acumulado_ibov': '{:,.2%}'.format})

cumulative_ret_modelo = (retornos_modelo.retorno + 1).cumprod() - 1

cumulative_ret_ibov = (retornos_modelo.ibovespa + 1).cumprod() - 1

df_acumulado = pd.DataFrame(data = {"retorno_acum_modelo": cumulative_ret_modelo, "retorno_acum_ibov" : cumulative_ret_ibov }, index = cumulative_ret_ibov.index)

df_acumulado = df_acumulado.resample("Y").last()

df_acumulado = df_acumulado[['retorno_acum_modelo', 'retorno_acum_ibov']]

df_acumulado.style.format({
    'retorno_acum_modelo': '{:,.2%}'.format,
    'retorno_acum_ibov': '{:,.2%}'.format
})

df_acumulado.plot()