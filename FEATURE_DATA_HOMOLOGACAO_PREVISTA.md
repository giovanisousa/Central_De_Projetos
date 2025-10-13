# ✅ FEATURE: Data de Homologação Prevista nos Cards

**Status**: IMPLEMENTADO  
**Data**: 13/10/2025  
**Requisito**: Exibir data de homologação prevista nos cards da coluna "Em Andamento - Implantação"

---

## 📋 REQUISITO

> "Para os cards que estão nas colunas 'Em Andamento - Implantação', precisamos ter informada a data de homologação, para um maior controle. Pensei que esta data pode ficar ao lado esquerdo do botão Comentário, com um ícone de uma bandeira de chegada. A data será a `data_homologacao_prevista`."

> "O campo customizado que consta a data de homologação prevista é o campo `data_de_termino_original`. Neste caso, precisamos que a data que se encontra neste campo esteja no banco de dados no campo `data_homologacao_prevista`."

---

## 🔧 IMPLEMENTAÇÃO

### 1. Banco de Dados

#### Migração Adicionada

```python
# database.py - Migração 3
if 'data_homologacao_prevista' not in columns:
    cursor.execute("ALTER TABLE projects ADD COLUMN data_homologacao_prevista TEXT")
    print("Migração: Coluna 'data_homologacao_prevista' adicionada à tabela projects")
```

#### Extração do Campo do Zoho

```python
# database.py - Função _extract_project_data_for_db()
data_homologacao_prevista = project_data.get('data_de_termino_original')  # Campo customizado do Zoho
```

**Mapeamento:**
- **Campo no Zoho**: `data_de_termino_original` (campo de primeiro nível)
- **Campo no Banco**: `data_homologacao_prevista` (TEXT)

#### Inclusão no Dicionário de Parâmetros

```python
params = {
    ...
    'data_homologacao': data_homologacao,
    'data_homologacao_prevista': data_homologacao_prevista,  # NOVO!
    'data_virada': data_virada,
    ...
}
```

---

### 2. Backend (API)

#### Endpoint `/api/carregar_projetos` (routes/api.py)

Atualizado para buscar e retornar `data_homologacao_prevista` do banco:

```python
# Busca data_mudanca_status e data_homologacao_prevista do banco
projeto_id = projeto.get('id')
data_mudanca_status = None
data_homologacao_prevista = None
try:
    project_row = database.get_project_by_id(projeto_id)
    if project_row:
        try:
            data_mudanca_status = project_row['data_mudanca_status']
            data_homologacao_prevista = project_row['data_homologacao_prevista']  # NOVO!
        except (KeyError, IndexError):
            data_mudanca_status = None
            data_homologacao_prevista = None
except Exception as e:
    print(f"[WARN] Erro ao buscar dados do projeto {projeto_id}: {e}")

info_projeto = {
    'id': projeto_id,
    'nome': nome_projeto,
    ...
    'data_mudanca_status': data_mudanca_status,
    'data_homologacao_prevista': data_homologacao_prevista  # NOVO!
}
```

**Resultado JSON:**
```json
{
  "sucesso": true,
  "projetos": {
    "Em Andamento - Implantação": [
      {
        "id": "2376502000002326783",
        "nome": "1084 - AMA Diagnóstico - NR/AP (SEM OA)",
        "data_homologacao_prevista": "2025-11-15",  // ✅ NOVO CAMPO!
        ...
      }
    ]
  }
}
```

---

### 3. Frontend (HTML + JavaScript)

#### JavaScript - Criação do Elemento

```javascript
// templates/index.html - função criarCardProjeto()

// 2. Data de Homologação Prevista (apenas para coluna "Em Andamento - Implantação")
let dataHomologacaoPrevistaHtml = '';
if (coluna === 'Em Andamento - Implantação' && projeto.data_homologacao_prevista) {
    const dataFormatada = formatDateToDDMMYYYY(projeto.data_homologacao_prevista);
    dataHomologacaoPrevistaHtml = `
        <div class="data-homologacao-prevista" title="Data de Homologação Prevista">
            <i class="fas fa-flag-checkered"></i>
            <span>${dataFormatada}</span>
        </div>
    `;
}
```

