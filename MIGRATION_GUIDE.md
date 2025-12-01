# 🎯 Guia Rápido - Migração Railway → Render

## Status Atual
✅ Código atualizado para Render  
✅ Sincronização automática no boot desabilitada (evita timeout)  
✅ GitHub Actions configurado para Render  
✅ Documentação completa criada  

---

## 📝 Próximos Passos

### 1️⃣ Fazer Push do Código
```bash
# Se estiver na branch feature/sincronizacao-render:
git push origin feature/sincronizacao-render

# Depois, merge na main:
git checkout main
git merge feature/sincronizacao-render
git push origin main
```

### 2️⃣ Configurar Variáveis de Ambiente no Render

**Acesse:** Render Dashboard → Seu Service → Environment

Adicione as seguintes variáveis:

```bash
# Banco de Dados (Neon PostgreSQL)
DATABASE_URL=postgresql://usuario:senha@host/database

# Zoho API
ZOHO_CLIENT_ID=seu_client_id
ZOHO_CLIENT_SECRET=seu_client_secret  
ZOHO_REFRESH_TOKEN=seu_refresh_token

# Flask
SECRET_KEY=sua_secret_key_aleatoria

# Token de Sincronização (gere um novo token seguro)
SYNC_TOKEN=seu_token_seguro_aqui
```

**Para gerar SYNC_TOKEN:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3️⃣ Configurar Secrets no GitHub

**Acesse:** GitHub → Repositório → Settings → Secrets and variables → Actions

Adicione:
- **`SYNC_TOKEN`** = Mesmo valor configurado no Render
- **`APP_URL`** (opcional) = URL da sua app no Render

### 4️⃣ Fazer Deploy no Render

O Render detectará o push automaticamente e fará o build.

**O que vai acontecer:**
- ✅ Build e deploy (~2-3 minutos)
- ✅ Aplicação inicia sem erros
- ✅ Logs mostram: `⚠️ Banco de dados vazio! Execute sincronização...`
- ✅ **SEM TIMEOUT** - deploy completa normalmente

### 5️⃣ Executar Primeira Sincronização

**Opção A - Via GitHub Actions (Recomendado):**
1. GitHub → Actions → "Sincronização Diária com Zoho"
2. Run workflow → main → Run workflow
3. Aguarde ~1 minuto (só inicia a sincronização)
4. Acompanhe progresso nos logs do Render (~5-10 minutos)

**Opção B - Via cURL:**
```bash
curl -X POST \
  -H "Authorization: Bearer SEU_SYNC_TOKEN" \
  -H "Content-Type: application/json" \
  https://sua-app.onrender.com/api/trigger-sync
```

### 6️⃣ Verificar Sincronização nos Logs do Render

**Acesse:** Render Dashboard → Logs

Procure por:
```
[INFO] api: 🔄 Iniciando sincronização via endpoint /api/trigger-sync
✅ Sincronização iniciada em background
[SYNC] Sincronizando fases de todos os projetos...
[1/107] Sincronizando fases do projeto: Nome do Projeto
✓ X fases sincronizadas
...
✅ Sincronização concluída com sucesso!
```

---

## 📚 Documentação Disponível

### 1. **DEPLOY.md**
- Guia completo de deploy no Render
- Como fazer primeira sincronização
- Troubleshooting detalhado
- Checklist pós-deploy

### 2. **GITHUB_ACTIONS_CONFIG.md**
- Como configurar secrets do GitHub
- Testes passo-a-passo
- Troubleshooting do GitHub Actions
- Exemplos de configuração de cron

### 3. **README.md** (se existir)
- Visão geral do projeto
- Funcionalidades principais

---

## 🔄 Sincronização Automática

**Frequência:** Diariamente às 06:00 AM UTC (03:00 horário de Brasília)

**Configurado em:** `.github/workflows/daily-sync.yml`

**Para alterar horário:** Edite o cron no arquivo YAML

---

## ✅ Checklist de Migração

### No Render:
- [ ] Serviço criado e conectado ao GitHub
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Deploy concluído com sucesso
- [ ] Aplicação acessível via URL
- [ ] Logs mostram app iniciado sem erros

### No GitHub:
- [ ] Secret `SYNC_TOKEN` configurado
- [ ] Secret `APP_URL` configurado (opcional)
- [ ] Código commitado e pushed
- [ ] Workflow testado manualmente
- [ ] Workflow passou sem erros

### Pós-Deploy:
- [ ] Primeira sincronização executada
- [ ] Logs do Render mostram sincronização completa
- [ ] Aplicação exibe projetos corretamente
- [ ] GitHub Actions rodando automaticamente

---

## 🆘 Suporte

Se encontrar problemas:

1. **Confira os logs** do Render primeiro
2. **Verifique** se todos os secrets/variáveis estão configurados
3. **Consulte** DEPLOY.md ou GITHUB_ACTIONS_CONFIG.md
4. **Teste** o endpoint manualmente com cURL

---

## 🎉 Pronto!

Após seguir todos os passos, sua aplicação estará:
- ✅ Rodando no Render
- ✅ Sincronizando automaticamente todo dia
- ✅ Sem problemas de timeout
- ✅ Com logs detalhados para debug

**Boa sorte com o deploy! 🚀**
