# 🚀 Sistema de Processamento de Tarefas de Implantação

## 📋 Visão Geral

Esta funcionalidade automatiza o processamento de tarefas quando o botão **"Agendar Implantação"** é clicado, realizando:

1. **Atualização de datas de início** para 2 tarefas específicas
2. **Atribuição automática** de tarefas aos implantadores RIS e PACS
3. **Processamento otimizado** para lidar com 200+ tarefas (projetos RIS) ou 20+ tarefas (projetos PACS)

## 🏗️ Arquitetura

### Arquivos Principais
- `implantacao_tarefas.py` - Módulo principal de processamento
- `implantacao_config.py` - Configurações e padrões de identificação
- `routes/api.py` - Integração com endpoint `/iniciar_implantacao`
- `equipe_implantacao_classificada.json` - Base de dados dos implantadores

### Fluxo de Processamento
```
Usuário clica "Agendar Implantação"
    ↓
Calcula datas (homologação/virada)
    ↓
Atualiza campos do projeto no Zoho
    ↓
Atualiza planilha principal
    ↓
🆕 PROCESSA TAREFAS AUTOMATICAMENTE
    ↓
Sincroniza banco local
    ↓
Retorna resultado completo
```

## ⚙️ Configuração

### 1. Definir Tarefas de Data
Edite `implantacao_config.py` e configure `TAREFAS_DATA_INICIO`:

```python
TAREFAS_DATA_INICIO = [
    "Definição do cronograma de homologação",
    "Início da implantação",
    # Adicione os títulos EXATOS das tarefas que precisam ter data atualizada
]
```

### 2. Configurar Padrões de Identificação
Ajuste os padrões para identificar tarefas RIS e PACS:

```python
PADROES_TAREFAS_RIS = [
    "ris", "netris", "configuração ris", "instalação ris"
    # Adicione mais padrões conforme necessário
]

PADROES_TAREFAS_PACS = [
    "pacs", "animatipacs", "configuração pacs", "instalação pacs"
    # Adicione mais padrões conforme necessário
]
```

### 3. Ajustar Performance
Para projetos com muitas tarefas:

```python
BATCH_SIZE_TAREFAS = 50    # Tarefas por lote
DELAY_ENTRE_LOTES = 2      # Segundos entre lotes
MAX_TAREFAS_PROCESSAR = 500 # Limite de segurança
```

## 🎯 Como Funciona

### Identificação de Tarefas

#### Por Data de Início
- Busca títulos que contenham os padrões definidos em `TAREFAS_DATA_INICIO`
- Atualiza a `start_date` para a data de início da implantação

#### Por Responsável
- **RIS**: Identifica tarefas com padrões como "ris", "netris", "configuração ris"
- **PACS**: Identifica tarefas com padrões como "pacs", "animatipacs", "setup pacs"
- Atribui usando os **ZPUIDs** do arquivo `equipe_implantacao_classificada.json`

### Cenários de Uso

#### Projeto Somente PACS (~20 tarefas)
```json
{
  "project_id": "123456",
  "data_inicio_implantacao": "2025-10-15",
  "implantador_pacs": "Aneidia Sa",
  "implantador_ris": ""
}
```

#### Projeto RIS + PACS (200+ tarefas)
```json
{
  "project_id": "123456", 
  "data_inicio_implantacao": "2025-10-15",
  "implantador_ris": "Pablo Pyerri Ferreira da Costa",
  "implantador_pacs": "Aneidia Sa"
}
```

## 📊 Monitoramento

### Logs Detalhados
O sistema produz logs extensivos:

```
[DEBUG][INICIAR_IMPLANTACAO] ===== ETAPA 3: PROCESSANDO TAREFAS =====
[DEBUG][INICIAR_IMPLANTACAO] Produtos detectados - RIS: True, PACS: True
[INFO] Processando lote 1/4 (50 tarefas)
[SUCCESS] Responsável atribuído para tarefa 789123
📅 2 tarefas com datas atualizadas
✅ 156 tarefas atribuídas aos implantadores
```