#### HTML - Posicionamento no Card

```html
<div class="project-footer">
    <div class="day-counter stage-days">...</div>
    <div class="day-counter total-days">...</div>
</div>
${dataHomologacaoPrevistaHtml}  <!-- À esquerda do botão de comentário -->
${addCommentBtnHtml}
```

**Estrutura visual:**
```
+-------------------------------+
| 📦 NR/AP   👤 GP   📅 01/10/25 |
| +-----------------------------+
| | ⏳ 5d        📅 120d         |
| +-----------------------------+
| | 🏁 15/11/25  [+] ← posição   |
+-------------------------------+
   ↑ bandeira    ↑ comentário
```

---

### 4. CSS (Estilização)

#### Arquivo Criado: `static/css/data-homologacao.css`

```css
/* Estilo para Data de Homologação Prevista nos cards */
.data-homologacao-prevista {
    position: absolute;
    bottom: 8px;
    right: 42px; /* À esquerda do botão de comentário */
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: #fff3cd;        /* Fundo amarelo claro */
    border: 1px solid #ffc107; /* Borda amarela */
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #856404;            /* Texto marrom escuro */
    z-index: 1;
}

.data-homologacao-prevista i {
    color: #ffc107;            /* Ícone amarelo */
    font-size: 0.85rem;
}
```

**Paleta de Cores:**
- Fundo: `#fff3cd` (amarelo claro)
- Borda: `#ffc107` (amarelo bootstrap warning)
- Texto: `#856404` (marrom escuro)
- Ícone: `#ffc107` (amarelo)

**Inspiração**: Badge de alerta/aviso (bootstrap warning)

#### Link Adicionado no HTML

```html
<head>
    ...
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/data-homologacao.css') }}">  <!--NOVO-->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
```

---

## 🎯 COMPORTAMENTO

### Exibição Condicional

✅ **Exibe quando:**
- Card está na coluna `"Em Andamento - Implantação"`
- AND `projeto.data_homologacao_prevista` existe e não é null

❌ **NÃO exibe quando:**
- Card está em qualquer outra coluna
- OR `data_homologacao_prevista` é `null` ou `undefined`

### Formato da Data

**Entrada (banco/API):**
```
"2025-11-15"  (ISO 8601: YYYY-MM-DD)
```

**Saída (card):**
```
"15/11/25"  (brasileiro: DD/MM/YY)
```

Função usada: `formatDateToDDMMYYYY()`

---

## 🧪 TESTE

### Passo 1: Migrar Banco de Dados

```bash
# Parar aplicação se estiver rodando
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# Rodar app.py - migração automática
python app.py
```

**Saída esperada:**
```
Banco de dados 'zoho_cache.db' verificado/inicializado com o schema completo.
Migração: Coluna 'data_homologacao_prevista' adicionada à tabela projects
```

### Passo 2: Sincronizar Projetos

```python
# Rodar sync_zoho.py para buscar dados do Zoho
python sync_zoho.py
```

Isso vai:
1. Buscar `data_de_termino_original` do Zoho
2. Salvar como `data_homologacao_prevista` no banco

### Passo 3: Verificar Banco de Dados

```bash
python -c "import sqlite3; conn = sqlite3.connect('zoho_cache.db'); c = conn.cursor(); c.execute('SELECT id, nome, data_homologacao_prevista FROM projects WHERE data_homologacao_prevista IS NOT NULL LIMIT 5'); [print(f'{r[0]}: {r[1]} -> {r[2]}') for r in c.fetchall()]; conn.close()"
```

**Saída esperada:**
```
2376502000002326783: 1084 - AMA Diagnóstico - NR/AP (SEM OA) -> 2025-11-15
2376502000003539455: 1225 - Santa Casa - NR/AP -> 2025-12-20
...
```

### Passo 4: Testar Frontend

