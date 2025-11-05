# ✅ FASE 1: Normalização de Dados - CONCLUÍDA

**Data:** 2025-11-05  
**Branch:** correcao15  
**Commit:** 110778c

---

## 🎯 Objetivo

Remover gradualmente a dependência de `full_data_json`, criando colunas normalizadas para dados frequentemente acessados. Isso melhora:
- ✅ **Performance**: Queries SQL diretas com índices (vs parsing JSON)
- ✅ **Manutenibilidade**: Código mais limpo e legível
- ✅ **Confiabilidade**: Tipos de dados garantidos pelo PostgreSQL

---

## 📊 Colunas Adicionadas

| Coluna | Tipo | Descrição | População |
|--------|------|-----------|-----------|
| `owner_zpuid` | VARCHAR(50) | ZPUID do dono (GP) do projeto | 100% (106/106) |
| `owner_name` | VARCHAR(255) | Nome do dono (GP) | 100% (106/106) |
| `client_name` | VARCHAR(255) | Nome do cliente | 100% (106/106) |
| `project_name` | VARCHAR(500) | Nome do projeto | 100% (106/106) |

**Índice criado:** `idx_projects_owner_zpuid` (melhora performance do filtro GP)

---

## 🔧 Alterações no Código

### 1. **database.py**

#### Modelo `Project` (linhas 38-48)
```python
# ✅ FASE 1: Colunas normalizadas (substituem full_data_json gradualmente)
owner_zpuid = Column(String)  # ZPUID do dono (GP) do projeto
owner_name = Column(String)   # Nome do dono (GP)
client_name = Column(String)  # Nome do cliente
project_name = Column(String) # Nome do projeto

full_data_json = Column(Text) # JSON string - DEPRECATED, usar colunas normalizadas
```

#### `upsert_project()` (linhas 385-400)
```python
# ✅ FASE 1: Extrair dados normalizados de owner e client
owner_data = project_data.get('owner', {})
owner_zpuid = owner_data.get('zpuid')
owner_name = owner_data.get('name')

# Cliente: prioriza client_company, depois client, depois client_name
client_company = project_data.get('client_company', {})
client_obj = project_data.get('client', {})
client_name = (
    client_company.get('name') if isinstance(client_company, dict) else None
) or (
    client_obj.get('name') if isinstance(client_obj, dict) else None
) or project_data.get('client_name')

project_name = project_data.get('name', 'N/A')
```

#### Adicionado ao `project_obj` (linhas 438-442)
```python
# ✅ FASE 1: Colunas normalizadas
'owner_zpuid': owner_zpuid,
'owner_name': owner_name,
'client_name': client_name,
'project_name': project_name,
```

### 2. **routes/api.py**

#### Filtro GP Otimizado (linhas 633-645)
**ANTES (parsing JSON - lento):**
```python
# Solução TEMPORÁRIA: Filtrar por ZPUID usando full_data_json
all_projects = session.query(Project).all()
projetos_do_gp = []
for p in all_projects:
    if p.full_data_json:
        try:
            projeto_data = json.loads(p.full_data_json)
            owner_zpuid = projeto_data.get('owner', {}).get('zpuid', '')
            if str(owner_zpuid) == str(id_do_gp):
                projetos_do_gp.append(p)
        except:
            pass
```

**DEPOIS (query direta - rápido):**
```python
# ✅ FASE 1: Filtrar usando coluna normalizada owner_zpuid
from database import Project

logger.info(f"[DEBUG] GP selecionado: '{gp_selecionado}'")
logger.info(f"[DEBUG] ID do GP (zpuid): '{id_do_gp}'")

# ✅ Query otimizada: usa índice em owner_zpuid
projetos_do_gp = session.query(Project).filter(
    Project.owner_zpuid == str(id_do_gp)
).all()

logger.info(f"[DEBUG] Total de projetos encontrados: {len(projetos_do_gp)}")
```

---

## 📈 Ganhos de Performance

### Filtro GP (endpoint `/carregar_projetos`)

| Métrica | ANTES | DEPOIS | Melhoria |
|---------|-------|--------|----------|
| **Operação** | Loop + JSON parse (106 projetos) | Query SQL com índice | ⚡ ~10x |
| **Queries** | 1 SELECT * + 106 JSON parse | 1 SELECT com WHERE | ✅ |
| **Uso de índice** | ❌ Não | ✅ Sim (`idx_projects_owner_zpuid`) | ✅ |
| **Complexidade** | O(n) | O(log n) | ✅ |

**Estimativa:** Redução de ~200ms para ~20ms no filtro GP

---

## 🧪 Testes Realizados

✅ Migration executada com sucesso no banco de dados  
✅ 100% dos projetos populados com as novas colunas  
✅ Índice criado em `owner_zpuid`  
✅ Código atualizado em `database.py` e `routes/api.py`  
✅ Commit realizado (110778c)  

---

## 🚀 Próximas Fases

### **FASE 2: Substituir Usos de `full_data_json` em Detalhes**
- [ ] Substituir `detalhes_zoho` em `/mover_projeto` (linha 940)
- [ ] Substituir em `/agendar_homologacao` (linha 1849)
- [ ] Substituir em `/agendar_virada` (linha 2362)
- [ ] Adicionar colunas extras se necessário (ex: `start_date`, `created_time`)

### **FASE 3: Deprecação Gradual**
- [ ] Marcar `full_data_json` como DEPRECATED em toda documentação
- [ ] Parar de atualizar `full_data_json` em `upsert_project()`
- [ ] Adicionar warning logs quando `full_data_json` for acessado

### **FASE 4: Remoção Completa** (só após 100% de certeza)
- [ ] Remover coluna `full_data_json` do banco
- [ ] Remover do modelo `Project`
- [ ] Limpar código que referencia `full_data_json`

---

## 📝 Notas Importantes

1. **`full_data_json` ainda é atualizado**: Por segurança, continuamos salvando o JSON completo como backup
2. **Compatibilidade**: O código antigo que usa `full_data_json` ainda funciona normalmente
3. **Reversível**: Se houver problemas, podemos reverter para usar `full_data_json` novamente
4. **Performance**: O ganho real será medido após deploy em produção

---

## ✅ Status: FASE 1 CONCLUÍDA COM SUCESSO! 🎉
