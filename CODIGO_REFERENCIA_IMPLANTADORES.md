# 💻 Referência de Código - Implantadores

## 📋 Snippets Úteis

### 1. Consultar Implantadores no Banco

```python
import sqlite3

conn = sqlite3.connect('zoho_cache.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Buscar todos os projetos com implantadores
cursor.execute("""
    SELECT 
        id,
        nome,
        status_atual,
        implantador_ris,
        implantador_pacs
    FROM projects 
    WHERE implantador_ris IS NOT NULL 
       OR implantador_pacs IS NOT NULL
    ORDER BY nome
""")

projetos = cursor.fetchall()

for projeto in projetos:
    print(f"\n📦 {projeto['nome']}")
    if projeto['implantador_ris']:
        print(f"  📱 RIS: {projeto['implantador_ris']}")
    if projeto['implantador_pacs']:
        print(f"  💻 PACS: {projeto['implantador_pacs']}")

conn.close()
```

---

### 2. Atualizar Implantadores Manualmente no Banco

```python
from database import get_db_connection

def atualizar_implantadores_manual(project_id, implantador_ris=None, implantador_pacs=None):
    """
    Atualiza implantadores de um projeto manualmente.
    Útil para correções ou migrações.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE projects 
        SET 
            implantador_ris = ?,
            implantador_pacs = ?
        WHERE id = ?
    """, (implantador_ris, implantador_pacs, project_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Implantadores atualizados para projeto {project_id}")

# Exemplo de uso:
atualizar_implantadores_manual(
    project_id="2376502000005544019",
    implantador_ris="João Silva, Pedro Costa",
    implantador_pacs="Maria Santos"
)
```

---

### 3. Buscar Custom Fields de um Projeto no Zoho

```python
import utils

def buscar_implantadores_zoho(project_id):
    """
    Busca os implantadores diretamente do Zoho.
    """
    access_token = utils.obter_access_token()
    
    if not access_token:
        print("❌ Erro ao obter access token")
        return None
    
    # Buscar projeto do Zoho
    project_data = utils.buscar_projeto_zoho(project_id, access_token)
    
    if not project_data:
        print("❌ Projeto não encontrado no Zoho")
        return None
    
    # Extrair custom fields
    implantador_ris = None
    implantador_pacs = None
    
    if 'custom_fields' in project_data:
        for field in project_data['custom_fields']:
            if field.get('label_name') == 'implantador_ris':
                implantador_ris = field.get('value')
            elif field.get('label_name') == 'implantador_pacs':
                implantador_pacs = field.get('value')
    
    # Também verificar no primeiro nível
    if not implantador_ris:
        implantador_ris = project_data.get('implantador_ris')
    if not implantador_pacs:
        implantador_pacs = project_data.get('implantador_pacs')
    
    print(f"\n📦 Projeto: {project_data.get('name')}")
    print(f"📱 RIS: {implantador_ris}")
    print(f"💻 PACS: {implantador_pacs}")
    
    return {
        'implantador_ris': implantador_ris,
        'implantador_pacs': implantador_pacs
    }

# Exemplo de uso:
implantadores = buscar_implantadores_zoho("2376502000005544019")
```

---

### 4. Testar Envio de Payload ao Zoho

```python
import requests
import utils

def testar_envio_implantadores(project_id, tipo_projeto='RIS'):
    """
    Testa o envio de implantadores ao Zoho sem usar o manager.
    """
    access_token = utils.obter_access_token()
    portal_id = "868230290"
    
    # Payload de teste
    campo_nome = f"implantador_{tipo_projeto.lower()}"
    payload = {
        "custom_fields": {
            campo_nome: {
                "zpuid_teste_123": "zpuid_teste_123",
                "zpuid_teste_456": "zpuid_teste_456"
            }
        }
    }
    
    url = f"https://projectsapi.zoho.com/restapi/portal/{portal_id}/projects/{project_id}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Enviando payload para projeto {project_id}...")
    print(f"📋 Payload: {payload}")
    
    response = requests.patch(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code in [200, 201]:
        print("✅ Sucesso!")
        print(f"Resposta: {response.json()}")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(f"Detalhes: {response.text[:500]}")
    
    return response

# Exemplo de uso:
# testar_envio_implantadores("2376502000005544019", "RIS")
```

