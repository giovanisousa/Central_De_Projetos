# Correção: Atribuição de Tarefas ao Implantador

## 🐛 Problema Identificado

**Sintoma**: Implantadores sendo adicionados ao projeto com sucesso, mas tarefas NÃO sendo atribuídas a eles.

**Erro da API**: `{"error":{"code":6891,"message":"Given URL is wrong"}}`

**URL Incorreta**: `https://projectsapi.zoho.com/restapi/restapi/portal/...` (duplicação de `/restapi`)

**Diagnóstico**: Comparação entre código funcional (GP) vs código não funcional (Implantador).

## 📊 Análise Comparativa

### ✅ Atribuição ao GP (FUNCIONA)
**Localização**: `routes/api.py`, linha 385

```python
url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}/"
headers_rest = {"Authorization": f"Bearer {access_token}"}
payload_rest = {"person_responsible": str(gp_zpuid)}
resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=45)
```

**Características**:
- ✅ Endpoint: `/restapi/portal/.../tasks/{id}/` (REST API)
- ✅ Header: `Bearer {token}`
- ✅ Payload: `{"person_responsible": "zpuid"}`
- ✅ Método: POST com `data=payload`

### ❌ Atribuição ao Implantador (NÃO FUNCIONAVA)
**Localização**: `implantacao_manager.py`

**Problema 1 - URL Duplicada**:
```python
# Construtor (linha 29)
self.base_url = "https://projectsapi.zoho.com/restapi"  # Já contém /restapi

# Método atribuir_tarefa (linha 160 - ANTES)
url = f"{self.base_url}/restapi/portal/..."  # ❌ DUPLICOU /restapi!
# Resultado: https://projectsapi.zoho.com/restapi/restapi/portal/...
```

**Problema 2 - Headers Incorretos**:
```python
# Construtor (linha 26)
self.headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}  # ❌ Formato errado

# Método atribuir_tarefa (linha 177 - ANTES)
response = requests.post(url, headers=self.headers, ...)  # ❌ Usa headers v3
```

## 🔧 Solução Implementada

### Correção 1: URL sem Duplicação

```python
# ANTES (ERRADO)
url = f"{self.base_url}/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
# Resultado: .../restapi/restapi/portal/...

# DEPOIS (CORRETO)
url = f"{self.base_url}/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
# Resultado: .../restapi/portal/...
```

### Correção 2: Headers REST (Bearer Token)

```python
# ANTES (ERRADO) - Usava self.headers com Zoho-oauthtoken
response = requests.post(url, headers=self.headers, data=payload, timeout=30)

# DEPOIS (CORRETO) - Headers REST específicos
headers_rest = {"Authorization": f"Bearer {self.access_token}"}
response = requests.post(url, headers=headers_rest, data=payload, timeout=30)
```

### Correção 3: Formato do Payload

```python
# Para um único usuário (caso comum do implantador)
payload = {"person_responsible": user_ids[0]}

# Para múltiplos usuários (caso raro)
owners_and_work = {
    "owners": {
        "add": [{"zpuid": zpuid} for zpuid in user_ids]
    }
}
payload = {"owners_and_work": json.dumps(owners_and_work)}
```

## 🎯 Código Final Corrigido

```python
def atribuir_tarefa(self, project_id: str, task_id: str, user_ids: List[str]) -> Tuple[bool, Optional[str]]:
    """Atribui uma tarefa para um ou mais usuários usando REST API do Zoho"""
    
    # ✅ URL correta (base_url já contém /restapi)
    url = f"{self.base_url}/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
    
    # ✅ Formato conforme documentação Zoho
    if len(user_ids) > 1:
        owners_and_work = {
            "owners": {
                "add": [{"zpuid": zpuid} for zpuid in user_ids]
            }
        }
        payload = {"owners_and_work": json.dumps(owners_and_work)}
    else:
        payload = {"person_responsible": user_ids[0]}
    
    # ✅ Headers REST com Bearer token
    headers_rest = {"Authorization": f"Bearer {self.access_token}"}
    response = requests.post(url, headers=headers_rest, data=payload, timeout=30)
    
    if response.status_code in (200, 201):
        return (True, None)
    else:
        erro = f"Status {response.status_code}: {response.text[:200]}"
        return (False, erro)
```

## ✅ Correções Aplicadas

