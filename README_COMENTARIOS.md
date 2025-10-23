# 📝 Sistema de Comentários - Documentação Completa

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Banco de Dados](#banco-de-dados)
4. [API e Sincronização](#api-e-sincronização)
5. [Como Usar](#como-usar)
6. [Próximos Passos](#próximos-passos)

---

## 🎯 Visão Geral

Sistema completo para buscar, armazenar e gerenciar comentários de projetos do Zoho Projects. Permite sincronizar comentários do Zoho para o banco de dados local e adicionar novos comentários via API.

### Funcionalidades Implementadas ✅

- ✅ Tabela de comentários no banco de dados SQLite
- ✅ Sincronização de comentários do Zoho Projects via API
- ✅ Paginação automática (API do Zoho limita 100 comentários por página)
- ✅ Armazenamento da data do último comentário em cada projeto
- ✅ Adição de comentários via API
- ✅ Funções de consulta otimizadas com índices
- ✅ Script de testes completo

---

## 🏗️ Arquitetura

### Fluxo de Dados

```
┌─────────────────┐
│  Zoho Projects  │
│   (API v3)      │
└────────┬────────┘
         │
         │ sync_comentarios.py
         │ buscar_comentarios_projeto_zoho()
         ▼
┌─────────────────┐
│  Banco SQLite   │
│  (comentarios)  │
└────────┬────────┘
         │
         │ database.py
         │ get_comentarios_projeto()
         ▼
┌─────────────────┐
│   Interface     │
│   Web (TODO)    │
└─────────────────┘
```

---

## 🗄️ Banco de Dados

### Tabela `comentarios`

```sql
CREATE TABLE comentarios (
    id TEXT PRIMARY KEY,              -- ID do comentário no Zoho
    projeto_id TEXT NOT NULL,         -- FK para projects
    conteudo TEXT NOT NULL,           -- Texto do comentário
    autor_zpuid TEXT,                 -- ZPUID do autor
    autor_nome TEXT,                  -- Nome do autor
    autor_email TEXT,                 -- Email do autor
    data_criacao TEXT NOT NULL,       -- Data de criação (ISO 8601)
    data_modificacao TEXT,            -- Data de modificação
    adicionado_via TEXT,              -- Canal: WEB, MOBILE, API, etc.
    full_data_json TEXT,              -- JSON completo do comentário
    FOREIGN KEY (projeto_id) REFERENCES projects (id)
);

CREATE INDEX idx_comentarios_projeto_data 
ON comentarios (projeto_id, data_criacao DESC);
```

### Coluna Adicionada à Tabela `projects`

```sql
ALTER TABLE projects ADD COLUMN data_ultimo_comentario TEXT;
```

**Justificativa:**
- ✅ Otimiza consultas de projetos sem atualização recente
- ✅ Evita JOIN/subconsulta para calcular alerta de 5 dias úteis
- ✅ Denormalização estratégica (valor consultado frequentemente)
- ✅ Consistente com `data_ultima_mudanca`

---

## 🔌 API e Sincronização

### Módulo `sync_comentarios.py`

#### Funções Principais

##### 1. `buscar_comentarios_projeto_zoho(projeto_id, access_token, page=1, per_page=100)`

Busca comentários de um projeto com paginação.

**Parâmetros:**
- `projeto_id` (str): ID do projeto no Zoho
- `access_token` (str): Token OAuth
- `page` (int): Número da página (padrão: 1)
- `per_page` (int): Comentários por página (max: 100)

**Retorna:**
```python
{
    'comments': [...],
    'page_info': {
        'per_page': '100',
        'has_next_page': 'false',
        'count': '12',
        'page': '1'
    }
}
```

**Endpoint da API:**
```
GET /api/v3/portal/{PORTAL_ID}/projects/{PROJECT_ID}/comments
```

**Escopo OAuth Necessário:**
```
ZohoProjects.comments.ALL
```

---

##### 2. `buscar_todos_comentarios_projeto(projeto_id, access_token)`

Busca **TODOS** os comentários de um projeto (percorre todas as páginas).

**Retorna:** Lista completa de comentários

**Exemplo:**
```python
from sync_comentarios import buscar_todos_comentarios_projeto
from utils import obter_access_token

token = obter_access_token()
comentarios = buscar_todos_comentarios_projeto("2376502000002326783", token)
print(f"Total: {len(comentarios)} comentários")
```

---

##### 3. `sincronizar_comentarios_projeto(projeto_id, access_token=None)`

Sincroniza comentários de um projeto do Zoho para o banco local.

**Retorna:** Número de comentários sincronizados (int)

**Exemplo:**
```python
from sync_comentarios import sincronizar_comentarios_projeto

total = sincronizar_comentarios_projeto("2376502000002326783")
print(f"✅ {total} comentários sincronizados")
```

---

##### 4. `sincronizar_comentarios_todos_projetos(forcar_ressincronizacao=False)`

Sincroniza comentários de **TODOS** os projetos no banco de dados.

**Parâmetros:**
- `forcar_ressincronizacao` (bool): Se True, limpa comentários existentes antes

**Retorna:**
```python
{
    'total_projetos': 150,
    'total_comentarios': 3842,
    'projetos_com_erros': []
}
```

**Exemplo:**
```python
from sync_comentarios import sincronizar_comentarios_todos_projetos

# Sincronização incremental (mantém comentários existentes)
resultado = sincronizar_comentarios_todos_projetos()

# Sincronização completa (remove e re-sincroniza tudo)
resultado = sincronizar_comentarios_todos_projetos(forcar_ressincronizacao=True)
```

---

##### 5. `adicionar_comentario_projeto_zoho(projeto_id, conteudo, access_token=None)`

Adiciona um novo comentário a um projeto via API e sincroniza no banco local.

**Parâmetros:**
- `projeto_id` (str): ID do projeto
- `conteudo` (str): Texto do comentário
- `access_token` (str, opcional): Token OAuth

**Retorna:** Dicionário com dados do comentário criado

**Exemplo:**
```python
from sync_comentarios import adicionar_comentario_projeto_zoho

comentario = adicionar_comentario_projeto_zoho(
    projeto_id="2376502000002326783",
    conteudo="Homologação concluída com sucesso!"
)

print(f"Comentário criado: {comentario['id']}")
```

---

### Módulo `database.py`

#### Funções de Comentários

##### 1. `upsert_comentario(comentario_data, projeto_id)`

Insere ou atualiza um comentário no banco.

**Atualiza automaticamente:** `data_ultimo_comentario` no projeto

---

##### 2. `get_comentarios_projeto(projeto_id, limit=None, offset=0)`

Busca comentários de um projeto (ordenados por data decrescente).

**Exemplo:**
```python
from database import get_comentarios_projeto

# Buscar todos
comentarios = get_comentarios_projeto("2376502000002326783")

# Buscar com paginação (10 por página)
comentarios = get_comentarios_projeto("2376502000002326783", limit=10, offset=0)

for c in comentarios:
    print(f"{c['autor_nome']}: {c['conteudo']}")
```

---

##### 3. `get_ultimo_comentario_projeto(projeto_id)`

Busca o comentário mais recente de um projeto.

**Retorna:** `sqlite3.Row` ou `None`

---

##### 4. `atualizar_data_ultimo_comentario(projeto_id)`

Atualiza `data_ultimo_comentario` no projeto com a data do comentário mais recente.

**Chamada automática:** Executada por `upsert_comentario()`

---

##### 5. `contar_comentarios_projeto(projeto_id)`

Conta o número total de comentários de um projeto.

**Exemplo:**
```python
from database import contar_comentarios_projeto

total = contar_comentarios_projeto("2376502000002326783")
print(f"Projeto tem {total} comentários")
```

---

##### 6. `limpar_comentarios_projeto(projeto_id)`

Remove **TODOS** os comentários de um projeto e define `data_ultimo_comentario = NULL`.

**Retorna:** Número de comentários removidos

---

## 🚀 Como Usar

### Passo 1: Atualizar Escopo OAuth

Antes de usar as funcionalidades de comentários, **é necessário** atualizar o token OAuth para incluir o escopo `ZohoProjects.comments.ALL`.

Consulte o arquivo **`ATUALIZACAO_ESCOPOS_COMENTARIOS.md`** para instruções detalhadas.

**URL de Autorização (com todos os escopos):**
```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tags.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.users.ALL,ZohoProjects.teams.ALL,ZohoProjects.timesheets.ALL,ZohoProjects.milestones.ALL,ZohoProjects.comments.ALL,ZohoSearch.securesearch.READ&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://localhost
```

---

### Passo 2: Executar Testes

Execute o script de testes para validar a integração:

```bash
python test_comentarios.py
```

**Testes Disponíveis:**
1. ✅ Sincronização de comentários do Zoho
2. ✅ Busca de comentários no banco de dados
3. ✅ Adição de novo comentário via API
4. ✅ Verificação da data do último comentário

---

### Passo 3: Sincronizar Comentários

#### Opção A: Sincronizar UM Projeto

```python
from sync_comentarios import sincronizar_comentarios_projeto

projeto_id = "2376502000002326783"
total = sincronizar_comentarios_projeto(projeto_id)
print(f"✅ {total} comentários sincronizados")
```

#### Opção B: Sincronizar TODOS os Projetos

```python
from sync_comentarios import sincronizar_comentarios_todos_projetos

resultado = sincronizar_comentarios_todos_projetos()
print(f"Projetos: {resultado['total_projetos']}")
print(f"Comentários: {resultado['total_comentarios']}")
```

#### Opção C: Usar o Script Interativo

```bash
python sync_comentarios.py
```

Menu de opções:
1. Sincronizar comentários de UM projeto específico
2. Sincronizar comentários de TODOS os projetos
3. Sincronizar comentários de TODOS os projetos (forçar ressincronização)

---

### Passo 4: Consultar Comentários

```python
from database import get_comentarios_projeto, get_ultimo_comentario_projeto

projeto_id = "2376502000002326783"

# Buscar todos os comentários
comentarios = get_comentarios_projeto(projeto_id)
for c in comentarios:
    print(f"{c['data_criacao']} - {c['autor_nome']}: {c['conteudo']}")

# Buscar apenas o mais recente
ultimo = get_ultimo_comentario_projeto(projeto_id)
if ultimo:
    print(f"Último comentário: {ultimo['conteudo']}")
```

---

### Passo 5: Adicionar Comentário

```python
from sync_comentarios import adicionar_comentario_projeto_zoho

projeto_id = "2376502000002326783"
conteudo = "Projeto em homologação. Tudo funcionando conforme esperado."

comentario = adicionar_comentario_projeto_zoho(projeto_id, conteudo)
print(f"✅ Comentário criado: {comentario['id']}")
```

---

## 📝 Próximos Passos

### Parte 2: Interface Web (Pendente)

#### 1. Criar Endpoints REST

**Arquivo:** `routes/api.py`

```python
@api_bp.route('/comentarios/<projeto_id>', methods=['GET'])
def api_buscar_comentarios(projeto_id):
    """Busca comentários de um projeto."""
    pass

@api_bp.route('/comentarios/<projeto_id>', methods=['POST'])
def api_adicionar_comentario(projeto_id):
    """Adiciona um novo comentário."""
    pass

@api_bp.route('/sincronizar-comentarios/<projeto_id>', methods=['POST'])
def api_sincronizar_comentarios(projeto_id):
    """Sincroniza comentários do Zoho."""
    pass
```

#### 2. Criar Modal de Comentários

**Arquivo:** `templates/index.html`

- Modal ao clicar no botão "+" do card
- Campo de texto para novo comentário
- Lista de comentários existentes (autor, data, conteúdo)
- Botão "Sincronizar" para atualizar do Zoho
- Scroll para comentários longos

#### 3. Implementar Alerta de Projetos Sem Atualização

**Critério:** Projetos sem comentários há mais de 5 dias úteis

**Implementação:**
- Script Python para calcular dias úteis desde último comentário
- Adicionar classe CSS `sem-atualizacao` ao card
- Borda vermelha + tooltip informativo

#### 4. Atualizar Sincronização Periódica

Incluir sincronização de comentários no processo de sincronização existente:

**Arquivo:** `sync_zoho.py`

```python
def synchronize_projects():
    # ... código existente ...
    
    # Sincronizar comentários de todos os projetos
    from sync_comentarios import sincronizar_comentarios_todos_projetos
    sincronizar_comentarios_todos_projetos()
```

---

## 📚 Referências

- **Documentação Zoho - Comments API:** https://www.zoho.com/projects/help/rest-api/comments-api.html
- **OAuth Scopes do Zoho:** https://www.zoho.com/projects/help/rest-api/oauth-scopes.html
- **ISSUES_CONHECIDOS.md:** Funcionalidade #1 - Sistema de Comentários Completo
- **ATUALIZACAO_ESCOPOS_COMENTARIOS.md:** Guia de atualização do token OAuth

---

## ⚙️ Configurações

### Escopo OAuth Necessário

```
ZohoProjects.comments.ALL
```

### Limite da API

- **Comentários por página:** 100 (máximo)
- **Rate limiting:** Recomendado delay de 0.2s entre páginas

### Performance

- **Índice otimizado:** `idx_comentarios_projeto_data` acelera consultas
- **Denormalização:** `data_ultimo_comentario` na tabela `projects`
- **Paginação:** Suportada nas funções de busca

---

## 🐛 Troubleshooting

### Erro 401 - Invalid OAuth Scope

**Causa:** Token não tem permissão `ZohoProjects.comments.ALL`

**Solução:** Atualizar token OAuth (veja `ATUALIZACAO_ESCOPOS_COMENTARIOS.md`)

---

### Erro 404 - Project Not Found

**Causa:** Projeto ID inválido ou projeto sem comentários

**Solução:** Verificar ID do projeto no banco de dados

---

### Comentários Não Aparecem no Banco

**Causa:** Sincronização não foi executada

**Solução:**
```python
from sync_comentarios import sincronizar_comentarios_projeto
sincronizar_comentarios_projeto("SEU_PROJETO_ID")
```

---

## 📊 Estatísticas

Após implementação completa, o sistema permite:

- ✅ Sincronizar centenas de projetos em minutos
- ✅ Buscar comentários com performance otimizada (índices)
- ✅ Adicionar comentários via interface web
- ✅ Rastrear projetos sem atualização há > 5 dias úteis
- ✅ Histórico completo de comunicação do projeto

---

**Última atualização:** 22/10/2025  
**Versão:** 1.0.0  
**Status:** Backend Completo ✅ | Interface Pendente ⏳
