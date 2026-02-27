# Correções do sync_completo_seguro.py

## 🔧 Problemas Corrigidos

### 1. Token Zoho expirando (erro 401)
**Problema:** Access token do Zoho expira após ~1 hora, causando erros 401 no meio da sincronização.

**Solução:**
- ✅ Renovação de token a cada **15 minutos** (antes era 30min)
- ✅ Retry automático **3 tentativas** para erros 401
- ✅ Renovação de token entre tentativas
- ✅ Delay de 2s entre retries

### 2. Foreign Key Violation - Listas sem Fase
**Problema:** Alguns projetos têm listas de tarefas que referenciam fases inexistentes:
```
Key (fase_id)=(2376502000000000073) is not present in table "fases"
```

**Solução em `database.py`:**
- ✅ `upsert_lista_de_tarefas()`: Verifica se fase existe antes de inserir
- ✅ Ignora listas que referenciam fases inexistentes (log de warning)
- ✅ `upsert_tarefa()`: Verifica se lista de tarefas existe
- ✅ Ignora tarefas órfãs (sem lista correspondente)
- ✅ Proteção com try/except no session.close()

### 3. Import faltante
**Problema:** `requests.exceptions.HTTPError` sem import de `requests`

**Solução:**
- ✅ Adicionado `import requests` em sync_completo_seguro.py

## 📊 Código de Retry

```python
# Retry automático para erros 401 (token expirado)
fases = []
max_retries = 3
for attempt in range(max_retries):
    try:
        fases = sync_fases(project_id, access_token)
        break  # Sucesso
    except requests.exceptions.HTTPError as http_err:
        if '401' in str(http_err):  # Token expirado
            print(f"  [AVISO] Token expirado na tentativa {attempt+1}/{max_retries}. Renovando...")
            access_token = obter_access_token_zoho()
            token_time = time.time()
            time.sleep(2)
        else:
            raise
    except Exception as e:
        if attempt < max_retries - 1:
            print(f"  [AVISO] Erro na tentativa {attempt+1}/{max_retries}: {e}")
            time.sleep(2)
        else:
            raise
```

## 📋 Código de Validação de Foreign Key

```python
# database.py - upsert_lista_de_tarefas()
fase_id = lista_data.get('milestone', {}).get('id')

# Verificar se fase existe (se fase_id não é None)
if fase_id:
    fase_existe = session.query(Fase).filter(Fase.id == fase_id).first()
    if not fase_existe:
        logger.warning(f"Lista '{lista_data.get('name')}' referencia fase inexistente (ID: {fase_id}). Ignorando esta lista.")
        return
```

## ✅ Resultado Esperado

Com essas correções, o script agora:
1. ✅ Não falha com erro 401 (renova token automaticamente)
2. ✅ Não falha com Foreign Key Violation (valida antes de inserir)
3. ✅ Continua processando mesmo se encontrar dados inconsistentes
4. ✅ Log claro de listas/tarefas ignoradas

## 🚀 Próximo Passo

Execute novamente:
```bash
python sync_completo_seguro.py
```

**Comportamento esperado:**
- Sincronizar ~107 projetos
- Renovar token automaticamente a cada 15min
- Ignorar listas sem fase válida (com warning no log)
- Completar sem erros de Foreign Key
- Tempo estimado: 20-30 minutos
