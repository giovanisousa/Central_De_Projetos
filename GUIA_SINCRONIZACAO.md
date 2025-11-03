# 🔄 Guia Completo de Sincronização - Central de Projetos

## 📋 Índice
1. [Configuração Inicial](#configuração-inicial)
2. [Configurando Sincronização Automática](#configurando-sincronização-automática)
3. [Como Executar Sincronizações](#como-executar-sincronizações)
4. [Monitoramento e Logs](#monitoramento-e-logs)
5. [Resolução de Problemas](#resolução-de-problemas)

---

## 🚀 Configuração Inicial

### Passo 1: Deploy do Código no Railway

1. **Commit e Push das alterações**
   ```bash
   git add .
   git commit -m "feat: Sistema completo de sincronização automática"
   git push origin manual-atualizacao
   ```

2. **Criar Pull Request e Fazer Merge**
   - Acesse: https://github.com/giovanisousa/Central_De_Projetos
   - Clique em "Pull Requests" → "New Pull Request"
   - Selecione a branch `manual-atualizacao` → `main`
   - Clique em "Create Pull Request"
   - Revise as mudanças e clique em "Merge Pull Request"

3. **Aguardar Deploy Automático**
   - O Railway detectará o novo commit na branch `main`
   - Aguarde 2-5 minutos para o deploy completar
   - Verifique em: https://railway.app/dashboard

### Passo 2: Configurar Railway CLI (Para Sincronização Manual)

1. **Instalar Railway CLI**
   ```powershell
   # No PowerShell como Administrador
   npm install -g @railway/cli
   ```

2. **Fazer Login**
   ```powershell
   railway login
   ```
   - Uma janela do navegador abrirá
   - Faça login com sua conta Railway
   - Volte ao terminal

3. **Conectar ao Projeto**
   ```powershell
   cd "C:\Users\Giovani Souza\Documents\Central_De_Projetos"
   railway link
   ```
   - Selecione seu projeto (Central_De_Projetos)
   - Selecione o ambiente (production)

### Passo 3: Gerar Token do Railway

1. **Gerar Token de Acesso**
   ```powershell
   railway token
   ```
   - Copie o token gerado (formato: `railway_xxx...`)

2. **⚠️ IMPORTANTE: Guarde o token em local seguro**
   - Este token será usado para sincronização automática
   - Não compartilhe este token publicamente

---

## 🤖 Configurando Sincronização Automática

### Passo 4: Configurar GitHub Secret

1. **Acessar Configurações do Repositório**
   - Vá para: https://github.com/giovanisousa/Central_De_Projetos/settings/secrets/actions

2. **Adicionar Novo Secret**
   - Clique em "New repository secret"
   - **Name:** `RAILWAY_TOKEN`
   - **Value:** Cole o token gerado no Passo 3
   - Clique em "Add secret"

### Passo 5: Verificar GitHub Action

1. **Confirmar que o arquivo existe**
   - Vá para: https://github.com/giovanisousa/Central_De_Projetos/blob/main/.github/workflows/daily-sync.yml

2. **A sincronização automática está configurada para:**
   - ⏰ Executar todo dia às **02:00 AM UTC** (23:00 horário de Brasília)
   - 🔄 Sincronizar todas as fases de todos os projetos
   - 📊 Evitar timeout usando Railway CLI diretamente

---

## 🔧 Como Executar Sincronizações

### Opção 1: Via Interface Web (Recomendado para testes rápidos)

#### Sincronização Completa (Projetos + Fases)
```javascript
// No navegador, abra o Console (F12) e execute:
fetch('/api/sync-complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        force: true,
        phases_only: false
    })
})
.then(r => r.json())
.then(data => console.log('Job ID:', data.job_id));
```

#### Sincronização Apenas de Fases
```javascript
fetch('/api/sync-complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        phases_only: true
    })
})
.then(r => r.json())
.then(data => console.log('Job ID:', data.job_id));
```

**⚠️ ATENÇÃO:** A execução via web pode ser interrompida após 30 segundos devido ao timeout do Gunicorn. Use para testes apenas.

---

### Opção 2: Via Railway CLI (Recomendado para sincronização completa)

#### Sincronização Inicial (Primeira vez - EXECUTE ISSO PRIMEIRO!)
```powershell
# Sincronizar TODAS as fases de TODOS os projetos
railway run python sync_complete.py --phases-only
```

**Resultado esperado:**
```
=== SINCRONIZAÇÃO COMPLETA ===
Estatísticas ANTES:
- Total de projetos: 100
- Total de fases: 100
- Média de fases por projeto: 1.0

[SYNC] Sincronizando fases para todos os projetos...
[SYNC] Processando projeto 1/100...
[SYNC] Processando projeto 2/100...
...
[SYNC] ✅ Sincronização completa concluída!

Estatísticas DEPOIS:
- Total de projetos: 100
- Total de fases: 800
- Média de fases por projeto: 8.0
```

#### Sincronização Forçada (Reprocessar tudo)
```powershell
# Força re-sincronização de todos os projetos e fases
railway run python sync_complete.py --force
```

#### Sincronizar Projeto Específico
```powershell
# Substituir PROJECT_ID pelo ID do projeto Zoho
railway run python sync_complete.py --project-id=PROJECT_ID
```

---

### Opção 3: Via GitHub Actions (Manual)

1. **Acessar Actions**
   - Vá para: https://github.com/giovanisousa/Central_De_Projetos/actions

2. **Executar Workflow Manualmente**
   - Clique em "Daily Sync - Zoho Projects"
   - Clique em "Run workflow"
   - Selecione a branch `main`
   - Clique em "Run workflow"

3. **Acompanhar Execução**
   - Clique no workflow em execução
   - Expanda "Run sync script"
   - Veja os logs em tempo real

---

### Opção 4: Via Script Python Local (Não recomendado)

```powershell
# ⚠️ Isso executará localmente e pode demorar 10-30 minutos
python sync_complete.py --phases-only
```

**Desvantagens:**
- Requer configuração local de credenciais
- Pode ser interrompido se fechar o terminal
- Não tem os mesmos recursos do servidor

---

## 📊 Monitoramento e Logs

### Ver Logs do Railway

#### Em Tempo Real
```powershell
railway logs
```

#### Filtrar Logs de Sincronização
```powershell
railway logs | Select-String "SYNC"
```

#### Ver Últimas 100 Linhas
```powershell
railway logs --tail 100
```

### Ver Logs no Dashboard

1. Acesse: https://railway.app/dashboard
2. Selecione seu projeto
3. Clique em "Deployments"
4. Clique no deployment ativo
5. Veja a aba "Logs"

### Verificar Status no Banco de Dados

```python
# Conecte ao banco via Railway CLI
railway run python

# No Python:
from database import db, Project, Fase

# Ver total de projetos
total_projetos = Project.query.count()
print(f"Total de projetos: {total_projetos}")

# Ver total de fases
total_fases = Fase.query.count()
print(f"Total de fases: {total_fases}")

# Ver média de fases por projeto
media = total_fases / total_projetos if total_projetos > 0 else 0
print(f"Média de fases por projeto: {media:.1f}")
```

---

## 🔍 Resolução de Problemas

### Problema: "GitHub Action falhou com erro de autenticação"

**Causa:** Token do Railway inválido ou expirado

**Solução:**
1. Gerar novo token:
   ```powershell
   railway token
   ```
2. Atualizar secret no GitHub:
   - https://github.com/giovanisousa/Central_De_Projetos/settings/secrets/actions
   - Editar `RAILWAY_TOKEN`
   - Colar novo token

---

### Problema: "Sincronização via web dá timeout"

**Causa:** Sincronização demora mais de 30 segundos

**Solução:** Use Railway CLI ao invés da interface web:
```powershell
railway run python sync_complete.py --phases-only
```

---

### Problema: "Poucas fases no banco (menos de 500)"

**Causa:** Sincronização inicial nunca foi executada

**Solução:** Execute a sincronização inicial:
```powershell
railway run python sync_complete.py --phases-only
```

**Resultado esperado:** ~800 fases (100 projetos × 8 fases cada)

---

### Problema: "Erro ao conectar via Railway CLI"

**Causa:** Não está linkado ao projeto correto

**Solução:**
```powershell
cd "C:\Users\Giovani Souza\Documents\Central_De_Projetos"
railway link
# Selecione o projeto e ambiente corretos
```

---

### Problema: "Dados desatualizados na interface"

**Causa:** Cache do navegador

**Solução:**
1. Limpar cache: `Ctrl + Shift + R` (Windows)
2. Ou sincronizar novamente:
   ```powershell
   railway run python sync_complete.py --phases-only
   ```

---

## 📅 Cronograma de Sincronização

### Automática (Configurada)
- ⏰ **Diariamente às 02:00 AM UTC** (23:00 horário de Brasília)
- 🔄 Sincroniza todas as fases de todos os projetos
- 📧 Notificação em caso de falha (via GitHub)

### Manual (Quando necessário)
- 🆕 Após criar novo projeto no Zoho
- 🔧 Após mudanças importantes em fases
- 🐛 Após correção de bugs que afetam dados
- ✅ Após deploy de novas funcionalidades

**Comando rápido:**
```powershell
railway run python sync_complete.py --phases-only
```

---

## ⚡ Resumo dos Comandos Principais

### Configuração (Executar uma vez)
```powershell
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Conectar ao projeto
cd "C:\Users\Giovani Souza\Documents\Central_De_Projetos"
railway link

# 4. Gerar token (copiar para GitHub Secrets)
railway token
```

### Sincronização Inicial (Executar após deploy)
```powershell
railway run python sync_complete.py --phases-only
```

### Sincronização Rápida (Dia a dia)
```powershell
railway run python sync_complete.py --phases-only
```

### Ver Logs
```powershell
railway logs | Select-String "SYNC"
```

---

## 📞 Suporte

### Arquivos de Referência
- 📄 `sync_complete.py` - Script de sincronização
- 📄 `SINCRONIZACAO.md` - Documentação técnica detalhada
- 📄 `.github/workflows/daily-sync.yml` - Configuração do cronjob

### Verificações de Saúde
```powershell
# Ver estatísticas atuais
railway run python -c "from database import db, Project, Fase; from sqlalchemy import func; print(f'Projetos: {Project.query.count()}'); print(f'Fases: {Fase.query.count()}'); print(f'Média: {Fase.query.count() / Project.query.count():.1f}')"
```

---

## ✅ Checklist de Configuração Completa

- [ ] Código deployado no Railway (main branch)
- [ ] Railway CLI instalado e conectado
- [ ] Token do Railway gerado
- [ ] Secret `RAILWAY_TOKEN` configurado no GitHub
- [ ] GitHub Action ativada e funcionando
- [ ] Sincronização inicial executada (`--phases-only`)
- [ ] Logs verificados sem erros
- [ ] Estatísticas do banco confirmadas (~800 fases)

**Após completar todos os itens, seu sistema estará 100% funcional! 🎉**
