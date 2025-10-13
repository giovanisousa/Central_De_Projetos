# 🔍 Diagnóstico Detalhado - Adição de Usuários ao Projeto

## 📋 Logs Implementados

### 1. Logs Iniciais - Coleta de Dados dos Implantadores

```
================================================================================
[INFO] ETAPA 2: ADICIONANDO USUÁRIOS AO PROJETO
================================================================================

[DEBUG] 📋 DADOS DOS IMPLANTADORES:
[DEBUG]   RIS:
[DEBUG]     - Nome: Pablo Pyerri Ferreira da Costa
[DEBUG]     - ZPUID: 2376502000000080073
[DEBUG]     - Email: pablo.pyerri@animati.com.br
[DEBUG]   PACS:
[DEBUG]     - Nome: Aneidia Sa
[DEBUG]     - ZPUID: 2376502000004578023
[DEBUG]     - Email: aneidia.sa@animati.com.br
```

### 2. Logs de Verificação de Usuário

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[DEBUG][CHECK_USER] 🔍 VERIFICANDO USUÁRIO NO PROJETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[DEBUG][CHECK_USER] 🔗 URL: https://projectsapi.zoho.com/api/v3/portal/868230290/projects/2376502000005995871/projectusers
[DEBUG][CHECK_USER] 🆔 ZPUID procurado: 2376502000000080073
[DEBUG][CHECK_USER] 📨 Status Code: 200
[DEBUG][CHECK_USER] 👥 Total de usuários no projeto: 15
[DEBUG][CHECK_USER] 📋 Primeiros usuários:
[DEBUG][CHECK_USER]   1. ZPUID: 2376502000000080001, Email: usuario1@animati.com.br, Nome: Usuario 1
[DEBUG][CHECK_USER]   2. ZPUID: 2376502000000080002, Email: usuario2@animati.com.br, Nome: Usuario 2
[DEBUG][CHECK_USER]   ...
[DEBUG][CHECK_USER] ❌ Usuário 2376502000000080073 NÃO encontrado no projeto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. Logs de Adição de Usuário

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[DEBUG][ADD_USER] 📤 TENTATIVA DE ADICIONAR USUÁRIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[DEBUG][ADD_USER] 🔗 URL: https://projectsapi.zoho.com/api/v3/portal/868230290/projects/2376502000005995871/projectusers
[DEBUG][ADD_USER] 📧 Email: pablo.pyerri@animati.com.br
[DEBUG][ADD_USER] 🆔 ZPUID: 2376502000000080073
[DEBUG][ADD_USER] 📦 Payload: {
    "userdetails": [{
        "email_id": "pablo.pyerri@animati.com.br",
        "zpuid": "2376502000000080073"
    }],
    "notify": "false"
}
[DEBUG][ADD_USER] 🔑 Token (primeiros 50 chars): 1000.8d8275545982f7cc886d1a95f09db153.9902ed8f2e...
[DEBUG][ADD_USER] 📨 Status Code: 201
[DEBUG][ADD_USER] 📄 Response Headers: {...}
[DEBUG][ADD_USER] 📝 Response Body: {"message": "User added successfully", ...}
[SUCCESS][ADD_USER] ✅ Usuário pablo.pyerri@animati.com.br adicionado ao projeto 2376502000005995871
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4. Logs de Resumo Intermediário

```
[INFO] 📊 RESUMO DA ADIÇÃO DE USUÁRIOS:
[INFO]   RIS  - Tentou: True, Já estava: False, Adicionado: True
[INFO]   PACS - Tentou: True, Já estava: False, Adicionado: True
================================================================================
```

### 5. Relatório Final Completo

```
================================================================================
[INFO] RELATÓRIO FINAL DE PROCESSAMENTO
================================================================================
[INFO] 📊 ESTATÍSTICAS GERAIS:
[INFO]   - Total de tarefas processadas: 344
[INFO]   - Usuários adicionados ao projeto: 2
[INFO]   - Datas de início atualizadas: 0
[INFO]   - Tarefas RIS atribuídas: 10
[INFO]   - Tarefas PACS atribuídas: 8
[INFO]   - Erros encontrados: 0

[INFO] 👥 DETALHAMENTO DA ADIÇÃO DE USUÁRIOS:
[INFO] 🔹 IMPLANTADOR RIS (Pablo Pyerri Ferreira da Costa):
[INFO]   - ZPUID encontrado: ✓ (2376502000000080073)
[INFO]   - Email encontrado: ✓ (pablo.pyerri@animati.com.br)
[INFO]   - Já estava no projeto: ✗
[INFO]   - Tentou adicionar: ✓
[INFO]   - Adicionado com sucesso: ✓

[INFO] 🔹 IMPLANTADOR PACS (Aneidia Sa):
[INFO]   - ZPUID encontrado: ✓ (2376502000004578023)
[INFO]   - Email encontrado: ✓ (aneidia.sa@animati.com.br)
[INFO]   - Já estava no projeto: ✗
[INFO]   - Tentou adicionar: ✓
[INFO]   - Adicionado com sucesso: ✓
================================================================================
```