---

### 5. Sincronizar Implantadores de Todos os Projetos

```python
from database import get_db_connection, _formatar_implantadores, _get_custom_field
import utils

def sincronizar_todos_implantadores():
    """
    Força sincronização de implantadores de todos os projetos do Zoho.
    """
    access_token = utils.obter_access_token()
    
    if not access_token:
        print("❌ Erro ao obter access token")
        return
    
    # Buscar todos os projetos do banco
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects")
    project_ids = [row[0] for row in cursor.fetchall()]
    
    print(f"🔄 Sincronizando {len(project_ids)} projetos...")
    
    atualizados = 0
    erros = 0
    
    for project_id in project_ids:
        try:
            # Buscar dados do Zoho
            project_data = utils.buscar_projeto_zoho(project_id, access_token)
            
            if not project_data:
                continue
            
            # Extrair implantadores
            implantador_ris_raw = _get_custom_field(project_data, 'implantador_ris')
            implantador_pacs_raw = _get_custom_field(project_data, 'implantador_pacs')
            
            implantador_ris = _formatar_implantadores(implantador_ris_raw) if implantador_ris_raw else None
            implantador_pacs = _formatar_implantadores(implantador_pacs_raw) if implantador_pacs_raw else None
            
            # Atualizar banco
            if implantador_ris or implantador_pacs:
                cursor.execute("""
                    UPDATE projects 
                    SET 
                        implantador_ris = ?,
                        implantador_pacs = ?
                    WHERE id = ?
                """, (implantador_ris, implantador_pacs, project_id))
                
                atualizados += 1
                print(f"✅ Atualizado: {project_data.get('name')}")
        
        except Exception as e:
            erros += 1
            print(f"❌ Erro no projeto {project_id}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Resumo:")
    print(f"✅ Atualizados: {atualizados}")
    print(f"❌ Erros: {erros}")

# Exemplo de uso:
# sincronizar_todos_implantadores()
```

---

### 6. Gerar Relatório de Implantadores

```python
from database import get_db_connection
from collections import defaultdict

def gerar_relatorio_implantadores():
    """
    Gera relatório de projetos por implantador.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            nome,
            status_atual,
            implantador_ris,
            implantador_pacs
        FROM projects 
        WHERE (implantador_ris IS NOT NULL OR implantador_pacs IS NOT NULL)
          AND status_atual IN ('Em Andamento', 'Em Andamento - Implantação')
    """)
    
    projetos = cursor.fetchall()
    
    # Agrupar por implantador
    por_implantador = defaultdict(list)
    
    for projeto in projetos:
        nome_projeto = projeto['nome']
        
        if projeto['implantador_ris']:
            implantadores = projeto['implantador_ris'].split(', ')
            for impl in implantadores:
                por_implantador[f"{impl} (RIS)"].append(nome_projeto)
        
        if projeto['implantador_pacs']:
            implantadores = projeto['implantador_pacs'].split(', ')
            for impl in implantadores:
                por_implantador[f"{impl} (PACS)"].append(nome_projeto)
    
    # Imprimir relatório
    print("=" * 60)
    print("📊 RELATÓRIO DE PROJETOS POR IMPLANTADOR")
    print("=" * 60)
    print()
    
    for implantador, projetos_lista in sorted(por_implantador.items()):
        print(f"\n👤 {implantador}")
        print(f"   Total de projetos: {len(projetos_lista)}")
        for projeto in projetos_lista:
            print(f"   • {projeto}")
    
    print()
    print("=" * 60)
    
    conn.close()

# Exemplo de uso:
# gerar_relatorio_implantadores()
```

---

### 7. Limpar Implantadores de um Projeto

```python
from database import get_db_connection

def limpar_implantadores(project_id):
    """
    Remove implantadores de um projeto específico.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE projects 
        SET 
            implantador_ris = NULL,
            implantador_pacs = NULL
        WHERE id = ?
    """, (project_id,))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Implantadores removidos do projeto {project_id}")

# Exemplo de uso:
# limpar_implantadores("2376502000005544019")
```

