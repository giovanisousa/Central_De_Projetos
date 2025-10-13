# 📚 EXEMPLOS PRÁTICOS - Ajuste de Datas para Tarefas Específicas

## 🎯 Cenário 1: Projeto RIS + PACS Completo

### Entrada (Modal)
```
Data de início da implantação: 15/10/2025
Implantador RIS: Pablo Pyerri Ferreira da Costa
Implantador PACS: Aneidia Sa
Tipo de projeto: RIS + PACS
```

### Tarefas no Projeto Zoho
```
1. Registrar Projeto Planilha de Andamento
2. Criar pastas no Google Drive
3. [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)  ← ✅
4. [PACS] Realizar reunião com cliente para entendimento do fluxo do cliente (PACS) ← ✅
5. Checar o DEIP e os Docs de Infra
6. Solicitar definição do cronograma de homologação
...
```

### Resultado
```
[INFO] 📅 Ajustando data para tarefa específica: [RIS] Realizar reunião com cliente...
[SUCCESS] ✓ Data ajustada com sucesso!

[INFO] 📅 Ajustando data para tarefa específica: [PACS] Realizar reunião com cliente...
[SUCCESS] ✓ Data ajustada com sucesso!

📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 2 📅
```

### Verificação no Zoho
| Tarefa | Data de Início Antes | Data de Início Depois |
|--------|---------------------|----------------------|
| [RIS] Realizar reunião com cliente... | 01/11/2025 | **15/10/2025** ✅ |
| [PACS] Realizar reunião com cliente... | 01/11/2025 | **15/10/2025** ✅ |

---

## 🎯 Cenário 2: Projeto Somente PACS

### Entrada (Modal)
```
Data de início da implantação: 20/10/2025
Implantador RIS: (nenhum)
Implantador PACS: Aneidia Sa
Tipo de projeto: Somente PACS
```

### Tarefas no Projeto Zoho
```
1. Registrar Projeto Planilha de Andamento
2. Criar pastas no Google Drive
3. Realizar reunião com cliente para entendimento do fluxo do cliente (PACS) ← ✅
4. Checar o DEIP e os Docs de Infra  ← ✅ (Fallback)
5. Solicitar definição do cronograma de homologação
...
```

### Resultado
```
[INFO] 📅 Ajustando data para tarefa específica: Realizar reunião com cliente (PACS)...
[SUCCESS] ✓ Data ajustada com sucesso!

[INFO] 📅 Ajustando data para tarefa específica: Checar o DEIP e os Docs de Infra...
[SUCCESS] ✓ Data ajustada com sucesso!

📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 2 📅
```

### Verificação no Zoho
| Tarefa | Data de Início Antes | Data de Início Depois |
|--------|---------------------|----------------------|
| Realizar reunião com cliente (PACS) | 05/11/2025 | **20/10/2025** ✅ |
| Checar o DEIP e os Docs de Infra | 08/11/2025 | **20/10/2025** ✅ |

---

## 🎯 Cenário 3: Projeto Somente RIS

### Entrada (Modal)
```
Data de início da implantação: 18/10/2025
Implantador RIS: Pablo Pyerri Ferreira da Costa
Implantador PACS: (nenhum)
Tipo de projeto: Somente RIS
```

### Tarefas no Projeto Zoho
```
1. Registrar Projeto Planilha de Andamento
2. Criar pastas no Google Drive
3. 1.2 Realizar reunião com cliente para entendimento do fluxo do cliente (RIS) ← ✅
4. Checar o DEIP e os Docs de Infra
5. Solicitar definição do cronograma de homologação
...
```

### Resultado
```
[INFO] 📅 Ajustando data para tarefa específica: 1.2 Realizar reunião com cliente...
[SUCCESS] ✓ Data ajustada com sucesso!

📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 1 📅
```

### Verificação no Zoho
| Tarefa | Data de Início Antes | Data de Início Depois |
|--------|---------------------|----------------------|
| 1.2 Realizar reunião com cliente (RIS) | 10/11/2025 | **18/10/2025** ✅ |

---

## 🎯 Cenário 4: Tarefas com Prefixos Diferentes

### Entrada (Modal)
```
Data de início da implantação: 22/10/2025
Tipo de projeto: RIS + PACS
```