---

## 🎯 O Que Cada Log Revela

### ✅ Log de Verificação de Usuário
**Identifica:**
- Se a API de listagem de usuários está funcionando
- Quantos usuários já estão no projeto
- Se o ZPUID procurado está correto
- Se o usuário já existe (evitando tentativa duplicada)

### ✅ Log de Adição de Usuário
**Identifica:**
- URL exata da requisição
- Payload completo enviado
- Token utilizado (parcial, por segurança)
- Status code da resposta
- Headers da resposta
- Body completo da resposta (até 1000 chars)
- Mensagem de erro detalhada (se houver)

### ✅ Log de Resumo
**Identifica:**
- Se os dados foram coletados corretamente
- Se a tentativa de adicionar foi feita
- Se o usuário já estava no projeto
- Se a adição foi bem-sucedida
- Erros específicos (se houver)

---

## 🔧 Como Usar os Logs para Diagnóstico

### Cenário 1: Usuários não encontrados
**Se aparecer:**
```
[WARN] ⚠️ Dados insuficientes para adicionar implantador RIS
[WARN]    - ZPUID RIS não encontrado
```

**Problema:** O ZPUID não foi encontrado no arquivo `equipe_implantacao_classificada.json`

**Solução:** Verificar se o nome do implantador selecionado está exatamente igual ao registrado no JSON

---

### Cenário 2: Erro 403 na adição
**Se aparecer:**
```
[ERROR][ADD_USER] ❌ Falha ao adicionar usuário
[ERROR][ADD_USER] Status: 403
[ERROR][ADD_USER] Response completo: {"code": 6831, "message": "Permission denied"}
```

**Problemas possíveis:**
1. Token sem permissões adequadas
2. Usuário não tem permissão para adicionar usuários ao projeto
3. ZPUID inválido ou de outro portal

**Solução:** Verificar permissões do token e ZPUID

---

### Cenário 3: Usuário já existe
**Se aparecer:**
```
[DEBUG][CHECK_USER] ✅ Usuário 2376502000000080073 ENCONTRADO no projeto
[INFO] ✓ Implantador RIS já está no projeto
```

**Resultado:** Sistema pula a etapa de adição (comportamento correto)

---

### Cenário 4: Erro na API do Zoho
**Se aparecer:**
```
[ERROR][CHECK_USER] ❌ Erro ao verificar usuários: 500
[ERROR][CHECK_USER] Response: {"error": "Internal server error"}
```

**Problema:** API do Zoho com problemas temporários

**Solução:** Tentar novamente após alguns minutos

---

## 📊 Interpretando o Relatório Final

### ✅ Caso de Sucesso Completo
```
[INFO] Usuários adicionados ao projeto: 2
[INFO] RIS  - Tentou: True, Já estava: False, Adicionado: True
[INFO] PACS - Tentou: True, Já estava: False, Adicionado: True
```
**Resultado:** Ambos implantadores foram adicionados com sucesso

---

### ⚠️ Caso de Usuários Já Existentes
```
[INFO] Usuários adicionados ao projeto: 0
[INFO] RIS  - Tentou: False, Já estava: True, Adicionado: False
[INFO] PACS - Tentou: False, Já estava: True, Adicionado: False
```
**Resultado:** Usuários já estavam no projeto (ok)

---

### ❌ Caso de Falha
```
[INFO] Usuários adicionados ao projeto: 0
[INFO] RIS  - Tentou: True, Já estava: False, Adicionado: False
[ERROR]  - Erro: 403 Client Error: Forbidden
```
**Resultado:** Tentou adicionar mas falhou (verificar logs detalhados acima)

---

## 🚀 Próximos Passos para Diagnóstico

1. **Execute o processo de agendamento**
2. **Procure no console pelos logs formatados:**
   - Seção `ETAPA 2: ADICIONANDO USUÁRIOS`
   - Logs de `[CHECK_USER]`
   - Logs de `[ADD_USER]`
   - `RELATÓRIO FINAL`

3. **Analise as informações coletadas:**
   - ZPUIDs foram encontrados?
   - Emails foram encontrados?
   - Usuários já estavam no projeto?
   - Status code das requisições (200, 201, 403, etc.)
   - Mensagens de erro específicas

4. **Compartilhe os logs relevantes** para análise detalhada

---

**Data:** 12 de outubro de 2025  
**Versão:** 2.0 - Logs Detalhados e Estruturados