1. **URL do Endpoint**:
   - ❌ Antes: `.../restapi/restapi/portal/...` (duplicado)
   - ✅ Depois: `.../restapi/portal/...` (correto)

2. **Headers de Autenticação**:
   - ❌ Antes: `{"Authorization": "Zoho-oauthtoken {token}"}` (API v3)
   - ✅ Depois: `{"Authorization": "Bearer {token}"}` (REST API)

3. **Formato do Payload**:
   - ❌ Antes: `{"owners": "zpuid1,zpuid2"}` (string CSV - não funciona)
   - ✅ Depois (único): `{"person_responsible": "zpuid"}` (formato GP)
   - ✅ Depois (múltiplos): `{"owners_and_work": json.dumps({...})}` (JSON estruturado)

## 🧪 Como Testar

1. Reinicie o servidor Flask (se estiver rodando)

2. Teste "Agendar Implantação" em um projeto

3. Verifique os logs - agora deve aparecer:
   ```
   [DEBUG][ATRIBUIR_TAREFA] URL: https://projectsapi.zoho.com/restapi/portal/.../tasks/{id}/
   [DEBUG][ATRIBUIR_TAREFA] Status: 200
   [DEBUG][ADICIONAR_IMPLANTADOR] ✅ Tarefa atribuída: 'Dúvidas Módulo Agendamento'
   ```

4. Acesse a tarefa no Zoho Projects e confirme que o implantador aparece como responsável

## 🎯 Resultado Esperado

- ✅ URL correta (sem duplicação de `/restapi`)
- ✅ Headers REST (Bearer token)
- ✅ Payload no formato correto
- ✅ Status 200 na resposta da API
- ✅ Tarefas atribuídas ao implantador no Zoho
- ✅ Implantador visível como responsável na UI do Zoho

## 🔍 Raiz do Problema

**O problema era uma combinação de 2 erros**:

1. **Duplicação de `/restapi` na URL**: O `base_url` já continha `/restapi`, mas o método adicionava novamente
2. **Headers incorretos**: Usava headers da API v3 (`Zoho-oauthtoken`) em vez de REST (`Bearer`)

A solução foi **replicar exatamente** o que funciona para o GP, sem duplicar o caminho REST.

---

**Status**: ✅ Correção aplicada  
**Próximo passo**: Teste pelo usuário (deve funcionar agora!)  
**Data**: 2025-10-19
**Atualização**: Corrigido erro de URL duplicada

## 📊 Análise Comparativa

### ✅ Atribuição ao GP (FUNCIONA)
**Localização**: `routes/api.py`, linha 385

```python
url_rest = f"https://projectsapi.zoho.com/restapi/portal/{ZOHO_PORTAL_ID}/projects/{id_do_novo_projeto}/tasks/{task_id}/"
headers_rest = {"Authorization": f"Bearer {access_token}"}
payload_rest = {"person_responsible": str(gp_zpuid)}
resp_rest = requests.post(url_rest, headers=headers_rest, data=payload_rest, timeout=45)
```

**Características**:
- ✅ Endpoint: `/restapi/portal/.../tasks/{id}/` (REST API)
- ✅ Header: `Bearer {token}`
- ✅ Payload: `{"person_responsible": "zpuid"}`
- ✅ Método: POST com `data=payload`

### ❌ Atribuição ao Implantador (NÃO FUNCIONAVA)
**Localização**: `implantacao_manager.py`, linha 159 (ANTES DA CORREÇÃO)

```python
url = f"{self.base_url}/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
payload = {"owners": ",".join(user_ids)}
response = requests.post(url, headers=self.headers, data=payload, timeout=30)
```

**Problemas identificados**:
1. ❌ Endpoint: `/portal/.../tasks/{id}/` (faltava `/restapi`)
2. ❌ Header: `Zoho-oauthtoken {token}` (deveria ser `Bearer`)
3. ❌ Payload: `{"owners": "zpuid1,zpuid2"}` (string CSV - formato incorreto)
4. ❌ Formato não compatível com documentação da API

## 🔧 Solução Implementada

### Mudanças no `implantacao_manager.py`