### Tarefas no Projeto Zoho (Variações de Prefixos)
```
1.   Registrar Projeto Planilha de Andamento
2.1  Criar pastas no Google Drive
3.2.1 [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS) ← ✅
4.5   (PACS) Realizar reunião com cliente para entendimento do fluxo do cliente (PACS) ← ✅
5.    Checar o DEIP e os Docs de Infra
...
```

### Processamento Interno
```
Tarefa: "3.2.1 [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
  ↓ Remove "3.2.1"
  ↓ Remove "[RIS]"
  ↓ Resultado: "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
  ↓ Compara com config
  ✅ MATCH! → Ajustar data

Tarefa: "4.5 (PACS) Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)"
  ↓ Remove "4.5"
  ↓ Remove "(PACS)"
  ↓ Resultado: "Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)"
  ↓ Compara com config
  ✅ MATCH! → Ajustar data
```

### Resultado
```
[DEBUG] ✓ Tarefa identificada para ajuste de data (exata): '3.2.1 [RIS] Realizar reunião...'
[INFO] 📅 Ajustando data para tarefa específica: 3.2.1 [RIS] Realizar reunião...
[SUCCESS] ✓ Data ajustada com sucesso!

[DEBUG] ✓ Tarefa identificada para ajuste de data (exata): '4.5 (PACS) Realizar reunião...'
[INFO] 📅 Ajustando data para tarefa específica: 4.5 (PACS) Realizar reunião...
[SUCCESS] ✓ Data ajustada com sucesso!

📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 2 📅
```

---

## 🎯 Cenário 5: Tarefas Similares (Não Deve Ajustar)

### Entrada (Modal)
```
Data de início da implantação: 25/10/2025
```

### Tarefas no Projeto Zoho
```
1. Realizar reunião de kickoff
2. Realizar reunião com cliente para apresentação
3. Agendar reunião com equipe interna
4. Checar apenas o DEIP
5. Checar documentação técnica
...
```

### Processamento Interno
```
Tarefa: "Realizar reunião de kickoff"
  ↓ Compara com config
  ❌ NÃO MATCH → Ignorar

Tarefa: "Realizar reunião com cliente para apresentação"
  ↓ Compara com config
  ❌ NÃO MATCH → Ignorar

Tarefa: "Checar apenas o DEIP"
  ↓ Compara com config ("Checar o DEIP e os Docs de Infra")
  ❌ NÃO MATCH → Ignorar
```

### Resultado
```
📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 0 📅
```

**✅ Comportamento Correto:** Apenas as tarefas EXATAS são ajustadas

---

## 🎯 Cenário 6: Tarefas com Case Diferente

### Entrada (Modal)
```
Data de início da implantação: 28/10/2025
```

### Tarefas no Projeto Zoho (Diferentes Cases)
```
1. REALIZAR REUNIÃO COM CLIENTE PARA ENTENDIMENTO DO FLUXO DO CLIENTE (RIS) ← ✅
2. realizar reunião com cliente para entendimento do fluxo do cliente (pacs) ← ✅
3. Realizar Reunião Com Cliente Para Entendimento Do Fluxo Do Cliente (RIS) ← ✅
...
```

### Processamento Interno
```
Todas convertidas para lowercase antes da comparação:
✅ "realizar reunião com cliente para entendimento do fluxo do cliente (ris)"
✅ "realizar reunião com cliente para entendimento do fluxo do cliente (pacs)"
✅ "realizar reunião com cliente para entendimento do fluxo do cliente (ris)"
```

### Resultado
```
[INFO] 📅 Ajustando data para tarefa específica: REALIZAR REUNIÃO COM CLIENTE...
[SUCCESS] ✓ Data ajustada com sucesso!

[INFO] 📅 Ajustando data para tarefa específica: realizar reunião com cliente...
[SUCCESS] ✓ Data ajustada com sucesso!

[INFO] 📅 Ajustando data para tarefa específica: Realizar Reunião Com Cliente...
[SUCCESS] ✓ Data ajustada com sucesso!

📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 3 📅
```

**✅ Case-Insensitive:** Maiúsculas/minúsculas não importam

---

## 🎯 Cenário 7: Erro na API do Zoho (403 Forbidden)

