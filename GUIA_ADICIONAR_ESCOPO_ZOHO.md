# 🔐 Guia: Adicionar Escopo OAuth para Gerenciamento de Usuários no Zoho Projects

**Data:** 15/10/2025  
**Problema:** Erro 401 INVALID_OAUTHSCOPE ao tentar adicionar usuários ao projeto  
**Solução:** Adicionar escopo correto e re-gerar refresh token

---

## 📋 Escopos Necessários do Zoho Projects

### Escopos Atuais (Implícitos)
O sistema atual usa escopos básicos como:
- `ZohoProjects.projects.ALL` - Gerenciamento de projetos
- `ZohoProjects.tasks.ALL` - Gerenciamento de tarefas
- `ZohoProjects.milestones.READ` - Leitura de fases (documentado em `phases.py`)

### ✅ Escopo Necessário para Adicionar Usuários
Para adicionar usuários aos projetos, precisamos de **um** dos seguintes escopos:

1. **`ZohoProjects.users.ALL`** (Recomendado)
   - Gerenciamento completo de usuários em projetos
   - Inclui: adicionar, remover, atualizar permissões

2. **`ZohoProjects.portals.ALL`** (Alternativa)
   - Acesso completo ao portal, incluindo usuários
   - Mais abrangente (pode ser excessivo)

---

## 🛠️ Passo a Passo para Adicionar o Escopo

### Etapa 1: Acessar Console de Desenvolvedor do Zoho

1. Acesse: https://api-console.zoho.com/
2. Faça login com a conta Animati
3. Vá em **"Self Client"** ou localize o Client ID: `1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR`

### Etapa 2: Gerar Nova URL de Autorização

A URL de autorização deve conter o escopo `ZohoProjects.users.ALL`:

```
https://accounts.zoho.com/oauth/v2/auth?
  scope=ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.milestones.READ,ZohoProjects.users.ALL&
  client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&
  response_type=code&
  access_type=offline&
  redirect_uri=https://www.zoho.com/projects
```

**URL Completa (copie e cole no navegador):**
```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.milestones.READ,ZohoProjects.users.ALL&client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR&response_type=code&access_type=offline&redirect_uri=https://www.zoho.com/projects
```

### Etapa 3: Autorizar e Obter Grant Code

1. Cole a URL no navegador
2. Faça login se solicitado
3. **Autorize** as permissões solicitadas
4. Você será redirecionado para uma URL como:
   ```
   https://www.zoho.com/projects?code=1000.xxxxx.yyyyy&location=us&accounts-server=https://accounts.zoho.com
   ```
5. **Copie o valor do parâmetro `code`** (sem o prefixo `1000.`)

### Etapa 4: Trocar Grant Code por Refresh Token

Execute o seguinte comando `curl` (ou use Postman/Insomnia):

```bash
curl -X POST "https://accounts.zoho.com/oauth/v2/token" \
  -d "grant_type=authorization_code" \
  -d "client_id=1000.FHMB9OAB6ARPGZN1IS5ORTIKNTT1DR" \
  -d "client_secret=70226965d09b04444346222d9b4846c86a5d31d2fe" \
  -d "redirect_uri=https://www.zoho.com/projects" \
  -d "code=SEU_GRANT_CODE_AQUI"
```

**Exemplo de resposta:**
```json
{
  "access_token": "1000.xxxx.yyyy",
  "refresh_token": "1000.zzzz.wwww",
  "expires_in": 3600,
  "api_domain": "https://www.zohoapis.com",
  "token_type": "Bearer"
}
```

### Etapa 5: Salvar Novo Refresh Token

1. Copie o valor de `refresh_token` da resposta
2. Substitua o conteúdo do arquivo `zoho_refresh_token.txt` pelo novo refresh token:
   ```bash
   echo "1000.zzzz.wwww" > zoho_refresh_token.txt
   ```

### Etapa 6: Testar Adição de Usuário

Execute o script de teste:
```bash
python test_add_user_to_project.py
```

**Resultado esperado:**
```
✅ Usuário adicionado ao projeto com sucesso!
Status Code: 200 ou 201
```

---

## 🔍 Verificar Escopos do Token Atual

Para verificar quais escopos o token atual possui, você pode fazer uma requisição de informações do token:

```bash
curl "https://accounts.zoho.com/oauth/v2/token/info" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

---

## 📝 Checklist de Validação

- [ ] Acessou console de desenvolvedor Zoho
- [ ] Gerou URL de autorização com escopo `ZohoProjects.users.ALL`
- [ ] Autorizou e obteve grant code
- [ ] Trocou grant code por refresh token
- [ ] Salvou novo refresh token em `zoho_refresh_token.txt`
- [ ] Testou adição de usuário com `test_add_user_to_project.py`
- [ ] Verificou que requisição retorna 200/201 (sucesso)

---

## 🚨 Notas Importantes

### Sobre Escopos
- Os escopos são **case-sensitive**: `ZohoProjects.users.ALL` ≠ `zohoprojects.users.all`
- Uma vez gerado o refresh token com escopos, **não é possível adicionar escopos sem re-gerar**
- O refresh token **não expira**, mas pode ser revogado manualmente

### Sobre Grant Code
- O grant code é **de uso único** e expira em **60 segundos**
- Se expirar, você precisa gerar uma nova URL de autorização

### Sobre Access Token vs Refresh Token
- **Access Token**: Expira em 1 hora, usado nas requisições à API
- **Refresh Token**: Não expira, usado para gerar novos access tokens
- O sistema atual já gerencia isso automaticamente via `utils.obter_access_token()`

---

## 🔗 Referências

- [Documentação OAuth do Zoho](https://www.zoho.com/projects/help/rest-api/oauth-steps.html)
- [Escopos do Zoho Projects](https://www.zoho.com/projects/help/rest-api/oauth-scopes.html)
- [API de Usuários do Projeto](https://www.zoho.com/projects/help/rest-api/project-users-api.html)
- Arquivo de teste: `test_add_user_to_project.py`
- Issue documentado: `ISSUES_CONHECIDOS.md` (seção "Erro ao Adicionar Usuários")

---

## ✅ Após Implementação

Quando o escopo for adicionado e testado com sucesso:

1. Atualizar `ISSUES_CONHECIDOS.md`:
   - Mover issue de "Problemas Conhecidos" para "Problemas Resolvidos"
   - Adicionar data de resolução e escopo utilizado

2. Documentar escopo em `config.py` (comentário):
   ```python
   # --- ZOHO API ---
   # OAuth Scopes utilizados:
   # - ZohoProjects.projects.ALL
   # - ZohoProjects.tasks.ALL
   # - ZohoProjects.milestones.READ
   # - ZohoProjects.users.ALL (adicionado em 15/10/2025)
   ```

3. Implementar funcionalidade de adicionar usuários no fluxo principal:
   - Adicionar implantadores RIS/PACS automaticamente ao criar projeto
   - Usar payload correto: `{"userdetails": [{"email_id": "..."}], "notify": false}`
