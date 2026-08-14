"""
=====================================================
ETL CRIME LONDON - Google BigQuery → Local
=====================================================

OBJETIVO
--------
Este script realiza o processo completo de extração,
limpeza e padronização dos dados de crimes de Londres,
armazenados no Google BigQuery.

ETAPAS DO PIPELINE
------------------
1. Conexão com o BigQuery
2. Extração do dataset bruto (RAW)
3. Padronização de nomes de colunas (snake_case)
4. Remoção de linhas duplicadas e linhas completamente vazias
5. Remoção de colunas sem valores (se houver)
6. Ajuste de tipos de dados
7. Tradução das categorias de crimes para português
8. Salvamento do dataset final (camada READY)

O resultado é um dataset limpo, auditável e pronto
para análise, BI ou modelagem.

Autor: Thiago Alvarenga (Ajustado a partir de modelo do Prof. Rodrigo Garcia Brunini)
"""

# =====================================================
# 1. IMPORTAÇÕES
# =====================================================
from google.cloud import bigquery
import pandas as pd
import os
import sys
import re

# =====================================================
# 2. CONFIGURAÇÕES GERAIS
# =====================================================

PROJECT_ID = "london-crime-analytics-504619"
TABLE = "london-crime-analytics-504619.dados_crimes_londress.crimes_londres_agregado"
DATASET_LOCATION = None  # ajuste para 'US' ou 'EU' se necessário

# Caminho de saída - camada READY
OUTPUT_PATH = (
    r"C:\Users\THIAGO\Documents\curso_big_query\projeto_bigquery_crime_london"
    r"\data\ready\crimes_londres_limpo.csv"
)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


