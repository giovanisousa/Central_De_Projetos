# Análise: Campos `dias_fase` e `data_ultima_mudanca`

## 📋 Resumo Executivo

Este documento mapeia o uso, cálculo e atualização dos campos críticos `dias_fase` (ou `dias_na_fase`) e `data_ultima_mudanca` na aplicação Central de Projetos.

**Status Atual:** ⚠️ **INCONSISTENTE** - Os campos não são zerados/atualizados corretamente quando o card muda de coluna.

---

## 🗃️ Definição dos Campos

### 1. `dias_na_fase` (ou `dias_fase`)
**Tipo:** STRING (formato: "Nd", "N/D", "Hoje", "Futuro")  
**Propósito:** Quantidade de dias que o projeto permanece no status/fase atual  
**Localização:** 
- Coluna `dias_na_fase` na tabela `projects` (banco SQLite)
- Campo calculado/derivado (não vem diretamente do Zoho)

### 2. `data_ultima_mudanca`
**Tipo:** STRING (formato: 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS')  
**Propósito:** Data da última alteração de status ou tag do projeto  
**Localização:** 
- Coluna `data_ultima_mudanca` na tabela `projects` (banco SQLite)
- Mapeado do campo `last_modified_time` do Zoho Projects

---

## 🔄 Fluxo de Dados - Quando são Atualizados

### 📥 **1. Carga Inicial / Sincronização (Zoho → Banco)**

#### Arquivo: `database.py` → Função `upsert_project()`
```python
# Linhas ~270-280
dias_na_fase_calc = utils.calcular_dias_na_fase(info_min, coluna_hint)
dias_total_calc = utils.calcular_dias_total_projeto(start_date, created_time)

params = {
    # ...
    'dias_na_fase': dias_na_fase_calc,  # ✅ Calculado com base em datas específicas
    'dias_total': dias_total_calc,
    'data_ultima_mudanca': project_data.get('last_modified_time'),  # ❌ Vem do Zoho (genérico)
    # ...
}
```

**Problema Identificado:**
- `data_ultima_mudanca` vem do `last_modified_time` do Zoho, que **NÃO É ESPECÍFICO** de mudança de status
- Pode ser atualizado por qualquer alteração no projeto (comentário, tarefa, custom field, etc.)
- **Não reflete quando houve a última mudança de STATUS especificamente**

---

### 🎯 **2. Movimentação de Card (Mudança de Coluna)**

#### Arquivo: `routes/api.py` → Endpoint `/mover_projeto`

**Etapa 1: Quando DEVERIA atualizar (caso específico)**
```python
# Linhas ~783-793
if coluna_origem == "Falta Liberar Servidor Infra" and coluna_destino == "Em Andamento":
    data_atual = date.today().strftime('%Y-%m-%d')
    cursor.execute(
        "UPDATE projects SET data_liberacao_servidor = ? WHERE id = ?",
        (data_atual, projeto_id)
    )
    cursor.execute(
        "UPDATE projects SET data_ultima_mudanca = ? WHERE id = ?",  # ✅ Atualiza aqui
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), projeto_id)
    )
```
- ✅ **Atualiza `data_ultima_mudanca`** apenas nesta transição específica
- ❌ **NÃO atualiza** `dias_na_fase` diretamente
- ❌ **NÃO ocorre para outras mudanças de coluna**

**Etapa 2: Sincronização após movimentação**
```python
# Linhas ~1810-1890 (função _sincronizar_db_local)
# 1. Sincroniza dados do Zoho
project_updated = synchronize_single_project(projeto_id, access_token)

# 2. Força atualização da data_ultima_mudanca
data_atual = date.today().strftime('%Y-%m-%d')
cursor.execute("""
    UPDATE projects 
    SET data_ultima_mudanca = ?
    WHERE id = ?
""", (data_atual, projeto_id))  # ✅ Atualiza para HOJE

# 3. Recalcula dias_na_fase
data_ultima = datetime.strptime(data_ultima_str, '%Y-%m-%d').date()
hoje = date.today()
dias_fase = (hoje - data_ultima).days  # ✅ Deveria ser 0 se data_ultima foi atualizada

cursor.execute("""
    UPDATE projects 
    SET dias_na_fase = ?
    WHERE id = ?
""", (str(dias_fase), projeto_id))
```

**Análise:**
- ✅ **Atualiza `data_ultima_mudanca` para a data de HOJE**
- ✅ **Recalcula `dias_na_fase`** baseado na `data_ultima_mudanca` atualizada
- ⚠️ Porém, há um **race condition** possível: se `synchronize_single_project()` sobrescrever `data_ultima_mudanca` com dados antigos do Zoho, o cálculo fica errado

---

### 📊 **3. Exibição no Frontend**

#### Arquivo: `routes/api.py` → Endpoint `/dias-na-fase/<project_id>`
```python
# Linhas ~680-728
# 1. Tenta usar CACHE em memória (TTL: 90 segundos)
key = f"{project_id}|{coluna}" if use_coluna else f"{project_id}"
ent = current_app.config['_DIAS_FASE_CACHE'].get(key)
if ent and (now - ent['ts'] <= 90):
    return jsonify({"dias_na_fase": ent['valor']})

# 2. Busca do banco de dados
project_row = database.get_project_by_id(project_id)
if project_row and project_row['dias_na_fase']:
    return jsonify({"dias_na_fase": project_row['dias_na_fase']})

# 3. Calcula a partir das datas do projeto (fallback)
valor = utils.calcular_dias_na_fase(info_min, None)
```

**Análise:**
- ✅ Usa cache para reduzir carga
- ✅ Prioriza valor já calculado no banco
- ❌ **Não reflete mudanças imediatas** após movimentação (aguarda TTL de cache expirar ou próxima sincronização)

---

## 🧮 Como é Calculado: `dias_na_fase`

### Arquivo: `utils.py` → Função `calcular_dias_na_fase()`

#### Versão 1 (Linhas ~414-437) - Usada no `upsert_project`
```python
def calcular_dias_na_fase(info_min: dict | None, coluna_hint: str | None = None) -> str:
    # Escolhe data baseada na coluna
    if coluna_hint == 'Em Homologação':
        cand = _parse_date_any(info_min.get('data_homologacao'))
    elif coluna_hint == 'Em Virada':
        cand = _parse_date_any(info_min.get('data_virada'))
    elif coluna_hint == 'Em Operação Assistida':
        cand = _parse_date_any(info_min.get('data_inicio_oa'))
    elif coluna_hint in ['Em Andamento', 'Em Andamento - Implantação']:
        cand = _parse_date_any(info_min.get('data_inicio_implantacao')) or \
               _parse_date_any(info_min.get('data_inicio'))
    # ... outros casos
    
    # Fallback genérico
    if not cand:
        cand = _parse_date_any(info_min.get('data_inicio')) or \
               _parse_date_any(info_min.get('data_criacao'))
    
    # Calcula diferença
    return _fmt_dias((date.today() - cand).days)
```

**Características:**
- ✅ Inteligente: escolhe a data mais apropriada para cada fase
- ❌ **Não usa `data_ultima_mudanca`** - usa datas específicas de cada fase
- ❌ Pode estar incorreto se o projeto mudou de fase mas as datas específicas não foram atualizadas

#### Versão 2 (Linhas ~1822-1858) - Com API do Zoho
```python
def calcular_dias_na_fase(info_projeto, status_atual, project_id=None, access_token=None):
    if project_id and access_token:
        # Busca data da última mudança de status/tag via API
        ultima_data = obter_data_ultima_mudanca_status_ou_tag(project_id, access_token)
        if ultima_data:
            dias = (date.today() - ultima_data).days
            return f"{dias}d" if dias > 0 else "Hoje"
    
    # Fallback: usa data_inicio ou data_criacao
    # ... (similar à versão 1)
```

**Características:**
- ✅ **Usa API do Zoho** para buscar a data REAL da última mudança de status/tag
- ✅ Mais preciso quando disponível
- ❌ Faz chamada à API (pode ser lento/consumir rate limit)
- ❌ **NÃO É USADO** no fluxo principal da aplicação

---

## 🔍 Função de Busca: `obter_data_ultima_mudanca_status_ou_tag()`

### Arquivo: `utils.py` (Linhas ~1693-1736)
```python
def obter_data_ultima_mudanca_status_ou_tag(project_id, access_token):
    # 1. Busca histórico de edições do projeto via API /edits
    items = _fetch_project_edits(access_token, project_id, max_pages=6)
    
    # 2. Procura por edições de campo 'status' ou 'etiquetas'
    for item in items:
        edits = item.get('edits') or []
        for ed in edits:
            fname = str(ed.get('field_name', '')).strip().lower()
            if fname not in ("status", "etiquetas"):
                continue
            
            # 3. Extrai a data da ação
            d = parse_action_time(item.get('action_time') or item.get('time'))
            if d and (best_date is None or d > best_date):
                best_date = d
    
    return best_date  # date object ou None
```

**Características:**
- ✅ **Preciso**: busca exatamente mudanças de status ou tags
- ✅ Usa cache interno para evitar rate limit
- ❌ **Consome API do Zoho** (limitado)
- ❌ **Não é chamado durante o fluxo de movimentação de card**

---

## 🐛 Problemas Identificados

### 1. **`data_ultima_mudanca` não é específica de status**
- **Origem:** Vem do `last_modified_time` do Zoho
- **Problema:** Atualizado por QUALQUER mudança (comentário, tarefa, etc.)
- **Impacto:** `dias_na_fase` calculado incorretamente se baseado neste campo

### 2. **Race Condition na Sincronização**
```
Fluxo atual:
1. Usuário move card → chama /mover_projeto
2. _atualizar_zoho() → atualiza status/tags no Zoho
3. _sincronizar_db_local() → 
   3.1. synchronize_single_project() busca dados do Zoho
   3.2. upsert_project() SOBRESCREVE data_ultima_mudanca com last_modified_time antigo
   3.3. Tenta atualizar data_ultima_mudanca para HOJE
   3.4. Recalcula dias_na_fase
```
**Problema:** A etapa 3.2 pode sobrescrever a atualização manual da etapa 3.3

### 3. **`dias_na_fase` não é zerado ao mover card**
- Deveria ser "0" ou "Hoje" ao mudar de coluna
- Atualmente mantém valor antigo até próximo recálculo
- Frontend aguarda cache expirar (90s) ou reload manual

### 4. **Cálculo baseado em datas específicas de fase**
```python
# Em Virada → usa data_virada
# Em Homologação → usa data_homologacao
# Em Andamento → usa data_inicio_implantacao
```
**Problema:** Se estas datas não existem ou não são atualizadas, o cálculo fica errado

### 5. **Função de API não usada no fluxo principal**
- `obter_data_ultima_mudanca_status_ou_tag()` é a mais precisa
- Mas **não é chamada** durante `/mover_projeto`
- Apenas em `calcular_dias_na_fase()` versão 2, que não é usada no fluxo

---

## ✅ Solução Proposta

### Opção 1: Usar `data_ultima_mudanca` corretamente

**Modificações:**
1. **Ao mover card**, atualizar `data_ultima_mudanca` ANTES da sincronização
2. **Na sincronização**, NÃO sobrescrever se foi atualizada recentemente (< 5 min)
3. **Zerar `dias_na_fase`** imediatamente ao mover

```python
# Em _sincronizar_db_local():
# 1. Atualizar data_ultima_mudanca PRIMEIRO
data_atual = date.today().strftime('%Y-%m-%d')
cursor.execute("UPDATE projects SET data_ultima_mudanca = ?, dias_na_fase = '0' WHERE id = ?", 
               (data_atual, projeto_id))

# 2. Sincronizar do Zoho SEM sobrescrever data_ultima_mudanca se recente
project_updated = synchronize_single_project(
    projeto_id, 
    access_token,
    preserve_recent_change=True  # Novo parâmetro
)
```

### Opção 2: Usar API do Zoho para precisão

**Modificações:**
1. Chamar `obter_data_ultima_mudanca_status_ou_tag()` periodicamente (batch noturno)
2. Atualizar `data_ultima_mudanca` no banco com o valor da API
3. `dias_na_fase` sempre calculado a partir de `data_ultima_mudanca`

**Vantagens:**
- ✅ Muito preciso
- ✅ Não depende de race conditions

**Desvantagens:**
- ❌ Consome API do Zoho
- ❌ Não é em tempo real (depende de sync batch)

### Opção 3: Campo separado `data_mudanca_status` (RECOMENDADO)

**Modificações:**
1. Criar novo campo `data_mudanca_status` na tabela `projects`
2. Atualizar SOMENTE ao mover card (fonte única de verdade)
3. `dias_na_fase` calculado APENAS a partir de `data_mudanca_status`
4. Manter `data_ultima_mudanca` para outros fins (auditoria)

```sql
-- Migration
ALTER TABLE projects ADD COLUMN data_mudanca_status TEXT;
```

```python
# Em api_mover_projeto():
cursor.execute("""
    UPDATE projects 
    SET data_mudanca_status = ?, 
        dias_na_fase = '0',
        status_atual = ?
    WHERE id = ?
""", (date.today().strftime('%Y-%m-%d'), coluna_destino, projeto_id))

# Em calcular_dias_na_fase():
if project_row and project_row.get('data_mudanca_status'):
    data_base = parse_date(project_row['data_mudanca_status'])
    return _fmt_dias((date.today() - data_base).days)
```

**Vantagens:**
- ✅ Sem ambiguidade
- ✅ Sem race conditions
- ✅ Fonte única de verdade
- ✅ `data_ultima_mudanca` mantida para auditoria geral

---

## 📌 Checklist de Correção

- [ ] Decidir qual abordagem seguir (recomendado: Opção 3)
- [ ] Criar migration para novo campo (se Opção 3)
- [ ] Modificar `api_mover_projeto()` para atualizar campo específico
- [ ] Modificar `upsert_project()` para não sobrescrever mudanças recentes
- [ ] Atualizar `calcular_dias_na_fase()` para usar campo específico
- [ ] Limpar cache ao mover card
- [ ] Adicionar testes para garantir que:
  - [ ] `dias_na_fase` é zerado ao mover
  - [ ] `data_mudanca_status` é atualizada ao mover
  - [ ] Sincronização não sobrescreve mudanças recentes
- [ ] Documentar comportamento esperado

---

## 📚 Referências de Código

| Arquivo | Função/Endpoint | Linha | Descrição |
|---------|----------------|-------|-----------|
| `database.py` | `upsert_project()` | ~250-350 | Insere/atualiza projeto no banco |
| `utils.py` | `calcular_dias_na_fase()` (v1) | ~414-437 | Cálculo com datas específicas |
| `utils.py` | `calcular_dias_na_fase()` (v2) | ~1822-1858 | Cálculo com API Zoho |
| `utils.py` | `obter_data_ultima_mudanca_status_ou_tag()` | ~1693-1736 | Busca data via API |
| `routes/api.py` | `/mover_projeto` | ~733-850 | Endpoint de movimentação |
| `routes/api.py` | `_sincronizar_db_local()` | ~1808-1900 | Sincronização pós-movimentação |
| `routes/api.py` | `/dias-na-fase/<id>` | ~680-728 | Endpoint de consulta |

---

**Documento gerado em:** 13/10/2025  
**Autor:** Análise Automatizada de Código  
**Status:** ⚠️ Aguardando Implementação de Correções
