# 📖 Guia: Popular Banco Neon Localmente

## 🎯 Objetivo

Este guia mostra como fazer a **primeira sincronização** do Zoho para o banco de dados Neon **a partir do seu computador local**, evitando timeout no Render.

---

## 📋 Pré-requisitos

### 1. Python Instalado
```bash
python --version  # Deve ser 3.8 ou superior
```

### 2. Dependências Instaladas
```bash
pip install -r requirements.txt
```

Se não tiver o arquivo requirements.txt ou estiver faltando alguma lib:
```bash
pip install python-dotenv psycopg2-binary sqlalchemy requests
```

### 3. Informações Necessárias

Você precisará ter em mãos:
- ✅ String de conexão do banco Neon (DATABASE_URL)
- ✅ Credenciais da API do Zoho (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)

---

## 🔧 Passo 1: Configurar Arquivo .env

### Criar o arquivo .env

Na raiz do projeto, crie um arquivo chamado `.env` (sem extensão, apenas .env):

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Linux/Mac:**
```bash
cp .env.example .env
nano .env  # ou vim, code, etc.
```

### Preencher as variáveis

Edite o arquivo `.env` com seus valores reais:

```bash
# Banco Neon (copie do painel do Neon)
DATABASE_URL=postgresql://usuario:senha@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# Zoho API (mesmos valores que estão no Render)
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZOHO_REFRESH_TOKEN=1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Flask (pode usar qualquer valor por enquanto)
SECRET_KEY=qualquer-chave-aleatoria-aqui

# Token de sincronização (mesmo do Render)
SYNC_TOKEN=seu-token-aqui
```

### ⚠️ IMPORTANTE: Verificar a String de Conexão do Neon

A string do Neon deve ter este formato:
```
postgresql://usuario:senha@host:porta/database?sslmode=require
```

**Onde pegar:**
1. Acesse: Neon Dashboard → Seu Projeto → Connection Details
2. Copie a string de conexão completa (modo "Pooled connection" ou "Direct connection")
3. Cole no `.env` substituindo o exemplo

---

## 🚀 Passo 2: Executar a Sincronização

### Rodar o script

No terminal, na raiz do projeto:

```bash
python popular_banco.py
```

### O que vai acontecer:

```
================================================================================
  POPULANDO BANCO NEON - PRIMEIRA SINCRONIZAÇÃO
  Início: 2025-12-09 14:30:00
================================================================================

✅ Arquivo .env carregado
✅ Módulo database importado
📊 Estado atual do banco:
   - Projetos: 0
   - Fases: 0
✅ Módulos de sincronização importados

================================================================================
📥 ETAPA 1/2: SINCRONIZANDO PROJETOS DO ZOHO
================================================================================
--- Iniciando sincronização completa do Zoho ---
Buscando projetos modificados desde: 2000-01-01T00:00:00Z
Buscando página 1 de projetos...
  -> Sincronizado projeto: Projeto A (ID: XXX)
  -> Sincronizado projeto: Projeto B (ID: XXX)
  ...
--- Sincronização concluída. 107 projetos foram atualizados/inseridos. ---

✅ Projetos sincronizados com sucesso!
📊 Projetos inseridos: 107
   Total no banco: 107

================================================================================
📊 ETAPA 2/2: SINCRONIZANDO FASES DE TODOS OS PROJETOS
================================================================================
⏱️  Esta etapa pode levar 10-15 minutos...
⚠️  Zoho API Rate Limit: 100 req/2min - usando delay de 2s entre projetos

=== SINCRONIZANDO FASES DE TODOS OS PROJETOS ===
[SYNC] Sincronizando fases para 107 projetos...
[1/107] Sincronizando fases do projeto: Projeto A
  ✓ 5 fases sincronizadas
[2/107] Sincronizando fases do projeto: Projeto B
  ✓ 3 fases sincronizadas
...

✅ Fases sincronizadas com sucesso!

================================================================================
✅ SINCRONIZAÇÃO COMPLETA CONCLUÍDA!
================================================================================

📊 Estatísticas finais:
   - Projetos no banco: 107 (novos: 107)
   - Fases no banco: 450 (novas: 450)
   - Média de fases por projeto: 4.2

🎉 Banco Neon populado com sucesso!
⏱️  Fim: 2025-12-09 14:45:00
================================================================================

✅ Script finalizado com sucesso!

Próximos passos:
1. Verifique os dados no banco Neon
2. Faça deploy no Render
3. Sincronizações futuras serão via GitHub Actions
```

### ⏱️ Tempo estimado
- **ETAPA 1** (Projetos): ~2-5 minutos
- **ETAPA 2** (Fases): ~10-15 minutos (depende do número de projetos)
- **Total**: ~15-20 minutos

---

## ✅ Passo 3: Verificar no Neon

1. Acesse: Neon Dashboard → Seu Projeto → SQL Editor
2. Execute as queries:

```sql
-- Contar projetos
SELECT COUNT(*) as total_projetos FROM projects;

-- Contar fases
SELECT COUNT(*) as total_fases FROM fases;

-- Ver primeiros projetos
SELECT id, nome, status, created_at 
FROM projects 
LIMIT 10;

-- Verificar projetos com fases
SELECT 
    p.nome as projeto,
    COUNT(f.id) as num_fases
FROM projects p
LEFT JOIN fases f ON f.projeto_id = p.id
GROUP BY p.id, p.nome
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Erro: "ModuleNotFoundError: No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Erro: "could not connect to server"
- ✅ Verifique se DATABASE_URL está correto
- ✅ Teste a conexão no SQL Editor do Neon primeiro
- ✅ Certifique-se de incluir `?sslmode=require` no final da URL

### Erro: "ZOHO API error" ou "invalid token"
- ✅ Verifique ZOHO_CLIENT_ID, CLIENT_SECRET e REFRESH_TOKEN
- ✅ Certifique-se que o REFRESH_TOKEN não expirou
- ✅ Pode ser necessário gerar um novo token no Zoho API Console

### Erro: "Rate limit exceeded"
- ✅ Normal! O script tem delays para evitar isso
- ✅ Se acontecer, o script tenta novamente automaticamente
- ✅ Aguarde 2 minutos e execute novamente se necessário

### Script muito lento
- ✅ Normal! São 100+ projetos com delays de 2s entre cada
- ✅ Zoho tem limite de 100 requisições a cada 2 minutos
- ✅ Deixe rodando em segundo plano e aguarde

---

## 🎉 Após Sincronização Bem-Sucedida

### 1. Commitar (opcional)
```bash
git add popular_banco.py .env.example
git commit -m "feat: adiciona script para popular banco Neon localmente"
```

**⚠️ NUNCA commite o arquivo .env** (só .env.example)

### 2. Deploy no Render

Com o banco já populado, o deploy no Render será rápido:
- Não tentará sincronizar no boot (banco não está vazio)
- Aplicação inicia normalmente
- Sincronizações futuras via GitHub Actions

### 3. Configurar GitHub Actions

As sincronizações diárias automáticas continuarão via GitHub Actions:
- Configurado em `.github/workflows/daily-sync.yml`
- Roda diariamente às 06:00 UTC
- Ou execute manualmente quando precisar

---

## 📚 Arquivos Relacionados

- `popular_banco.py` - Script principal (este guia)
- `.env.example` - Template de configuração
- `sync_zoho.py` - Lógica de sincronização
- `database.py` - Definição do schema
- `DEPLOY.md` - Guia completo de deploy no Render

---

**Última atualização:** 2025-12-09
