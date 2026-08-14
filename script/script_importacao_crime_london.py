"""
Script para executar queries no Google BigQuery usando Python
sobre dados de crimes de Londres, visualizar resultados com pandas
e salvar saídas em CSV.

Dataset: London Crime Analytics
Autor: Thiago Alvarenga (Ajustado a partir de modelo do Prof. Rodrigo Garcia Brunini)
"""

# ======================
# Imports
# ======================
from google.cloud import bigquery
import pandas as pd
import os
import sys

# ======================
# Configurações do Projeto
# ======================
PROJECT_ID = "london-crime-analytics-504619"
TABLE = "london-crime-analytics-504619.dados_crimes_londress.crimes_londres_agregado"
DATASET_LOCATION = None  # ajuste para 'US' ou 'EU' se necessário

# ======================
# Ambiente / Debug
# ======================
print("=== Ambiente de Execução ===")
print("Python executable:", sys.executable)
print("Python version:", sys.version.splitlines()[0])
print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print()

# ======================
# Cliente BigQuery
# ======================
client = bigquery.Client(project=PROJECT_ID)

def run_query(query: str) -> bigquery.job.QueryJob:
    """
    Executa uma query no BigQuery respeitando a região do dataset.
    """
    if DATASET_LOCATION:
        return client.query(query, location=DATASET_LOCATION)
    return client.query(query)

# ======================================================
# Query 1 — Preview dos dados
# ======================================================
print(">>> Query 1: Preview (10 linhas)")

sql_preview = f"""
SELECT
    ano,
    mes,
    bairro,
    categoria_principal,
    subcategoria,
    total_crimes,
    qtd_regioes_lsoa
FROM {TABLE}
LIMIT 10
"""

df_preview = run_query(sql_preview).to_dataframe()
print(df_preview.to_string(index=False))
print()

# ======================================================
# Extração do dataset bruto (sem limpeza)
# ======================================================
print(">>> Extração do dataset bruto (RAW)")

sql_raw = f"""
SELECT *
FROM {TABLE}
"""

df_raw = run_query(sql_raw).to_dataframe()

RAW_OUTPUT_PATH = (
    r"C:\Users\THIAGO\Documents\curso_big_query\projeto_bigquery_crime_london"
    r"\data\raw\crimes_londres_raw.csv"
)

os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)

df_raw.to_csv(RAW_OUTPUT_PATH, index=False)

print(f"Dataset RAW salvo em:\n{RAW_OUTPUT_PATH}")
print(f"Total de registros RAW: {len(df_raw)}")
print()

# ======================================================
# Query 2 — Total de crimes por ano (tendência histórica)
# ======================================================
print(">>> Query 2: Total de crimes por ano (tendência histórica)")

sql_tendencia = f"""
SELECT
    ano,
    SUM(total_crimes) AS total_crimes
FROM {TABLE}
GROUP BY ano
ORDER BY ano
"""

df_tendencia = run_query(sql_tendencia).to_dataframe()
print(df_tendencia.to_string(index=False))
print()

# ======================================================
# Query 3 — Top 5 bairros com mais crimes em 2016 (ano com mais dados)
# ======================================================
print(">>> Query 3: Top 5 bairros com mais crimes em 2016")

sql_top_bairros = f"""
SELECT
    bairro,
    SUM(total_crimes) AS total_crimes
FROM {TABLE}
WHERE ano = 2016
GROUP BY bairro
ORDER BY total_crimes DESC
LIMIT 5
"""

df_top_bairros = run_query(sql_top_bairros).to_dataframe()
print(df_top_bairros.to_string(index=False))
print()

# ======================================================
# Query 4 — Série temporal mensal do bairro com mais crimes em 2016
# ======================================================
print(">>> Query 4: Série temporal mensal - bairro com mais crimes em 2016")

# Primeiro, descobre o bairro com mais crimes em 2016
sql_bairro_top = f"""
SELECT
    bairro,
    SUM(total_crimes) AS total_crimes
FROM {TABLE}
WHERE ano = 2016
GROUP BY bairro
ORDER BY total_crimes DESC
LIMIT 1
"""
df_bairro_top = run_query(sql_bairro_top).to_dataframe()
bairro_top = df_bairro_top.iloc[0]['bairro'] if not df_bairro_top.empty else 'Westminster'

print(f"Bairro com mais crimes em 2016: {bairro_top}")
print()

# Depois, faz a série temporal desse bairro
sql_serie_temporal = f"""
SELECT
    ano,
    mes,
    SUM(total_crimes) AS total_crimes
FROM {TABLE}
WHERE bairro = '{bairro_top}'
GROUP BY ano, mes
ORDER BY ano, mes
"""

df_serie_temporal = run_query(sql_serie_temporal).to_dataframe()
print(df_serie_temporal.tail(10).to_string(index=False))
print()


# ======================================================
# Query — Listar todas as cidades/bairros únicos na coluna bairro
# ======================================================
print(">>> Cidades/Bairros únicos presentes na base:")

sql_bairros_unicos = f"""
SELECT DISTINCT
    bairro
FROM {TABLE}
WHERE bairro IS NOT NULL
ORDER BY bairro ASC
"""

# Executa a query e converte para DataFrame
df_bairros_unicos = run_query(sql_bairros_unicos).to_dataframe()

# Imprime a lista de bairros únicos em formato limpo
print(df_bairros_unicos.to_string(index=False))
print(f"\nTotal de bairros/cidades encontrados: {len(df_bairros_unicos)}")
print()


# ======================================================
# Query — Quantidade Exata de LSOAs Únicos por Bairro (Cidades de Londres)
# ======================================================
print(">>> Mapeando total de regiões LSOA para cada um dos 33 bairros...")

# Consultamos diretamente a tabela original pública no BigQuery para pegar o LSOA sem agregação
sql_lsoa_por_bairro = """
SELECT
    borough AS bairro,
    COUNT(DISTINCT lsoa_code) AS total_lsoas_unicos
FROM
    `bigquery-public-data.london_crime.crime_by_lsoa`
WHERE
    lsoa_code IS NOT NULL
GROUP BY
    bairro
ORDER BY
    total_lsoas_unicos DESC
"""

# Executa a query e converte para DataFrame Pandas
df_lsoa_bairros = run_query(sql_lsoa_por_bairro).to_dataframe()

# Exibe a lista completa das 33 cidades com seus respectivos LSOAs
print(df_lsoa_bairros.to_string(index=False))

# Estatísticas para enriquecer seu README.md
total_geral_lsoas = df_lsoa_bairros['total_lsoas_unicos'].sum()
media_lsoas = df_lsoa_bairros['total_lsoas_unicos'].mean()

print("\n=== RESUMO PARA DOCUMENTAÇÃO (README) ===")
print(f"Total de Bairros (Cidades): {len(df_lsoa_bairros)}")
print(f"Total Geral de Regiões LSOA em Londres: {total_geral_lsoas}")
print(f"Média de LSOAs por Bairro: {media_lsoas:.1f}")
print("=========================================\n")





# ======================================================
# Dicas finais
# ======================================================
print(">>> Dicas finais")
print("- Dataset de crimes é longitudinal e categórico: explore séries temporais e segmentações.")
print("- Use as queries para alimentar dashboards no Power BI.")
print("- Os dados já estão agregados por ano, mês, bairro e categoria.")