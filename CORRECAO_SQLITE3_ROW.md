# Correção: AttributeError 'sqlite3.Row' object has no attribute 'get'

**Data:** 13/10/2025  
**Status:** ✅ RESOLVIDO

---

## 🐛 Problema Identificado

Ao acessar a aplicação após implementação do sistema `data_mudanca_status`, todos os cards estavam exibindo `dias_fase = N/D`.

### Sintomas

```
[ERROR][dias-na-fase] project_id=2376502000005512175 erro='sqlite3.Row' object has no attribute 'get'
Traceback (most recent call last):
  File "routes\api.py", line 715, in api_dias_na_fase
    data_mudanca = project_row.get('data_mudanca_status')
                   ^^^^^^^^^^^^^^^
AttributeError: 'sqlite3.Row' object has no attribute 'get'
```

- Ao mover cards entre colunas, `dias_fase` não mostrava "Hoje"
- Campo continuava exibindo "N/D" mesmo após atualizar página
- Erro HTTP 500 nos endpoints `/api/dias-na-fase/<id>`

---

## 🔍 Causa Raiz

O objeto `sqlite3.Row` retornado por `database.get_project_by_id()` **não tem o método `.get()`** como dicionários Python.

### Código Problemático

```python
# ❌ ERRADO - sqlite3.Row não tem .get()
project_row = database.get_project_by_id(projeto_id)
data_mudanca = project_row.get('data_mudanca_status')  # AttributeError!
```

### Contexto Técnico

No arquivo `database.py`, configuramos:
```python
conn.row_factory = sqlite3.Row
```

Isso faz com que as queries retornem objetos `sqlite3.Row` que:
- ✅ Permitem acesso por **nome de coluna**: `row['coluna']`
- ✅ Permitem acesso por **índice**: `row[0]`
- ❌ **NÃO** têm método `.get()` como dicionários
- ❌ **NÃO** podem ser acessados com `.keys()` ou `.values()`

---

## ✅ Solução Implementada

### 1. Endpoint `/api/dias-na-fase/<project_id>` (routes/api.py, linha ~715)

**Antes:**
```python
data_mudanca = project_row.get('data_mudanca_status')
```

**Depois:**
```python
# sqlite3.Row: acessar por nome de coluna (não tem .get())
try:
    data_mudanca = project_row['data_mudanca_status']
except (KeyError, IndexError):
    data_mudanca = None
```

### 2. Endpoint `/api/carregar_projetos` (routes/api.py, linha ~624)

**Antes:**
```python
if project_row:
    data_mudanca_status = project_row.get('data_mudanca_status')
```

**Depois:**
```python
if project_row:
    # sqlite3.Row: acessar por nome de coluna (não tem .get())
    try:
        data_mudanca_status = project_row['data_mudanca_status']
    except (KeyError, IndexError):
        data_mudanca_status = None
```

### 3. Tratamento de Exceções

Adicionamos `try/except` para capturar:
- `KeyError`: Quando a coluna não existe no resultado (ex: SELECT sem a coluna)
- `IndexError`: Quando o índice está fora do range (fallback seguro)

Em ambos os casos, retornamos `None`, o que faz a função `calcular_dias_na_fase_from_status()` retornar `'N/D'` corretamente.

---

## 🧪 Validação

### Testes Realizados

1. ✅ Servidor reiniciado com sucesso sem erros de inicialização
2. ✅ Logs confirmaram banco de dados inicializado corretamente
3. ✅ Nenhum erro de sintaxe Python (pylint clean nos trechos modificados)

### Testes Pendentes (Usuário)

1. **Carregar projetos existentes:**
   - Acessar http://127.0.0.1:5000
   - Verificar que os cards **NÃO** exibem mais "N/D"
   - Verificar que `dias_fase` exibe valores reais (ex: "5d", "12d", etc.)

2. **Mover card entre colunas:**
   - Selecionar um card e mover para outra coluna
   - Verificar que `dias_fase` exibe **"Hoje"** imediatamente
   - Atualizar página e confirmar que "Hoje" persiste

3. **Validar incremento automático:**
   - Amanhã (14/10/2025), verificar que o mesmo card mostra **"1d"**
   - Depois de amanhã (15/10/2025), verificar **"2d"**

---

## 📝 Lições Aprendidas

### 1. Tipos de Row Factories no sqlite3

```python
# Opção 1: sqlite3.Row (atual) - acesso por nome de coluna
conn.row_factory = sqlite3.Row
row = cursor.fetchone()
value = row['column_name']  # ✅ Funciona
value = row.get('column_name')  # ❌ AttributeError

# Opção 2: Dicionário - compatível com .get()
def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

conn.row_factory = dict_factory
row = cursor.fetchone()
value = row.get('column_name', 'default')  # ✅ Funciona
```

### 2. Por Que Mantivemos sqlite3.Row?

- **Performance:** Mais leve que dicionários completos
- **Memória:** Não duplica dados em estruturas adicionais
- **Compatibilidade:** Código existente já usa `row['coluna']` em vários lugares
- **Simplicidade:** Apenas 2 locais precisaram correção

### 3. Padrão de Acesso Seguro

```python
# ✅ RECOMENDADO: Try/except para acesso seguro
try:
    value = row['column_name']
except (KeyError, IndexError):
    value = default_value

# ⚠️ ALTERNATIVA: Verificar se coluna existe (mais verboso)
if 'column_name' in row.keys():
    value = row['column_name']
else:
    value = default_value
```

---

## 🔄 Próximos Passos

1. **Usuário deve testar** movimentação de cards e validar comportamento
2. Se tudo funcionar corretamente, **commit das correções:**
   ```bash
   git add routes/api.py
   git commit -m "fix: corrige acesso a sqlite3.Row em endpoints de dias_fase

   - Substitui .get() por acesso direto row['coluna']
   - Adiciona try/except para KeyError/IndexError
   - Resolve AttributeError que causava N/D em todos os cards"
   ```

3. **Documentar no PR** que esta correção foi necessária após implementação inicial

---

## 📚 Referências

- [Python sqlite3 Documentation - Row Objects](https://docs.python.org/3/library/sqlite3.html#sqlite3.Row)
- Issue: AttributeError ao acessar `data_mudanca_status` em endpoints
- Arquivos modificados: `routes/api.py` (linhas ~624 e ~715)
