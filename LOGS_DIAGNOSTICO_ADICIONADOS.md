# 🔧 Logs de Diagnóstico Adicionados - Atribuição de Tarefas

## ✅ Modificações Realizadas

Adicionei **logs detalhados** em `implantacao_manager.py` para diagnosticar por que as tarefas não estão sendo atribuídas aos implantadores.

### Arquivo: `implantacao_manager.py`

#### 1. Função `atribuir_tarefa()` (linhas ~143-180)

**Logs adicionados**:
```python
# LOG DETALHADO para diagnóstico
print(f"[DEBUG][ATRIBUIR_TAREFA] URL: {url}")
print(f"[DEBUG][ATRIBUIR_TAREFA] Payload: {payload}")
print(f"[DEBUG][ATRIBUIR_TAREFA] User IDs: {user_ids}")

# ... após a requisição ...

# LOG DA RESPOSTA
print(f"[DEBUG][ATRIBUIR_TAREFA] Status: {response.status_code}")
print(f"[DEBUG][ATRIBUIR_TAREFA] Resposta: {response.text[:500]}")
```

**O que vai revelar**:
- ✅ URL correta da API
- ✅ Payload enviado (campo `owners` e ZPUIDs)
- ✅ Status HTTP da resposta
- ✅ Mensagem de erro da API (se houver)

---

#### 2. Função `adicionar_implantador_e_atribuir_tarefas()` (linhas ~410-550)

**Logs adicionados**:

**a) Início do processo**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ========== INÍCIO ==========")
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Projeto: {project_id}")
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Nome: {nome_implantador}")
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tipo: {tipo_projeto}")
```

**b) Equipe de implantação**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Equipe '{chave_equipe}': {len(equipe[chave_equipe])} membros")
```

**c) Busca do implantador**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Buscando: '{nome_normalizado}'")
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Implantadores disponíveis:")
for idx, imp in enumerate(implantadores, 1):
    print(f"[DEBUG][ADICIONAR_IMPLANTADOR]   {idx}. {imp.get('name')} ({imp.get('email')})")
```

**d) Implantador encontrado**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Encontrado: {implantador.get('name')}")
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Email: {email}")
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ZPUID: {zpuid}")
```

**e) Tarefas para atribuir**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas para atribuir:")
for idx, tarefa in enumerate(tarefas_para_atribuir, 1):
    print(f"[DEBUG][ADICIONAR_IMPLANTADOR]   {idx}. {tarefa}")
```

**f) Tarefas do projeto**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas encontradas no projeto: {len(tarefas_projeto)}")
```

**g) Atribuição de cada tarefa**:
```python
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Tarefa encontrada: '{task_name}' (ID: {task_id})")
# ... após tentar atribuir ...
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Tarefa atribuída: '{task_name}'")
# ou
print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ❌ Falha ao atribuir '{task_name}': {erro_tarefa}")
```

---

## 🎯 Como Usar os Logs

### 1. Executar o Teste

```powershell
python app.py
```

### 2. Agendar Implantação

1. Abra o projeto no Kanban
2. Clique no botão ▶️ "Agendar Implantação"
3. Preencha:
   - Data de início
   - Implantador RIS: **Celio**
   - Implantador PACS: **Marcello**
4. Clique em "Agendar"

### 3. Analisar os Logs no Terminal

Os logs vão aparecer no seguinte formato:

