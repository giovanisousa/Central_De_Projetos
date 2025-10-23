# 📝 ATUALIZAÇÃO DE ESCOPOS OAUTH - COMENTÁRIOS

## 🎯 Objetivo
Adicionar permissões para leitura e criação de comentários no Zoho Projects.

## 📋 Escopos Necessários

### ✅ Escopos Atuais (já configurados):
- `ZohoProjects.portals.READ`
- `ZohoProjects.projects.ALL`
- `ZohoProjects.tasks.ALL`
- `ZohoProjects.tags.ALL`
- `ZohoProjects.tasklists.ALL`
- `ZohoProjects.users.ALL`
- `ZohoProjects.teams.ALL`
- `ZohoProjects.timesheets.ALL`
- `ZohoProjects.milestones.ALL`
- `ZohoSearch.securesearch.READ`

### 🆕 Novos Escopos (comentários):
- `ZohoProjects.comments.ALL` - Permite ler e criar comentários

## 🔗 URL de Autorização Atualizada

**ATENÇÃO:** Esta URL já inclui TODOS os escopos (atuais + novos)

```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoProjects.comments.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

## 🚀 PASSO A PASSO PARA ATUALIZAR

### 1️⃣ Gerar Novo Grant Code

Cole a URL acima no navegador e autorize a aplicação.

### 2️⃣ Copiar o Code da URL de Redirecionamento

Exemplo:
```
https://localhost/?code=1000.abc123def456.xyz789&location=us&...
```

Copie o code completo: `1000.abc123def456.xyz789`

### 3️⃣ Executar o Script de Token

Abra o PowerShell e execute:

```powershell
# ========================================
# GERAR REFRESH TOKEN DO ZOHO
# ========================================

try {
    $params = @{
        grant_type = "authorization_code"
        client_id = "1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR"
        client_secret = "70226965d09b04444346222d9b4846c86a5d31d2fe"
        redirect_uri = "https://localhost"
        code = "COLE_SEU_CODE_AQUI"  # ← COLE O CODE AQUI!
    }
    
    Write-Host "Trocando grant code por refresh token..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "https://accounts.zoho.com/oauth/v2/token" -Method Post -Body $params -ErrorAction Stop
    
    if (-not $response.refresh_token) {
        Write-Host "❌ ERRO: Resposta não contém refresh_token!" -ForegroundColor Red
        Write-Host "Resposta recebida:" -ForegroundColor Yellow
        Write-Host ($response | ConvertTo-Json -Depth 5)
        exit
    }
    
    Write-Host "✅ ✅ ✅ SUCESSO! ✅ ✅ ✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "REFRESH TOKEN (copie isto):" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host $response.refresh_token -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    
    # Salvar automaticamente
    Set-Content -Path 'zoho_refresh_token.txt' -Value $response.refresh_token
    Write-Host "✅ Refresh token salvo em 'zoho_refresh_token.txt'!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ ERRO! $($_.Exception.Message)" -ForegroundColor Red
}
```

### 4️⃣ Testar a Sincronização de Comentários

```bash
python sync_comentarios.py
```

## 📊 Funcionalidades Implementadas

### Banco de Dados
✅ Tabela `comentarios` criada com:
- `id` (PK) - ID do comentário no Zoho
- `projeto_id` (FK) - ID do projeto
- `conteudo` - Texto do comentário
- `autor_zpuid` - ID do autor
- `autor_nome` - Nome do autor
- `autor_email` - Email do autor
- `data_criacao` - Data de criação (ISO 8601)
- `data_modificacao` - Data de modificação
- `adicionado_via` - Canal (WEB, MOBILE, API, etc.)
- `full_data_json` - JSON completo do comentário

✅ Coluna `data_ultimo_comentario` adicionada à tabela `projects`

✅ Índice `idx_comentarios_projeto_data` para otimizar buscas

### Funções no `database.py`
✅ `upsert_comentario()` - Insere/atualiza comentário
✅ `get_comentarios_projeto()` - Busca comentários de um projeto (com paginação)
✅ `get_ultimo_comentario_projeto()` - Busca comentário mais recente
✅ `atualizar_data_ultimo_comentario()` - Atualiza data no projeto
✅ `contar_comentarios_projeto()` - Conta comentários de um projeto
✅ `limpar_comentarios_projeto()` - Remove todos os comentários de um projeto

### Módulo `sync_comentarios.py`
✅ `buscar_comentarios_projeto_zoho()` - Busca comentários via API (com paginação)
✅ `buscar_todos_comentarios_projeto()` - Busca TODOS os comentários (percorre páginas)
✅ `sincronizar_comentarios_projeto()` - Sincroniza comentários de um projeto
✅ `sincronizar_comentarios_todos_projetos()` - Sincroniza comentários de TODOS os projetos
✅ `adicionar_comentario_projeto_zoho()` - Adiciona novo comentário via API

## 🧪 Scripts de Teste

### Sincronizar Comentários de UM Projeto
```python
from sync_comentarios import sincronizar_comentarios_projeto

projeto_id = "2376502000002326783"  # Substitua pelo ID real
total = sincronizar_comentarios_projeto(projeto_id)
print(f"✅ {total} comentários sincronizados")
```

### Sincronizar Comentários de TODOS os Projetos
```python
from sync_comentarios import sincronizar_comentarios_todos_projetos

resultado = sincronizar_comentarios_todos_projetos()
print(f"Projetos: {resultado['total_projetos']}")
print(f"Comentários: {resultado['total_comentarios']}")
```

### Adicionar um Comentário
```python
from sync_comentarios import adicionar_comentario_projeto_zoho

projeto_id = "2376502000002326783"
conteudo = "Teste de comentário automático via API"
comentario = adicionar_comentario_projeto_zoho(projeto_id, conteudo)
print(f"✅ Comentário criado: {comentario['id']}")
```

### Buscar Comentários do Banco
```python
from database import get_comentarios_projeto, get_ultimo_comentario_projeto

projeto_id = "2376502000002326783"

# Buscar todos os comentários
comentarios = get_comentarios_projeto(projeto_id)
for c in comentarios:
    print(f"{c['autor_nome']} ({c['data_criacao']}): {c['conteudo']}")

# Buscar apenas o mais recente
ultimo = get_ultimo_comentario_projeto(projeto_id)
if ultimo:
    print(f"Último comentário: {ultimo['conteudo']}")
```

## ⚠️ IMPORTANTE

1. **Backup do Token Atual**
   ```bash
   cp zoho_refresh_token.txt zoho_refresh_token_backup.txt
   ```

2. **O Code Expira em 60 Segundos**
   - Gere o code e execute o script rapidamente
   - Cada code só pode ser usado UMA vez

3. **Teste em Ambiente de Desenvolvimento**
   - Execute os testes antes de sincronizar todos os projetos
   - Verifique se os comentários estão sendo armazenados corretamente

## 📝 Próximos Passos

Após atualizar o token:

1. ✅ Executar migração do banco de dados (automática ao rodar `app.py`)
2. ✅ Testar sincronização de comentários de um projeto
3. ✅ Sincronizar comentários de todos os projetos
4. ⬜ Criar interface para exibir comentários
5. ⬜ Criar interface para adicionar comentários
6. ⬜ Implementar alerta de projetos sem atualização (> 5 dias úteis)

## 🔗 Referências

- **Documentação Zoho - Comments API:** https://www.zoho.com/projects/help/rest-api/comments-api.html
- **OAuth Scopes:** https://www.zoho.com/projects/help/rest-api/oauth-scopes.html