### Estatísticas Retornadas
```json
{
  "total_tarefas": 200,
  "datas_atualizadas": 2,
  "ris_atribuidas": 120,
  "pacs_atribuidas": 36,
  "erros": 1
}
```

## 🔧 APIs Utilizadas

### Atualização de Data
```
PATCH /api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}
Body: {"start_date": "2025-10-15"}
```

### Atribuição de Responsável
```
POST /restapi/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/
Body: {"person_responsible": "2376502000000080073"}
```

## 🛡️ Segurança e Performance

### Rate Limiting
- **Delay entre tarefas**: 0.3s (evita sobrecarga da API)
- **Delay entre lotes**: 2s (permite recuperação da API)
- **Retry automático**: 3 tentativas por operação
- **Timeout**: 30s por requisição

### Validações
- ✅ Verificação de ZPUIDs antes da atribuição
- ✅ Limite máximo de tarefas processadas (500)
- ✅ Exclusão de tarefas de "conclusão" e "encerramento"
- ✅ Processamento por prioridade (tarefas críticas primeiro)

### Tratamento de Erros
- ❌ Erros não interrompem o processo principal
- 📝 Logs detalhados para debugging
- 📊 Contabilização de erros nas estatísticas
- 🔄 Fallback gracioso em caso de falhas

## 🧪 Testes

Execute os testes antes de usar em produção:

```bash
python test_implantacao_tarefas.py
```

### O que é testado:
- ✅ Carregamento de configurações
- ✅ Acesso ao arquivo de equipe
- ✅ Identificação de tipos de tarefa
- ✅ Busca de ZPUIDs por nome

## 📈 Benefícios

### Para Projetos PACS (~20 tarefas)
- ⚡ Processamento em **~15 segundos**
- 🎯 **100% automático** - sem intervenção manual
- 📋 **2 datas** + **~18 atribuições** automáticas

### Para Projetos RIS (200+ tarefas)
- ⚡ Processamento em **~3-5 minutos**
- 🎯 **200+ atribuições** automáticas
- 📋 **2 datas** atualizadas
- 💪 **Performance otimizada** com processamento em lotes

### Impacto Operacional
- 🕒 **Economia de tempo**: 30-60 minutos de trabalho manual → automático
- ✅ **Redução de erros**: eliminação de atribuições manuais incorretas
- 📊 **Rastreabilidade**: logs completos de todas as operações
- 🔄 **Consistência**: mesmos critérios aplicados sempre

## 🚨 Troubleshooting

### Problemas Comuns

#### "Nenhuma tarefa processada"
- Verifique se os padrões em `implantacao_config.py` correspondem aos títulos reais
- Confirme se os implantadores foram selecionados corretamente

#### "ZPUIDs não encontrados"
- Verifique se os nomes no arquivo `equipe_implantacao_classificada.json` estão corretos
- Confirme se os nomes selecionados existem no arquivo

#### "Muitos erros de API"
- Verifique se o token do Zoho está válido
- Confirme se há rate limiting excessivo
- Considere aumentar `DELAY_ENTRE_TAREFAS`

### Modo Debug
Para troubleshooting, ative logs detalhados em `implantacao_config.py`:

```python
LOG_DETALHADO = True
LOG_PROGRESSO_A_CADA = 1  # Log de cada tarefa
```

## 🎉 Conclusão

Esta implementação transforma um processo manual demorado em uma operação **100% automatizada**, oferecendo:

- **Escalabilidade** para projetos de qualquer tamanho
- **Confiabilidade** com retry automático e tratamento de erros
- **Flexibilidade** através de configurações personalizáveis
- **Transparência** com logs detalhados e estatísticas completas

**A funcionalidade está pronta para uso em produção! 🚀**