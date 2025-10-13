# Ajuste de Datas para Tarefas Específicas da Implantação

## 📅 Visão Geral

Esta funcionalidade atualiza automaticamente a **data de início** de tarefas específicas para a mesma data informada no modal "Agendar Implantação".

## 🎯 Objetivo

Quando o usuário agenda uma implantação e define uma data de início, certas tarefas críticas devem ter suas datas de início automaticamente ajustadas para essa mesma data, garantindo que o cronograma esteja sincronizado.

## 📋 Tarefas Configuradas para Ajuste

As seguintes tarefas terão suas datas ajustadas (configuradas em `config.py`):

### Para Projetos com RIS
- **"Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"**

### Para Projetos com PACS
- **"Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)"**

### Para Projetos Somente PACS (Fallback)
- **"Checar o DEIP e os Docs de Infra"**
  - Esta tarefa é usada quando o projeto é somente PACS e não possui as tarefas de reunião acima

## 🔧 Configuração

### Arquivo: `config.py`

```python
# --- TAREFAS PARA AJUSTE DE DATA NA IMPLANTAÇÃO ---
# Tarefas que devem ter sua data de início ajustada para a data de início da implantação
# Importante: A identificação ignora prefixos (ex: "1. ", "[RIS] ", etc.)
TAREFAS_AJUSTE_DATA_IMPLANTACAO = [
    "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)",
    "Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)",
    "Checar o DEIP e os Docs de Infra"  # Fallback para projetos somente PACS
]
```

## 🔍 Como Funciona

### 1. Identificação Inteligente de Tarefas

A função `_verificar_tarefa_ajuste_data()` compara os títulos das tarefas com a lista configurada:

```python
def _verificar_tarefa_ajuste_data(self, titulo: str) -> bool:
    """
    Verifica se uma tarefa precisa ter sua data de início ajustada.
    Compara o título (sem prefixos) com a lista de tarefas configuradas.
    """
    titulo_limpo = self._remover_prefixos_tarefa(titulo).lower()
    
    for tarefa_config in TAREFAS_AJUSTE_DATA_IMPLANTACAO:
        tarefa_config_limpa = tarefa_config.lower().strip()
        
        # Comparação exata
        if titulo_limpo == tarefa_config_limpa:
            return True
        
        # Comparação parcial
        if tarefa_config_limpa in titulo_limpo or titulo_limpo in tarefa_config_limpa:
            return True
    
    return False
```

### 2. Remoção de Prefixos

A função `_remover_prefixos_tarefa()` remove prefixos comuns antes da comparação:

**Exemplos de prefixos removidos:**
- Numeração: `"1. "`, `"2.1 "`, `"3.2.1 "`
- Tags entre colchetes: `"[RIS] "`, `"[PACS] "`
- Tags entre parênteses: `"(RIS) "`, `"(PACS) "`

**Exemplo:**
```
Título original:    "1.2 [RIS] Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
Título limpo:       "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)"
```

Isso garante que a tarefa seja identificada corretamente, independentemente dos prefixos adicionados pelo Zoho Projects.

### 3. Atualização da Data

Quando uma tarefa é identificada:
1. A função `atualizar_data_inicio_tarefa()` é chamada
2. Um request PATCH é enviado para a API do Zoho:
   ```
   PATCH /api/v3/portal/{PORTAL_ID}/projects/{PROJECT_ID}/tasks/{TASK_ID}
   Body: {"start_date": "YYYY-MM-DD"}
   ```
3. A estatística `datas_especificas_atualizadas` é incrementada

## 📊 Estatísticas

A funcionalidade rastreia as seguintes métricas:

```python
stats = {
    "datas_atualizadas": 0,              # Sistema antigo (TAREFAS_DATA_INICIO)
    "datas_especificas_atualizadas": 0,  # Nova funcionalidade ✨
    # ... outras estatísticas
}
```

### Exemplo de Saída no Log

```
[INFO] 📊 ESTATÍSTICAS GERAIS:
[INFO]   - Total de tarefas processadas: 344
[INFO]   - Usuários adicionados ao projeto: 2
[INFO]   - Datas de início atualizadas (sistema antigo): 0
[INFO]   - Datas ajustadas (tarefas específicas): 2 📅
[INFO]   - Tarefas RIS atribuídas: 10
[INFO]   - Tarefas PACS atribuídas: 8
[INFO]   - Erros encontrados: 0
```