# =====================================================
# 3. INFORMAÇÕES DO AMBIENTE (DEBUG)
# =====================================================
print("=== Ambiente de Execução ===")
print("Python executable:", sys.executable)
print("Python version:", sys.version.splitlines()[0])
print("GOOGLE_APPLICATION_CREDENTIALS:",
      os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print()

# =====================================================
# 4. CLIENTE BIGQUERY
# =====================================================
client = bigquery.Client(project=PROJECT_ID)

def run_query(query: str):
    """
    Executa uma query no BigQuery.
    """
    if DATASET_LOCATION:
        return client.query(query, location=DATASET_LOCATION)
    return client.query(query)

# =====================================================
# 5. EXTRAÇÃO DO DATASET BRUTO
# =====================================================
print(">>> Extraindo dados do BigQuery (RAW)")

sql_raw = f"""
SELECT *
FROM {TABLE}
"""

df = run_query(sql_raw).to_dataframe()

print(f"Total de registros extraídos: {len(df)}")
print(f"Colunas: {df.shape[1]}")
print()

# =====================================================
# 6. PADRONIZAÇÃO DOS NOMES DAS COLUNAS
# =====================================================
print(">>> Padronizando nomes das colunas")

def normalize_column(col: str) -> str:
    """
    Normaliza nomes de colunas para snake_case.
    """
    col = col.strip().lower()
    col = re.sub(r"[^\w]+", "_", col)
    col = re.sub(r"_+", "_", col)
    return col.strip("_")

df.columns = [normalize_column(c) for c in df.columns]

print(f"Colunas padronizadas: {df.columns.tolist()}")
print()

# =====================================================
# 7. REMOÇÃO DE LINHAS DUPLICADAS E TOTALMENTE VAZIAS
# =====================================================
print(">>> Removendo linhas totalmente vazias e duplicadas")

# Remove linhas totalmente vazias
df = df.dropna(axis=0, how="all")

# Remove linhas duplicadas
qtd_antes = len(df)
df = df.drop_duplicates()
qtd_depois = len(df)

print(f"Linhas duplicadas removidas: {qtd_antes - qtd_depois}")
print()

# =====================================================
# 8. REMOÇÃO DE COLUNAS SEM VALORES (COM LOG)
# =====================================================
print(">>> Removendo colunas totalmente vazias")

cols_before = set(df.columns)

# Remove colunas completamente nulas
df = df.dropna(axis=1, how="all")

cols_after = set(df.columns)

# Identifica colunas removidas
removed_columns = sorted(list(cols_before - cols_after))

print(f"Total de colunas removidas: {len(removed_columns)}")

if removed_columns:
    print("Colunas excluídas:")
    for col in removed_columns:
        print(f"- {col}")
else:
    print("Nenhuma coluna foi removida.")
print()

# =====================================================
# 9. AJUSTE DE TIPOS DE DADOS
# =====================================================
print(">>> Ajustando tipos de dados")

# Converter colunas numéricas para tipos adequados
if "ano" in df.columns:
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")

if "mes" in df.columns:
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")

if "total_crimes" in df.columns:
    df["total_crimes"] = pd.to_numeric(df["total_crimes"], errors="coerce").astype("Int64")

if "qtd_regioes_lsoa" in df.columns:
    df["qtd_regioes_lsoa"] = pd.to_numeric(df["qtd_regioes_lsoa"], errors="coerce").astype("Int64")

# Colunas de texto permanecem como string
print("Tipos ajustados:")
print(df.dtypes)
print()

# =====================================================
# 10. TRADUÇÃO DAS CATEGORIAS DE CRIMES PARA PORTUGUÊS
# =====================================================
print(">>> Traduzindo categorias de crimes para português")

# Dicionário de tradução para categoria_principal
traducao_categoria_principal = {
    "Burglary": "Furto_Arrombamento",
    "Criminal Damage": "Dano_Criminal",
    "Drugs": "Drogas",
    "Fraud or Forgery": "Fraude_Falsificacao",
    "Other Notifiable Offences": "Outros_Crimes_Notificaveis",
    "Robbery": "Roubo",
    "Sexual Offences": "Crimes_Sexuais",
    "Theft and Handling": "Furto_Receptacao",
    "Violence Against the Person": "Violencia_Pessoa"
}

# Dicionário de tradução para subcategoria
traducao_subcategoria = {
    "Assault with Injury": "Agressao_Lesao",
    "Burglary in Other Buildings": "Arrombamento_Outros_Edificios",
    "Burglary in a Dwelling": "Arrombamento_Residencia",
    "Business Property": "Propriedade_Comercial",
    "Common Assault": "Agressao_Comum",
    "Counted per Victim": "Contado_Por_Vitima",
    "Criminal Damage To Dwelling": "Dano_Criminal_Residencia",
    "Criminal Damage To Motor Vehicle": "Dano_Criminal_Veiculo",
    "Criminal Damage To Other Building": "Dano_Criminal_Outro_Edificio",
    "Drug Trafficking": "Trafico_Drogas",
    "Going Equipped": "Porte_Instrumento",
    "Handling Stolen Goods": "Receptacao",
    "Harassment": "Assedio",
    "Motor Vehicle Interference & Tampering": "Interferencia_Veiculo",
    "Murder": "Homicidio",
    "Offensive Weapon": "Arma_Ofensiva",
    "Other Criminal Damage": "Outro_Dano_Criminal",
    "Other Drugs": "Outras_Drogas",
    "Other Fraud & Forgery": "Outra_Fraude_Falsificacao",
    "Other Notifiable": "Outro_Notificavel",
    "Other Sexual": "Outro_Crime_Sexual",
    "Other Theft": "Outro_Furto",
    "Other Theft Person": "Outro_Furto_Pessoa",
    "Other violence": "Outra_Violencia",
    "Personal Property": "Propriedade_Pessoal",
    "Possession Of Drugs": "Posse_Drogas",
    "Rape": "Estupro",
    "Theft From Motor Vehicle": "Furto_Veiculo",
    "Theft From Shops": "Furto_Lojas",
    "Theft/Taking Of Motor Vehicle": "Furto_Veiculo_Motor",
    "Theft/Taking of Pedal Cycle": "Furto_Bicicleta",
    "Wounding/GBH": "Lesao_Corporal"
}

# Aplicar tradução nas colunas
if "categoria_principal" in df.columns:
    df["categoria_principal"] = df["categoria_principal"].map(traducao_categoria_principal).fillna(df["categoria_principal"])
    print("✅ Coluna 'categoria_principal' traduzida")

if "subcategoria" in df.columns:
    df["subcategoria"] = df["subcategoria"].map(traducao_subcategoria).fillna(df["subcategoria"])
    print("✅ Coluna 'subcategoria' traduzida")

# Mostrar valores únicos após tradução
print("\n>>> Categorias principais após tradução:")
print(df["categoria_principal"].unique().tolist())

print("\n>>> Subcategorias após tradução (amostra):")
print(df["subcategoria"].unique()[:10].tolist())
print()

# =====================================================
# 11. SALVAMENTO DO DATASET LIMPO (READY)
# =====================================================
print(">>> Salvando dataset limpo")

df.to_csv(OUTPUT_PATH, index=False)

print("Arquivo salvo com sucesso:")
print(OUTPUT_PATH)
print(f"Linhas finais: {len(df)}")
print(f"Colunas finais: {df.shape[1]}")

# =====================================================
# 12. CONSIDERAÇÕES FINAIS
# =====================================================
print("\n>>> Pipeline concluído")
print("- Dataset limpo e padronizado")
print("- Colunas renomeadas para snake_case")
print("- Sem duplicatas ou linhas vazias")
print("- Categorias de crimes traduzidas para português")
print("- Pronto para Power BI, análises e modelos")
print("- Padrão profissional raw → ready aplicado")