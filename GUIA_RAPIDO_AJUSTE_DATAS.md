# 🚀 GUIA RÁPIDO - Ajuste de Datas para Tarefas Específicas

## ⚡ Visão Geral em 30 Segundos

**O que faz?** Ajusta automaticamente a data de início de tarefas específicas quando você agenda uma implantação.

**Tarefas afetadas:**
- ✅ Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)
- ✅ Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)
- ✅ Checar o DEIP e os Docs de Infra (fallback para projetos somente PACS)

**Como usar?** Nada! É automático. 🎯

---

## 🎯 Como Funciona (Resumido)

1. Usuário preenche modal "Agendar Implantação" com data: **15/10/2025**
2. Sistema processa todas as tarefas do projeto
3. Identifica as 3 tarefas configuradas (ignora prefixos numéricos e tags)
4. Atualiza a data de início delas para **15/10/2025**
5. Mostra estatística: `Datas ajustadas (tarefas específicas): 2 📅`

---

## 📊 Onde Ver os Resultados?

### No Terminal/Console

```
[INFO] 📊 ESTATÍSTICAS GERAIS:
[INFO]   - Datas ajustadas (tarefas específicas): 2 📅  ← AQUI
```

### No Zoho Projects

Verifique a data de início das tarefas:
- "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
- "Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)"

Deve estar igual à data informada no modal.

---

## 🛠️ Configuração (Onde Mexer)

### Adicionar Nova Tarefa

**Arquivo:** `config.py` (linha ~120)

```python
TAREFAS_AJUSTE_DATA_IMPLANTACAO = [
    "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)",
    "Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)",
    "Checar o DEIP e os Docs de Infra",
    "Sua nova tarefa aqui"  # ← Adicione aqui
]
```

**❗ IMPORTANTE:** Use o título EXATO da tarefa (sem prefixos numéricos ou tags)

---

## 🧪 Como Testar

### Teste Automatizado (Recomendado)

```powershell
python test_ajuste_datas_tarefas.py
```

✅ Todos os 25 testes devem passar

### Teste Manual

1. Crie/use um projeto de teste no Zoho
2. Verifique se ele tem as tarefas configuradas
3. Use o modal "Agendar Implantação"
4. Escolha uma data de início (ex: 20/10/2025)
5. Confirme
6. Verifique no Zoho se as datas foram atualizadas

---

## 🔍 Troubleshooting

### ❌ Tarefa não foi identificada

**Possíveis causas:**
1. Título da tarefa no Zoho ≠ configuração em `config.py`
2. Tarefa tem caracteres especiais não contemplados

**Solução:**
```python
# Ative log detalhado em implantacao_config.py
LOG_DETALHADO = True

# Execute novamente e veja os logs:
[DEBUG] ✓ Tarefa identificada...  ← Deve aparecer
```

### ❌ Data não foi atualizada

**Possíveis causas:**
1. Erro na API do Zoho (403, 500)
2. Token de acesso inválido

**Solução:**
```python
# Verifique os logs de erro:
[ERROR] Erro definitivo ao atualizar data da tarefa...
```

### ✅ Como saber se está funcionando?

Procure por esta linha nos logs:
```
[INFO] 📅 Ajustando data para tarefa específica: ...
[SUCCESS] ✓ Data ajustada com sucesso!
```

---

## 📖 Documentação Completa

| Arquivo | Descrição |
|---------|-----------|
| `AJUSTE_DATAS_TAREFAS_ESPECIFICAS.md` | Documentação técnica completa |
| `RESUMO_AJUSTE_DATAS.md` | Resumo da implementação |
| `GUIA_RAPIDO_AJUSTE_DATAS.md` | Este guia rápido |
| `test_ajuste_datas_tarefas.py` | Testes automatizados |

---

## 🎓 Exemplos de Títulos que SÃO Identificados

Todas estas variações SÃO identificadas corretamente:

```
✅ "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
✅ "1. Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
✅ "2.1 Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
✅ "[RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
✅ "1.2 [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
✅ "REALIZAR REUNIÃO COM CLIENTE PARA ENTENDIMENTO DO FLUXO DO CLIENTE (RIS)"
```

**Por quê?** Sistema remove prefixos automaticamente antes de comparar! 🎯

---

## 🎓 Exemplos de Títulos que NÃO SÃO Identificados

```
❌ "Realizar reunião de kickoff"
❌ "Agendar reunião com cliente"
❌ "Checar apenas o DEIP"
```

**Por quê?** Não estão na lista `TAREFAS_AJUSTE_DATA_IMPLANTACAO`

---

## 🔗 Links Rápidos

- **Configuração**: `config.py` → `TAREFAS_AJUSTE_DATA_IMPLANTACAO`
- **Implementação**: `implantacao_tarefas.py` → `_verificar_tarefa_ajuste_data()`
- **Testes**: Execute `python test_ajuste_datas_tarefas.py`

---

## 💡 Dica Profissional

**Quer adicionar uma nova tarefa mas não sabe o título exato?**

1. Abra o projeto no Zoho Projects
2. Copie o título EXATO da tarefa (Ctrl+C)
3. Cole em `config.py` dentro de `TAREFAS_AJUSTE_DATA_IMPLANTACAO`
4. Salve
5. Pronto! ✅

O sistema vai ignorar prefixos automaticamente.

---

**Última atualização:** 12/10/2025  
**Versão:** 1.0  
**Status:** ✅ Produção
