# 🚀 Guia de Deploy - Central de Projetos

## Deploy no Render.com

### 1. Preparação

**Variáveis de Ambiente Necessárias:**
```
DATABASE_URL=postgresql://...  # String de conexão Neon/PostgreSQL
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REFRESH_TOKEN=...
SYNC_TOKEN=...                 # Token para autenticar sincronização via API
SECRET_KEY=...                 # Flask secret key
```

### 2. Processo de Deploy

**O que acontece durante o deploy:**
1. ✅ Render instala dependências (`requirements.txt`)
2. ✅ Aplicação Flask inicia
3. ✅ Banco de dados é verificado/inicializado (schema criado automaticamente)
4. ⚠️  **SINCRONIZAÇÃO NÃO RODA AUTOMATICAMENTE** (para evitar timeout)

**Por que não sincronizar no boot?**
- A sincronização completa pode levar 5-10 minutos
- Render tem timeout de ~10 minutos para build/deploy
- Se o banco estiver vazio, o deploy pode falhar por timeout

### 3. Primeira Sincronização (Após Deploy)

**Opção 1: Via API (Recomendado para automação)**

```bash
curl -X POST \
  -H "Authorization: Bearer SEU_SYNC_TOKEN" \
  -H "Content-Type: application/json" \
  https://sua-app.onrender.com/api/trigger-sync
```

**Resposta esperada:**
```json
{
  "sucesso": true,
  "mensagem": "Sincronização iniciada em background. Verifique os logs do servidor para acompanhar o progresso.",
  "output": "Sincronização em execução. Logs disponíveis no servidor."
}
```

**Opção 2: Via GitHub Actions**

O workflow `.github/workflows/daily-sync.yml` já está configurado para chamar o endpoint automaticamente.

Execute manualmente:
1. Acesse: `GitHub → Actions → Daily Sync`
2. Clique em `Run workflow`
3. Selecione branch `main`
4. Clique em `Run workflow`

**Opção 3: Via Shell (acesso SSH/console)**

Se você tiver acesso ao console do Render:
```bash
python sync_complete.py
```

### 4. Acompanhando a Sincronização

**Nos Logs do Render:**
1. Acesse: Render Dashboard → Seu Service → Logs
2. Procure por mensagens como:
   ```
   [SYNC] Sincronização de fases iniciada...
   [1/107] Sincronizando fases do projeto: Nome do Projeto
   ✓ X fases sincronizadas
   ✅ Sincronização concluída com sucesso!
   ```

**Tempo estimado:**
- ~107 projetos × 2-3 segundos cada = **5-10 minutos**
- A sincronização roda em background (não bloqueia a aplicação)

### 5. Sincronizações Subsequentes

**Sincronização Diária Automática:**
- GitHub Actions executa diariamente às 6:00 AM UTC
- Configurado em `.github/workflows/daily-sync.yml`

**Sincronização Manual:**
- Use o endpoint `/api/trigger-sync` sempre que precisar
- Ou execute manualmente via GitHub Actions

### 6. Troubleshooting

**Deploy falha por timeout:**
- ✅ **Solução implementada:** Sincronização não roda no boot
- Se ainda ocorrer, verifique se há outro processo pesado rodando

**Sincronização não completa:**
- Verifique logs do Render para erros
- Confirme que `ZOHO_REFRESH_TOKEN` está válido
- Verifique rate limits da API do Zoho

**Banco de dados vazio após deploy:**
- ✅ **Normal!** Execute sincronização manual após deploy
- Logs mostrarão: `⚠️  Banco de dados vazio! Execute sincronização...`

**Erro 500 no endpoint /api/trigger-sync:**
- Verifique se `SYNC_TOKEN` está configurado no Render
- Confirme que está enviando `Authorization: Bearer SEU_TOKEN`
- Veja logs do Render para traceback detalhado

### 7. Checklist Pós-Deploy

- [ ] Deploy concluído com sucesso
- [ ] Aplicação acessível via URL do Render
- [ ] Logs mostram: `[SYNC] Projetos no banco: 0` ou `[SYNC] Banco de dados vazio`
- [ ] Executar sincronização inicial via API ou GitHub Actions
- [ ] Aguardar 5-10 minutos para conclusão
- [ ] Verificar logs: `✅ Sincronização concluída com sucesso!`
- [ ] Acessar aplicação e verificar que projetos aparecem
- [ ] Configurar GitHub Actions (se ainda não configurado)

---

## Migração de Railway para Render

**Diferenças importantes:**

| Aspecto | Railway | Render |
|---------|---------|--------|
| Build timeout | ~10 min | ~10 min |
| Logs | Real-time | Real-time |
| Variáveis de ambiente | Railway Dashboard | Render Dashboard |
| Deploy automático | Git push | Git push |

**Passos da migração:**
1. ✅ Criar banco Neon (PostgreSQL)
2. ✅ Criar serviço no Render
3. ✅ Configurar variáveis de ambiente
4. ✅ Fazer deploy inicial (sem sincronização)
5. ✅ Executar sincronização manual após deploy
6. ✅ Configurar GitHub Actions para usar nova URL

---

**Última atualização:** 2025-11-11