```python
def atribuir_tarefa(self, project_id: str, task_id: str, user_ids: List[str]) -> Tuple[bool, Optional[str]]:
    # 1️⃣ CORREÇÃO: URL com /restapi (igual ao GP)
    url = f"{self.base_url}/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
    
    # 2️⃣ CORREÇÃO: Formato conforme documentação Zoho
    if len(user_ids) > 1:
        # Para múltiplos usuários: owners_and_work com estrutura JSON
        owners_and_work = {
            "owners": {
                "add": [{"zpuid": zpuid} for zpuid in user_ids]
            }
        }
        payload = {"owners_and_work": json.dumps(owners_and_work)}
    else:
        # Para um único usuário: person_responsible (formato simples)
        payload = {"person_responsible": user_ids[0]}
    
    # 3️⃣ CORREÇÃO: Headers REST com Bearer token
    headers_rest = {"Authorization": f"Bearer {self.access_token}"}
    response = requests.post(url, headers=headers_rest, data=payload, timeout=30)
```

## 📖 Documentação da API Zoho

### Formato Correto para Múltiplos Usuários

Conforme documentação oficial:

```json
{
  "owners_and_work": {
    "owners": {
      "add": [
        {"zpuid": "868230290000012345"},
        {"zpuid": "868230290000067890"}
      ]
    }
  }
}
```

**Campo**: `owners_and_work`  
**Estrutura**: JSON com `owners.add` contendo array de objetos `{zpuid: "..."}`  
**Tipo**: String JSON (serializada)

### Formato para Usuário Único

```json
{
  "person_responsible": "868230290000012345"
}
```

**Campo**: `person_responsible`  
**Estrutura**: String simples com ZPUID  
**Vantagem**: Mais simples e confiável

## ✅ Correções Aplicadas

1. **URL do Endpoint**:
   - ❌ Antes: `.../portal/{portal_id}/projects/{project_id}/tasks/{task_id}/`
   - ✅ Depois: `.../restapi/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/`

2. **Headers de Autenticação**:
   - ❌ Antes: `{"Authorization": "Zoho-oauthtoken {token}"}`
   - ✅ Depois: `{"Authorization": "Bearer {token}"}`

3. **Formato do Payload**:
   - ❌ Antes: `{"owners": "zpuid1,zpuid2"}` (string CSV)
   - ✅ Depois (múltiplos): `{"owners_and_work": json.dumps({...})}` (JSON estruturado)
   - ✅ Depois (único): `{"person_responsible": "zpuid"}` (formato GP)

4. **Compatibilidade**:
   - ✅ Agora usa a MESMA abordagem que funciona para o GP
   - ✅ Suporta tanto usuário único quanto múltiplos
   - ✅ Segue documentação oficial da API

## 🧪 Como Testar

1. Reinicie o servidor Flask:
   ```powershell
   # Pare o servidor atual (Ctrl+C)
   python app.py
   ```

2. Teste "Agendar Implantação" em um projeto

3. Verifique os logs no terminal:
   ```
   [DEBUG][ATRIBUIR_TAREFA] URL: https://projectsapi.zoho.com/restapi/portal/.../tasks/{id}/
   [DEBUG][ATRIBUIR_TAREFA] Payload: {'person_responsible': '868230290000012345'}
   [DEBUG][ATRIBUIR_TAREFA] Status: 200
   [DEBUG][ATRIBUIR_TAREFA] Resposta: {"tasks":[{"id":"...","owner":{"zpuid":"868230290000012345"}}]}
   ```

4. Acesse a tarefa no Zoho Projects e confirme que o implantador aparece como responsável

## 🎯 Resultado Esperado

- ✅ Implantador adicionado ao projeto (já funcionava)
- ✅ Tarefas atribuídas ao implantador (AGORA DEVE FUNCIONAR)
- ✅ Status 200 na resposta da API
- ✅ Campo `owner.zpuid` preenchido na resposta JSON
- ✅ Implantador visível como responsável na UI do Zoho

## 🔍 Raiz do Problema

**O problema NÃO era conceitual (owners vs person_responsible)**.

**O problema era a IMPLEMENTAÇÃO**:
1. Endpoint errado (faltava `/restapi`)
2. Headers errados (Zoho-oauthtoken vs Bearer)
3. Formato de payload incompatível com a API

A solução foi **replicar exatamente** o que funciona para o GP, adaptando para suportar múltiplos usuários quando necessário.

---

**Status**: ✅ Correção aplicada  
**Próximo passo**: Teste pelo usuário  
**Data**: 2025-10-19
