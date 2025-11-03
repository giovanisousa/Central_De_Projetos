# Sistema de Sincronização Completa

## 📋 Visão Geral

Sistema de sincronização automática e manual com o Zoho Projects que mantém o banco de dados local atualizado com:
- Informações dos projetos
- Fases (milestones) de cada projeto
- Listas de tarefas
- Tarefas impeditivas

## ⚠️ IMPORTANTE: Timeout e Execução Assíncrona

**A sincronização completa pode levar 10-30 minutos**, muito além do limite de 30 segundos do Railway para requisições HTTP.

**Soluções implementadas:**
- ✅ **Via Railway CLI**: Executa diretamente no servidor (sem timeout)
- ✅ **Via GitHub Actions**: Usa Railway CLI (sem timeout)
- ✅ **Via API com async=true**: Executa em background, retorna imediatamente
- ❌ **Via API com async=false**: Causará timeout após 30s (NÃO RECOMENDADO)

## 🕐 Sincronização Automática (Diária às 02:00 AM)

### Configuração no Railway + GitHub Actions

A sincronização diária usa **Railway CLI** via GitHub Actions para executar o script diretamente no servidor (sem timeout HTTP).

### Passos para configurar:

1. **Obter Railway Token**:
   ```bash
   # No seu computador local, faça login no Railway
   railway login
   
   # Gere um token de projeto
   railway token
   ```

2. **No repositório GitHub**, vá em `Settings` → `Secrets and variables` → `Actions`

3. **Adicione o secret**:
   - Nome: `RAILWAY_TOKEN`
   - Valor: (cole o token gerado acima)

4. **O arquivo `.github/workflows/daily-sync.yml` já está configurado** para:
   - Executar automaticamente às 02:00 AM UTC todos os dias
   - Usar Railway CLI para executar `python sync_complete.py --phases-only` diretamente no servidor
   - **Sem timeout HTTP** (pode levar 30+ minutos sem problemas)
   - Permitir execução manual via interface do GitHub

### Como executar manualmente via GitHub:

1. Acesse: `Actions` → `Sincronização Diária com Zoho`
2. Clique em `Run workflow` → `Run workflow`

## 🔧 Execução Manual

### Opção 1: Via Comando no Servidor Railway

```bash
# SSH no container do Railway (se disponível) e execute:

# Sincronização completa (projetos + fases)
python sync_complete.py

# Forçar sincronização de TODOS os projetos (ignora last_modified_time)
python sync_complete.py --force

# Sincronizar apenas as fases dos projetos existentes
python sync_complete.py --phases-only

# Sincronizar um projeto específico
python sync_complete.py --project-id=2376502000001234567
```

### Opção 2: Via API REST (Execução em Background)

⚠️ **IMPORTANTE**: O endpoint executa em **background por padrão** para evitar timeout.

#### Sincronização completa em background (RECOMENDADO):
```bash
curl -X POST https://seu-app.railway.app/api/sync-complete \
  -H "Content-Type: application/json"

# Resposta imediata:
# {
#   "status": "started",
#   "message": "Sincronização iniciada em background",
#   "job_id": "abc123",
#   "note": "Acompanhe o progresso nos logs..."
# }
```

#### Sincronizar apenas fases em background:
```bash
curl -X POST https://seu-app.railway.app/api/sync-complete \
  -H "Content-Type: application/json" \
  -d '{"phases_only": true}'
```

#### Forçar sincronização completa em background:
```bash
curl -X POST https://seu-app.railway.app/api/sync-complete \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

#### Execução síncrona (NÃO RECOMENDADO - causará timeout):
```bash
curl -X POST https://seu-app.railway.app/api/sync-complete \
  -H "Content-Type: application/json" \
  -d '{"async": false}'
# ⚠️ Timeout após 30 segundos!
```

### Opção 3: Via Interface Web (Futuro)

Você pode adicionar um botão na interface administrativa para chamar o endpoint `/api/sync-complete`.

## 📊 Resposta da API

### Modo Assíncrono (padrão - sem timeout):
```json
{
  "status": "started",
  "message": "Sincronização iniciada em background (evita timeout HTTP)",
  "job_id": "abc123de",
  "note": "Acompanhe o progresso nos logs do servidor. A sincronização pode levar 10-30 minutos.",
  "params": {
    "force": false,
    "phases_only": true
  }
}
```

**Acompanhamento**: Veja os logs no Railway:
```bash
railway logs | grep "SYNC_JOB_abc123de"
```

### Modo Síncrono (NÃO RECOMENDADO - causará timeout):
```json
{
  "status": "success",
  "message": "Sincronização completa concluída com sucesso",
  "stats": {
    "projetos_antes": 102,
    "projetos_depois": 105,
    "projetos_novos": 3,
    "fases_antes": 100,
    "fases_depois": 840,
    "fases_novas": 740,
    "media_fases_por_projeto": 8.0
  }
}
```
⚠️ **Mas você não receberá esta resposta** porque ocorrerá timeout antes!

## 🐛 Troubleshooting

### Problema: Apenas 100 fases no banco

**Causa**: A sincronização normal só busca projetos modificados recentemente. Fases antigas não são sincronizadas.

**Solução**: Execute sincronização completa de fases:
```bash
python sync_complete.py --phases-only
```
Ou via API:
```bash
curl -X POST https://seu-app.railway.app/api/sync-complete \
  -H "Content-Type: application/json" \
  -d '{"phases_only": true}'
```

### Problema: Limite de registros no Railway

**Resposta**: O PostgreSQL no Railway (plano gratuito) oferece **1GB de espaço**, que suporta:
- ~500.000 registros de projetos
- ~4.000.000 de registros de fases
- Mais do que suficiente para qualquer uso normal

Não há limite artificial de número de registros.

### Problema: Sincronização demora muito

**Solução**: A sincronização completa pode demorar 10-30 minutos dependendo do número de projetos. Isso é normal porque:
- Cada projeto faz múltiplas chamadas à API do Zoho
- Há delays intencionais para não sobrecarregar a API
- Recomenda-se executar em horários de baixo uso (02:00 AM)

## 📝 Logs

Para monitorar a sincronização:

```bash
# No Railway, veja os logs em tempo real
railway logs

# Ou filtre por sincronização
railway logs | grep SYNC
```

## ⚙️ Configurações Avançadas

### Alterar horário da sincronização

Edite `.github/workflows/daily-sync.yml`:

```yaml
on:
  schedule:
    # Altere o horário aqui (formato: minuto hora * * *)
    # Exemplo: '0 6 * * *' = 06:00 AM UTC
    - cron: '0 2 * * *'
```

### Executar sincronização mais frequente

Você pode criar múltiplos agendamentos:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'   # 02:00 AM
    - cron: '0 14 * * *'  # 14:00 PM
```

## 🔒 Segurança

- O endpoint `/api/sync-complete` está público mas pode ser protegido com autenticação
- Considere adicionar um token de segurança para chamadas externas
- GitHub Actions secrets são criptografados e seguros

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs do Railway
2. Teste manualmente via curl
3. Verifique as estatísticas retornadas pela API