## 🔄 Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────┐
│  1. Usuário preenche modal "Agendar Implantação"           │
│     - Data de início: 15/10/2025                            │
│     - Implantador RIS: Pablo                                │
│     - Implantador PACS: Aneidia                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Sistema processa todas as tarefas do projeto            │
│     Total: 344 tarefas                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Para cada tarefa, remove prefixos do título             │
│     Antes: "1.2 [RIS] Realizar reunião com cliente..."     │
│     Depois: "Realizar reunião com cliente..."               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Verifica se tarefa está na lista configurada            │
│     TAREFAS_AJUSTE_DATA_IMPLANTACAO                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
           ▼                     ▼
    ┌──────────┐         ┌──────────────┐
    │   SIM    │         │     NÃO      │
    │  Ajustar │         │  Continuar   │
    │   Data   │         │              │
    └──────────┘         └──────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Atualiza data de início via API Zoho                    │
│     PATCH .../tasks/{TASK_ID}                               │
│     Body: {"start_date": "2025-10-15"}                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Incrementa estatística e continua processamento         │
│     datas_especificas_atualizadas += 1                      │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Exemplo de Uso

```python
from implantacao_tarefas import processar_implantacao_completa

stats = processar_implantacao_completa(
    project_id="2376502000005995871",
    data_inicio_implantacao="2025-10-15",
    implantador_ris="Pablo Pyerri Ferreira da Costa",
    implantador_pacs="Aneidia Sa",
    tem_ris=True,
    tem_pacs=True
)

# Resultado esperado:
# stats['datas_especificas_atualizadas'] = 2
# (1 tarefa RIS + 1 tarefa PACS)
```

## ✅ Diferenças entre Sistemas

| Aspecto | Sistema Antigo (`TAREFAS_DATA_INICIO`) | Nova Funcionalidade |
|---------|---------------------------------------|---------------------|
| **Configuração** | `implantacao_config.py` | `config.py` |
| **Identificação** | Busca por substring no título | Remove prefixos antes de comparar |
| **Estatística** | `datas_atualizadas` | `datas_especificas_atualizadas` |
| **Precisão** | Pode ter falsos positivos | Mais precisa (ignora prefixos) |
| **Propósito** | Genérico | Tarefas específicas da implantação |

## 🛠️ Manutenção

### Adicionar Nova Tarefa para Ajuste de Data

1. Abra `config.py`
2. Adicione o título exato da tarefa em `TAREFAS_AJUSTE_DATA_IMPLANTACAO`:

```python
TAREFAS_AJUSTE_DATA_IMPLANTACAO = [
    "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS)",
    "Realizar reunião com cliente para entendimento do fluxo do cliente (PACS)",
    "Checar o DEIP e os Docs de Infra",
    "Nova tarefa aqui"  # ← Adicionar aqui
]
```

### Verificar Tarefas Processadas

Ative o log detalhado em `implantacao_config.py`:

```python
LOG_DETALHADO = True
```

Saída esperada:
```
[DEBUG] ✓ Tarefa identificada para ajuste de data (exata): 'Realizar reunião com cliente...'
[INFO] 📅 Ajustando data para tarefa específica: Realizar reunião com cliente...
[SUCCESS] ✓ Data ajustada com sucesso!
```

## 📝 Notas Importantes

1. **Prefixos são Ignorados**: A comparação é feita após remover prefixos numéricos e tags
2. **Comparação Case-Insensitive**: Maiúsculas/minúsculas não importam
3. **Comparação Parcial Suportada**: Títulos parciais também são reconhecidos
4. **Compatível com Sistema Antigo**: As duas funcionalidades coexistem sem conflitos
5. **Estatísticas Separadas**: Cada sistema tem sua própria métrica para rastreamento

## 🔗 Arquivos Relacionados

- `config.py` - Configuração das tarefas
- `implantacao_tarefas.py` - Implementação da lógica
- `routes/api.py` - Endpoint `/iniciar_implantacao`
- `implantacao_config.py` - Configurações gerais do sistema de implantação

---

**Última atualização:** 12/10/2025
**Versão:** 1.0
