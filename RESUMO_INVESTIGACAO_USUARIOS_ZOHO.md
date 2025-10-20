# ✅ Resumo: Investigação - Erro ao Adicionar Usuários ao Projeto Zoho

**Data:** 15/10/2025  
**Objetivo:** Investigar erro 500 ao adicionar usuários (implantadores) ao projeto via API do Zoho

---

## 🔍 Investigação Realizada

### 1. Teste Criado
Arquivo: `test_add_user_to_project.py`

**Objetivo:** Testar adição de usuário seguindo **documentação oficial** do Zoho Projects API v3

**Payload utilizado (correto segundo docs):**
```json
{
  "userdetails": [{
    "email_id": "camilo.rodrigues@animati.com.br"
  }],
  "notify": false
}
```

**Endpoint:**
```
POST https://projectsapi.zoho.com/api/v3/portal/868230290/projects/2376502000004324882/projectusers
```

### 2. Descoberta Principal

❌ **Erro 401 INVALID_OAUTHSCOPE**

```json
{
  "error": {
    "status_code": "401",
    "title": "INVALID_OAUTHSCOPE",
    "error_type": "FIELDS_VALIDATION_ERROR",
    "details": [{
      "message": "Invalid OAuth scope."
    }]
  }
}
```

**Causa Raiz Identificada:**
> O token de acesso OAuth **não possui o escopo necessário** para adicionar/gerenciar usuários em projetos do Zoho.

---

## 🎯 Conclusões

### ✅ Payload Está Correto
- Formato: `{"userdetails": [{"email_id": "..."}], "notify": false}` ✅
- **NÃO** usar `zpuid` (não existe na documentação oficial)
- Campos opcionais: `profile_id`, `role_id`, `rate` (podem ser adicionados depois)

### ❌ Problema Real: Escopo OAuth Insuficiente
- O erro **NÃO é 500** (como documentado originalmente em ISSUES_CONHECIDOS.md)
- O erro **É 401** - falta de permissão OAuth
- Token atual provavelmente tem apenas escopos básicos:
  - `ZohoProjects.projects.ALL`
  - `ZohoProjects.tasks.ALL`
  - `ZohoProjects.milestones.READ`

### 🔐 Escopo Necessário
**`ZohoProjects.users.ALL`** ou **`ZohoProjects.portals.ALL`**

---

## 📋 Solução Implementada

### 1. Documentação Criada

#### `GUIA_ADICIONAR_ESCOPO_ZOHO.md`
Guia completo passo a passo para:
- Gerar URL de autorização com novo escopo
- Obter grant code
- Trocar grant code por refresh token
- Salvar novo refresh token
- Testar funcionalidade

#### Atualização em `ISSUES_CONHECIDOS.md`
- Atualizado status: "✅ Causa Identificada - Pendente Resolução"
- Documentado erro real: 401 INVALID_OAUTHSCOPE
- Payload correto documentado
- Próximos passos claramente definidos

### 2. Script de Teste
`test_add_user_to_project.py` - Pronto para re-teste após atualização do escopo

---

## 🚀 Próximos Passos

### Imediato (Usuário)
1. Seguir `GUIA_ADICIONAR_ESCOPO_ZOHO.md`
2. Gerar novo refresh token com escopo `ZohoProjects.users.ALL`
3. Salvar em `zoho_refresh_token.txt`
4. Executar `python test_add_user_to_project.py` para validar

### Após Validação (Desenvolvimento)
1. Implementar funcionalidade no fluxo principal:
   - Adicionar implantadores automaticamente ao criar projeto
   - Usar payload correto: `{"userdetails": [{"email_id": "..."}], "notify": false}`
   
2. Adicionar tratamento de erros específico:
   ```python
   if response.status_code == 401:
       if "INVALID_OAUTHSCOPE" in response.text:
           logging.error("Token OAuth sem permissão para gerenciar usuários")
   ```

3. Documentar escopo em `config.py`:
   ```python
   # OAuth Scopes utilizados:
   # - ZohoProjects.projects.ALL
   # - ZohoProjects.tasks.ALL
   # - ZohoProjects.milestones.READ
   # - ZohoProjects.users.ALL (adicionado em 15/10/2025)
   ```

4. Atualizar `ISSUES_CONHECIDOS.md`:
   - Mover para "Problemas Resolvidos"
   - Adicionar data de resolução

---

## 📊 Diferença: Documentado vs Realidade

| Aspecto | ISSUES_CONHECIDOS.md (Antes) | Descoberta Atual |
|---------|------------------------------|------------------|
| **Status Code** | 500 Internal Server Error | 401 Unauthorized |
| **Erro** | Servidor Zoho | OAuth Scope |
| **Causa Hipótese** | Campo `zpuid` incorreto | Token sem permissão |
| **Payload** | `{"email_id": "...", "zpuid": "..."}` | `{"email_id": "..."}` apenas |
| **Solução** | Investigar API | Adicionar escopo OAuth |

---

## ✨ Lições Aprendidas

1. **Sempre seguir documentação oficial** da API
   - Documentação Zoho Projects v3 não menciona campo `zpuid`
   - Campo `email_id` é suficiente

2. **Erros 401 vs 500 têm causas diferentes**
   - 401: Autenticação/Autorização (OAuth scopes)
   - 500: Erro interno do servidor (bug ou payload malformado)

3. **OAuth scopes são granulares**
   - Acesso a projetos ≠ Acesso a gerenciar usuários
   - Cada funcionalidade pode precisar de escopo específico

4. **Testar com script isolado é eficaz**
   - Permite identificar causa raiz rapidamente
   - Evita misturar erros de lógica de negócio com erros de API

---

## 📁 Arquivos Criados/Atualizados

### Criados
- ✅ `test_add_user_to_project.py` - Script de teste standalone
- ✅ `GUIA_ADICIONAR_ESCOPO_ZOHO.md` - Guia passo a passo
- ✅ `RESUMO_INVESTIGACAO_USUARIOS_ZOHO.md` - Este arquivo

### Atualizados
- ✅ `ISSUES_CONHECIDOS.md` - Status atualizado, causa raiz identificada

---

## 🔗 Referências

- **Documentação Oficial:**
  - [Zoho Projects - Add Users to Project](https://www.zoho.com/projects/help/rest-api/project-users-api.html#alink4)
  - [Zoho OAuth Scopes](https://www.zoho.com/projects/help/rest-api/oauth-scopes.html)
  
- **Arquivos do Projeto:**
  - `test_add_user_to_project.py` - Script de teste
  - `GUIA_ADICIONAR_ESCOPO_ZOHO.md` - Guia de implementação
  - `ISSUES_CONHECIDOS.md` - Issues e melhorias
  - `phases.py` - Exemplo de escopo OAuth documentado

---

**Status Final:** ✅ Causa raiz identificada. Aguardando atualização de escopo OAuth pelo usuário.