```bash
# Abrir aplicação
python app.py

# Abrir navegador
http://localhost:5000
```

**Verificar:**
1. Selecionar GP
2. Carregar projetos
3. Verificar cards na coluna "Em Andamento - Implantação"
4. Confirmar que aparecem:
   - 🏁 Ícone de bandeira de chegada (flag-checkered)
   - Data formatada (ex: "15/11/25")
   - À esquerda do botão de comentário (+)
   - Estilo amarelo claro

---

## 📊 EXEMPLO VISUAL

### Card SEM data de homologação

```
┌─────────────────────────────┐
│ ⚠️  !3                       │
│                              │
│ 1084 - AMA Diagnóstico...    │
│ 📦 NR/AP                     │
│ 👤 Giovani de Sousa          │
│ 📅 01/10/25                  │
│                              │
│ ⏳ 12d      📅 120d          │
│                         [+]  │
└─────────────────────────────┘
```

### Card COM data de homologação (NOVO!)

```
┌─────────────────────────────┐
│ ⚠️  !3                       │
│                              │
│ 1084 - AMA Diagnóstico...    │
│ 📦 NR/AP                     │
│ 👤 Giovani de Sousa          │
│ 📅 01/10/25                  │
│                              │
│ ⏳ 12d      📅 120d          │
│              🏁 15/11/25 [+] │  ← NOVO!
└─────────────────────────────┘
      ↑ amarelo claro
```

---

## 🔍 VALIDAÇÃO

### Checklist de Testes

- [ ] Migração do banco executada com sucesso
- [ ] Campo `data_homologacao_prevista` existe na tabela `projects`
- [ ] Sincronização do Zoho popula o campo corretamente
- [ ] API retorna `data_homologacao_prevista` no JSON
- [ ] Cards na coluna "Em Andamento - Implantação" exibem o badge
- [ ] Badge aparece à esquerda do botão de comentário
- [ ] Ícone de bandeira (`fa-flag-checkered`) está visível
- [ ] Data está formatada como DD/MM/YY
- [ ] Estilo amarelo claro está aplicado
- [ ] Badge NÃO aparece em outras colunas
- [ ] Badge NÃO aparece se `data_homologacao_prevista` for null

---

## 📁 ARQUIVOS MODIFICADOS

### Backend
1. ✅ `database.py`
   - Migração 3: `ALTER TABLE projects ADD COLUMN data_homologacao_prevista TEXT`
   - Extração: `data_homologacao_prevista = project_data.get('data_de_termino_original')`
   - Parâmetros: Adicionado ao dicionário `params`

2. ✅ `routes/api.py`
   - `/carregar_projetos`: Busca `data_homologacao_prevista` do banco
   - Retorna no JSON de `info_projeto`

### Frontend
3. ✅ `templates/index.html`
   - Link CSS: `<link rel="stylesheet" href="...data-homologacao.css">`
   - JavaScript: Criação condicional do elemento HTML
   - HTML: Adicionado antes do botão de comentário

4. ✅ `static/css/data-homologacao.css` (NOVO ARQUIVO)
   - Estilo do badge amarelo
   - Posicionamento absoluto
   - Ícone de bandeira

---

## 🎉 CONCLUSÃO

A funcionalidade foi implementada com sucesso! Agora os cards da coluna **"Em Andamento - Implantação"** exibem a data de homologação prevista com:

✅ Ícone de bandeira de chegada (`🏁`)  
✅ Data formatada (DD/MM/YY)  
✅ Estilo visual destacado (amarelo claro)  
✅ Posicionamento à esquerda do botão de comentário  
✅ Exibição condicional (apenas quando há data e card está na coluna correta)  

**Próximas melhorias sugeridas:**
- Adicionar indicador visual se a data está próxima (ex: <7 dias)
- Permitir edição da data diretamente do card
- Sincronizar mudanças da data com o Zoho

---

**Documento gerado por**: GitHub Copilot  
**Branch**: feature/datas-banco-de-dados  
**Arquivo**: FEATURE_DATA_HOMOLOGACAO_PREVISTA.md