### Entrada (Modal)
```
Data de início da implantação: 30/10/2025
```

### Situação
Usuário não tem permissão para editar tarefas no projeto

### Resultado
```
[INFO] 📅 Ajustando data para tarefa específica: Realizar reunião com cliente...
[WARN] Tentativa 1 falhou para atualizar data da tarefa 2376502000012345678: 403 Client Error...
[WARN] Tentativa 2 falhou para atualizar data da tarefa 2376502000012345678: 403 Client Error...
[WARN] Tentativa 3 falhou para atualizar data da tarefa 2376502000012345678: 403 Client Error...
[ERROR] Erro definitivo ao atualizar data da tarefa 2376502000012345678: 403 Client Error: Forbidden

📊 ESTATÍSTICAS:
  - Datas ajustadas (tarefas específicas): 0 📅
  - Erros encontrados: 1
```

**🔧 Solução:** Verificar permissões do usuário no projeto Zoho

---

## 🎯 Cenário 8: Projeto com 344 Tarefas

### Entrada (Modal)
```
Data de início da implantação: 05/11/2025
Tipo de projeto: RIS + PACS
```

### Situação
Projeto grande com muitas tarefas

### Processamento
```
[INFO] Total de tarefas carregadas: 344
[INFO] Processando lote 1/7 (50 tarefas)
  → Processa tarefas 1-50
[INFO] Processando lote 2/7 (50 tarefas)
  → Processa tarefas 51-100
  → Tarefa 87: "2.1 [RIS] Realizar reunião com cliente..." ← ✅ IDENTIFICADA
[INFO] 📅 Ajustando data para tarefa específica: 2.1 [RIS] Realizar reunião...
[SUCCESS] ✓ Data ajustada com sucesso!
...
[INFO] Processando lote 5/7 (50 tarefas)
  → Processa tarefas 201-250
  → Tarefa 234: "[PACS] Realizar reunião com cliente..." ← ✅ IDENTIFICADA
[INFO] 📅 Ajustando data para tarefa específica: [PACS] Realizar reunião...
[SUCCESS] ✓ Data ajustada com sucesso!
...
[INFO] Processando lote 7/7 (44 tarefas)
  → Processa tarefas 301-344
```

### Resultado
```
📊 ESTATÍSTICAS GERAIS:
  - Total de tarefas processadas: 344
  - Datas ajustadas (tarefas específicas): 2 📅
  - Tempo de processamento: ~3 minutos
```

**✅ Otimizado:** Sistema processa lotes de 50 tarefas com delays para não sobrecarregar API

---

## 📊 Tabela Comparativa de Cenários

| Cenário | Tarefas Identificadas | Datas Ajustadas | Tempo Aprox. |
|---------|----------------------|----------------|--------------|
| RIS + PACS Completo | 2 | 2 | ~10s |
| Somente PACS | 2 (com fallback) | 2 | ~10s |
| Somente RIS | 1 | 1 | ~5s |
| Prefixos Diferentes | 2 | 2 | ~10s |
| Tarefas Similares | 0 | 0 | ~0s |
| Case Diferente | 3 | 3 | ~15s |
| Erro API (403) | 1 | 0 | ~15s (3 tentativas) |
| Projeto Grande (344) | 2 | 2 | ~3min |

---

## 💡 Dicas de Uso

### ✅ Boas Práticas
1. Sempre verifique os logs para confirmar quantas tarefas foram ajustadas
2. Use `LOG_DETALHADO = True` durante testes
3. Execute `test_ajuste_datas_tarefas.py` antes de mudanças
4. Mantenha `TAREFAS_AJUSTE_DATA_IMPLANTACAO` atualizado

### ❌ Evitar
1. Não adicione títulos com prefixos em `config.py`
2. Não use títulos parciais demais (ex: "Realizar reunião")
3. Não desative validações de string vazia

### 🔍 Troubleshooting Rápido
- **0 datas ajustadas:** Verifique se as tarefas existem no projeto
- **Erros 403:** Verificar permissões do usuário
- **Erros 500:** Problema na API do Zoho (esperar/tentar novamente)

---

**Última atualização:** 12/10/2025  
**Versão:** 1.0
