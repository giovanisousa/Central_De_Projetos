# ⚙️ Configuração do GitHub Actions para Render

## 📋 Secrets Necessários

Configure os seguintes secrets no repositório GitHub:

### Como Adicionar Secrets no GitHub:
1. Acesse: `GitHub → Seu Repositório → Settings → Secrets and variables → Actions`
2. Clique em `New repository secret`
3. Adicione cada secret abaixo

---

## 🔑 Secrets Obrigatórios

### 1. `SYNC_TOKEN`
**Descrição:** Token de autenticação para o endpoint de sincronização

**Como obter:**
- Use o mesmo valor configurado na variável `SYNC_TOKEN` no Render
- Ou gere um novo token seguro:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

**Onde configurar:**
- GitHub: Repository → Settings → Secrets → `SYNC_TOKEN`
- Render: Dashboard → Service → Environment → `SYNC_TOKEN`

⚠️ **IMPORTANTE:** O valor deve ser **idêntico** em ambos os lugares!

---

## 🌐 Secrets Opcionais

### 2. `APP_URL` (Opcional)
**Descrição:** URL da aplicação no Render

**Valor padrão se não configurado:** 
```
https://central-de-projetos.onrender.com
```

**Quando configurar:**
- Se sua URL do Render for diferente da padrão
- Se quiser facilitar mudanças futuras de URL

**Exemplo:**
```
https://seu-nome-app.onrender.com
```

---

## ✅ Checklist de Configuração

### No Render:
- [ ] Variável `SYNC_TOKEN` configurada
- [ ] Variável `DATABASE_URL` configurada (Neon PostgreSQL)
- [ ] Variável `ZOHO_CLIENT_ID` configurada
- [ ] Variável `ZOHO_CLIENT_SECRET` configurada
- [ ] Variável `ZOHO_REFRESH_TOKEN` configurada
- [ ] Variável `SECRET_KEY` configurada (Flask)
- [ ] Deploy concluído com sucesso
- [ ] Aplicação acessível via URL

### No GitHub:
- [ ] Secret `SYNC_TOKEN` adicionado (mesmo valor do Render)
- [ ] Secret `APP_URL` adicionado (opcional)
- [ ] Workflow `.github/workflows/daily-sync.yml` commitado

---

## 🧪 Testando a Configuração

### Teste 1: Verificar se secrets estão configurados
```bash
# No terminal local, teste se consegue acessar o endpoint:
curl -X POST \
  -H "Authorization: Bearer SEU_SYNC_TOKEN" \
  -H "Content-Type: application/json" \
  https://sua-app.onrender.com/api/trigger-sync
```

**Resposta esperada:**
```json
{
  "sucesso": true,
  "mensagem": "Sincronização iniciada em background...",
  "output": "Sincronização em execução. Logs disponíveis no servidor."
}
```

### Teste 2: Executar GitHub Action manualmente
1. Acesse: `GitHub → Actions → Sincronização Diária com Zoho`
2. Clique em `Run workflow`
3. Selecione a branch `main` (ou sua branch atual)
4. Clique em `Run workflow`
5. Aguarde a execução (~10-30 segundos)
6. Verifique os logs:
   - ✅ Verde = sucesso
   - ❌ Vermelho = erro (veja os logs para detalhes)

### Teste 3: Verificar logs no Render
1. Acesse: `Render Dashboard → Seu Service → Logs`
2. Procure por mensagens como:
   ```
   [INFO] api: 🔄 Iniciando sincronização via endpoint /api/trigger-sync
   ✅ Sincronização iniciada em background
   [SYNC] Sincronizando fases de todos os projetos...
   ```

---

## 🔄 Cronograma de Sincronização

O workflow está configurado para:
- **Automática:** Diariamente às 06:00 AM UTC (03:00 horário de Brasília)
- **Manual:** A qualquer momento via interface do GitHub Actions

Para alterar o horário:
```yaml
# Em .github/workflows/daily-sync.yml
on:
  schedule:
    - cron: '0 6 * * *'  # Minuto Hora * * *
```

**Exemplos:**
- `'0 2 * * *'` = 02:00 UTC (23:00 Brasília)
- `'30 14 * * *'` = 14:30 UTC (11:30 Brasília)
- `'0 */6 * * *'` = A cada 6 horas

---

## ❌ Troubleshooting

### Erro: "Token de autorização inválido"
**Causa:** `SYNC_TOKEN` diferente entre GitHub e Render

**Solução:**
1. Verifique o valor em Render: Dashboard → Service → Environment
2. Verifique o secret no GitHub: Settings → Secrets
3. Certifique-se que são **idênticos** (sem espaços extras)

### Erro: "timeout" ou "connection refused"
**Causa:** App não está online ou URL incorreta

**Solução:**
1. Verifique se a aplicação está rodando no Render
2. Acesse a URL diretamente no navegador
3. Verifique o valor de `APP_URL` no GitHub secrets

### Erro 500: "Internal Server Error"
**Causa:** Erro na aplicação ao processar a requisição

**Solução:**
1. Veja os logs do Render para o traceback completo
2. Verifique se todas as variáveis de ambiente estão configuradas
3. Teste o endpoint manualmente com cURL

### Action passa mas sincronização não acontece
**Causa:** Sincronização em background pode estar falhando

**Solução:**
1. Verifique os logs do Render (não os do GitHub Actions)
2. A action só inicia a sincronização, o progresso está nos logs do servidor
3. Procure por erros relacionados ao Zoho API (rate limits, tokens expirados)

---

## 📚 Recursos Adicionais

- [Documentação completa de deploy](DEPLOY.md)
- [GitHub Actions - Documentação oficial](https://docs.github.com/en/actions)
- [Render - Documentação](https://render.com/docs)
- [Zoho Projects API](https://www.zoho.com/projects/help/rest-api/zprojects-api-reference.html)

---

**Última atualização:** 2025-12-01
