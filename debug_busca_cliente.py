import utils
from config import ID_PLANILHA_PROJETOS, NOME_ABA_PLANILHA, COLUNA_REFERENCIA_PARA_CONTAR_LINHAS, LINHA_CABECALHO

# Obter credenciais
creds = utils.build_google_credentials_from_session()
from googleapiclient.discovery import build
sheets_service = build('sheets', 'v4', credentials=creds)

# Buscar o cabeçalho
headers_range = f"{NOME_ABA_PLANILHA}!A{LINHA_CABECALHO}:ZZ{LINHA_CABECALHO}"
resp = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=headers_range).execute()
headers = (resp.get('values') or [[]])[0]

# Encontrar coluna de cliente
cliente_idx = None
for idx, h in enumerate(headers):
    if h == COLUNA_REFERENCIA_PARA_CONTAR_LINHAS:
        cliente_idx = idx
        break

if cliente_idx is None:
    print(f"Coluna '{COLUNA_REFERENCIA_PARA_CONTAR_LINHAS}' não encontrada!")
    exit(1)

# Buscar todos os clientes
from utils import _a1_col_letter
cliente_col = _a1_col_letter(cliente_idx)
valores_cli_range = f"{NOME_ABA_PLANILHA}!{cliente_col}{LINHA_CABECALHO+1}:{cliente_col}"
vals = sheets_service.spreadsheets().values().get(spreadsheetId=ID_PLANILHA_PROJETOS, range=valores_cli_range).execute()
linhas = (vals.get('values') or [])

# Buscar cliente específico
busca = "1064"
print(f"\n=== Buscando clientes que contêm '{busca}' ===\n")
encontrados = []
for i, row in enumerate(linhas, start=LINHA_CABECALHO + 1):
    val = (row[0] if row else '').strip()
    if busca in val:
        encontrados.append((i, val))
        print(f"Linha {i}: '{val}'")

if not encontrados:
    print(f"\n❌ Nenhum cliente encontrado com '{busca}' no código")
    print("\n=== Mostrando primeiras 10 linhas para debug ===\n")
    for i, row in enumerate(linhas[:10], start=LINHA_CABECALHO + 1):
        val = (row[0] if row else '').strip()
        print(f"Linha {i}: '{val}'")
else:
    print(f"\n✅ Encontrados {len(encontrados)} clientes")