---

### 8. Validar Payload antes de Enviar

```python
def validar_payload_implantadores(payload):
    """
    Valida o payload antes de enviar ao Zoho.
    """
    erros = []
    
    if not isinstance(payload, dict):
        erros.append("Payload deve ser um dicionário")
        return False, erros
    
    if "custom_fields" not in payload:
        erros.append("Payload deve conter 'custom_fields'")
        return False, erros
    
    custom_fields = payload["custom_fields"]
    
    for campo in ["implantador_ris", "implantador_pacs"]:
        if campo in custom_fields:
            valor = custom_fields[campo]
            
            if not isinstance(valor, dict):
                erros.append(f"Campo '{campo}' deve ser um dicionário")
            
            # Validar formato zpuid
            for key in valor.keys():
                if not key.startswith("zpuid"):
                    erros.append(f"Chave inválida em '{campo}': {key} (deve começar com 'zpuid')")
    
    if erros:
        return False, erros
    
    return True, []

# Exemplo de uso:
payload_teste = {
    "custom_fields": {
        "implantador_ris": {
            "zpuid_123": "zpuid_123"
        }
    }
}

valido, erros = validar_payload_implantadores(payload_teste)
if valido:
    print("✅ Payload válido!")
else:
    print("❌ Erros encontrados:")
    for erro in erros:
        print(f"  - {erro}")
```

---

### 9. Debug: Comparar Zoho vs Banco

```python
from database import get_db_connection
import utils

def comparar_implantadores_zoho_banco(project_id):
    """
    Compara implantadores entre Zoho e Banco de Dados.
    Útil para debug e validação.
    """
    # Buscar do banco
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT implantador_ris, implantador_pacs 
        FROM projects 
        WHERE id = ?
    """, (project_id,))
    
    row = cursor.fetchone()
    banco_ris = row['implantador_ris'] if row else None
    banco_pacs = row['implantador_pacs'] if row else None
    
    conn.close()
    
    # Buscar do Zoho
    access_token = utils.obter_access_token()
    project_data = utils.buscar_projeto_zoho(project_id, access_token)
    
    from database import _get_custom_field, _formatar_implantadores
    
    zoho_ris_raw = _get_custom_field(project_data, 'implantador_ris')
    zoho_pacs_raw = _get_custom_field(project_data, 'implantador_pacs')
    
    zoho_ris = _formatar_implantadores(zoho_ris_raw) if zoho_ris_raw else None
    zoho_pacs = _formatar_implantadores(zoho_pacs_raw) if zoho_pacs_raw else None
    
    # Comparar
    print("=" * 60)
    print(f"📊 COMPARAÇÃO: {project_data.get('name')}")
    print("=" * 60)
    print()
    
    print("📱 IMPLANTADOR RIS:")
    print(f"  Zoho: {zoho_ris}")
    print(f"  Banco: {banco_ris}")
    print(f"  Status: {'✅ Sincronizado' if zoho_ris == banco_ris else '⚠️ Dessincronizado'}")
    print()
    
    print("💻 IMPLANTADOR PACS:")
    print(f"  Zoho: {zoho_pacs}")
    print(f"  Banco: {banco_pacs}")
    print(f"  Status: {'✅ Sincronizado' if zoho_pacs == banco_pacs else '⚠️ Dessincronizado'}")
    
    print()
    print("=" * 60)

# Exemplo de uso:
# comparar_implantadores_zoho_banco("2376502000005544019")
```

---

## 📚 Documentos Relacionados

- `IMPLEMENTACAO_IMPLANTADORES.md` - Documentação técnica completa
- `GUIA_TESTES_IMPLANTADORES.md` - Guia de testes manuais
- `RESUMO_IMPLANTADORES.md` - Resumo executivo
- `test_implantadores.py` - Testes automatizados

---

**Nota**: Estes snippets são exemplos para referência. Ajuste conforme necessário para seu caso de uso específico.