```
[DEBUG][ADICIONAR_IMPLANTADOR] ========== INÍCIO ==========
[DEBUG][ADICIONAR_IMPLANTADOR] Projeto: 2376502000006131101
[DEBUG][ADICIONAR_IMPLANTADOR] Nome: Marcello Roza de Souza
[DEBUG][ADICIONAR_IMPLANTADOR] Tipo: PACS
[DEBUG][ADICIONAR_IMPLANTADOR] Equipe 'Implantação PACS': 5 membros
[DEBUG][ADICIONAR_IMPLANTADOR] Buscando: 'marcello roza de souza'
[DEBUG][ADICIONAR_IMPLANTADOR] Implantadores disponíveis:
[DEBUG][ADICIONAR_IMPLANTADOR]   1. Marcello Roza de Souza (marcello@animati.com.br)
[DEBUG][ADICIONAR_IMPLANTADOR]   2. Pablo Pyerri Ferreira da Costa (pablo@animati.com.br)
[DEBUG][ADICIONAR_IMPLANTADOR]   ...
[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Encontrado: Marcello Roza de Souza
[DEBUG][ADICIONAR_IMPLANTADOR] Email: marcello@animati.com.br
[DEBUG][ADICIONAR_IMPLANTADOR] ZPUID: 868230290000012345
[INFO] implantacao_manager: 🚀 Adicionando implantador Marcello Roza de Souza...
[INFO] implantacao_manager: ✅ Marcello Roza de Souza adicionado com sucesso
[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas para atribuir:
[DEBUG][ADICIONAR_IMPLANTADOR]   1. AP-01 - Preparar ambiente
[DEBUG][ADICIONAR_IMPLANTADOR]   2. AP-02 - Instalar sistema
[DEBUG][ADICIONAR_IMPLANTADOR]   ...
[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas encontradas no projeto: 100
[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Tarefa encontrada: 'AP-01 - Preparar ambiente' (ID: 2376502000006138370)
[DEBUG][ATRIBUIR_TAREFA] URL: https://projectsapi.zoho.com/restapi/portal/868230290/projects/2376502000006131101/tasks/2376502000006138370/
[DEBUG][ATRIBUIR_TAREFA] Payload: {'owners': '868230290000012345'}
[DEBUG][ATRIBUIR_TAREFA] User IDs: ['868230290000012345']
[DEBUG][ATRIBUIR_TAREFA] Status: 200
[DEBUG][ATRIBUIR_TAREFA] Resposta: {"response":"success"}
[INFO] implantacao_manager: ✅ Tarefa 2376502000006138370 atribuída para 1 usuário(s)
[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Tarefa atribuída: 'AP-01 - Preparar ambiente'
```

---

## 🔍 Cenários de Falha Esperados

### Cenário 1: Implantador não encontrado

```
[DEBUG][ADICIONAR_IMPLANTADOR] ❌ Implantador não encontrado!
```

**Causa**: Nome do implantador não corresponde à equipe  
**Solução**: Verificar nome exato no `equipe_implantacao_classificada.json`

---

### Cenário 2: Tarefas não encontradas

```
[DEBUG][ADICIONAR_IMPLANTADOR] ❌ Tarefa não encontrada: 'AP-01 - Preparar ambiente'
```

**Causa**: Tarefa não existe no projeto ou nome diferente  
**Solução**: Verificar nomes das tarefas em `implantacao_config.py`

---

### Cenário 3: API retornando erro

```
[DEBUG][ATRIBUIR_TAREFA] Status: 400
[DEBUG][ATRIBUIR_TAREFA] Resposta: {"error":"Invalid user ID"}
```

**Causa**: ZPUID inválido ou usuário sem permissão  
**Solução**: Verificar se o implantador tem acesso ao projeto

---

### Cenário 4: Sem tarefas no projeto

```
[DEBUG][ADICIONAR_IMPLANTADOR] Tarefas encontradas no projeto: 0
```

**Causa**: Projeto não tem tarefas ou API não retornou  
**Solução**: Aguardar sincronização ou verificar template

---

## 📊 Checklist de Diagnóstico

Com os logs, você poderá identificar:

- [ ] **Implantador encontrado?**
  - ✅ Nome corresponde à equipe?
  - ✅ Email e ZPUID estão corretos?

- [ ] **Implantador adicionado ao projeto?**
  - ✅ API retornou sucesso?
  - ✅ Usuário já estava no projeto?

- [ ] **Tarefas carregadas?**
  - ✅ Lista de tarefas para atribuir está correta?
  - ✅ Tarefas do projeto foram encontradas?

- [ ] **Atribuição funcionando?**
  - ✅ URL da API está correta?
  - ✅ Payload tem o ZPUID correto?
  - ✅ API retorna status 200?
  - ✅ Resposta indica sucesso?

---

## 🚀 Próximos Passos

1. **Execute o teste** com "Agendar Implantação"
2. **Copie os logs** do terminal
3. **Analise** qual cenário de falha ocorreu
4. **Reporte** os logs para investigação mais profunda

---

**Data**: 19/10/2025  
**Status**: ✅ Logs adicionados - Pronto para teste  
**Arquivo modificado**: `implantacao_manager.py`
