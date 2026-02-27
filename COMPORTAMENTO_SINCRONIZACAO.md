# Comportamento da Sincronização - Inserção no Banco

## ✅ RESPOSTA RÁPIDA

**Os projetos são inseridos IMEDIATAMENTE no banco, um por vez, assim que são buscados da API do Zoho.**

---

## 📋 Fluxo Detalhado

### 1. Busca Paginada (sync_zoho.py - linha 250-260)
```python
while True:
    params = {"page": page, "per_page": 50, "last_modified_time": last_sync_time}
    response = requests.get(url, headers=headers, params=params, timeout=45)
    projects = data.get('projects', [])
```
- Busca **50 projetos por página** da API do Zoho
- Faz múltiplas requisições até acabarem os projetos

### 2. Processamento Individual (sync_zoho.py - linha 265-280)
```python
for project in projects:
    # 1. Verifica se deve salvar (filtros de proprietário/status)
    if not projeto_deve_ser_salvo(project):
        continue
    
    # 2. INSERE/ATUALIZA NO BANCO IMEDIATAMENTE
    upsert_project(project)  # <--- AQUI! Commit no banco
    
    # 3. Depois busca fases, listas e tarefas
    sync_fases(project_id, access_token)
    sync_listas_e_tarefas(project_id, access_token, id_fase_impeditivos)
```

### 3. Insert/Update no Banco (database.py - linha 453-467)
```python
def upsert_project(project_data):
    session = Session()
    try:
        stmt = insert(Project).values(**project_obj)
        on_conflict_stmt = stmt.on_conflict_do_update(...)
        session.execute(on_conflict_stmt)
        session.commit()  # <--- COMMIT IMEDIATO!
    finally:
        session.close()
```

---

## 🎯 Comportamento Garantido

| Aspecto | Comportamento |
|---------|---------------|
| **Momento da inserção** | Imediata, assim que o projeto é processado |
| **Transação** | Cada projeto é um `commit()` separado |
| **Em caso de erro** | Rollback do projeto atual, próximos continuam |
| **Se interromper (Ctrl+C)** | Projetos já commitados permanecem no banco |
| **Ordem** | Sequencial - um projeto por vez |

---

## ✅ Vantagens deste Modelo

1. **Resistente a interrupções**: Se você apertar Ctrl+C, os projetos já sincronizados ficam salvos
2. **Visibilidade**: Você pode consultar o banco DURANTE a sincronização
3. **Recuperação**: Se der erro em um projeto, os outros continuam
4. **Progresso incremental**: Mesmo uma sincronização parcial já povoa o banco

---

## ⚠️ Implicações Práticas

### Se você interromper a sincronização:
- ✅ Projetos **já processados** estarão no banco Neon
- ❌ Projetos **não processados** ainda faltarão
- ✅ Próxima execução pode usar `last_modified_time` para buscar apenas novos/modificados

### Se ocorrer erro de API (401, timeout, etc):
- ✅ Projetos **antes do erro** estarão salvos
- ⚠️ Projeto **que deu erro** será pulado (com log de erro)
- ✅ Sincronização **continua** com próximos projetos

---

## 📊 Exemplo de Execução

```
Página 1: 50 projetos
  ├─ Projeto 1 → upsert_project() → COMMIT ✅
  ├─ Projeto 2 → upsert_project() → COMMIT ✅
  ├─ Projeto 3 → filtrado (ignorado) ⏭️
  ├─ Projeto 4 → upsert_project() → COMMIT ✅
  └─ ... (continua até projeto 50)

Página 2: 50 projetos
  ├─ Projeto 51 → upsert_project() → COMMIT ✅
  └─ ... (continua)

Página 3: 7 projetos (última página)
  ├─ Projeto 101 → upsert_project() → COMMIT ✅
  └─ ... até projeto 107
```

**Total: 107 commits separados (um por projeto válido)**

---

## 🔍 Como Monitorar Progresso

### Durante a execução:
```bash
# Terminal 1: Execute o script
python popular_banco.py

# Terminal 2: Consulte o banco em tempo real
python verificar_banco.py
```

Você verá o contador aumentando conforme os projetos são inseridos!

---

## 💡 Conclusão

**Sim, é seguro interromper a sincronização!** 

Os projetos já processados estarão no banco Neon. Você pode:
1. Verificar quantos foram inseridos: `python verificar_banco.py`
2. Decidir se quer continuar ou usar o que já tem
3. Executar novamente para completar (usa `last_modified_time` para otimizar)
