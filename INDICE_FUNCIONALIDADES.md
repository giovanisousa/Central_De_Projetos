# 📚 Índice de Funcionalidades - Central de Projetos

**Última atualização**: 13 de outubro de 2025

---

## 🎯 Funcionalidades Principais

### 1. 🎨 Dashboard Kanban
- Visualização de projetos em colunas (Aguardando Onboarding, Em Andamento, Em Homologação, etc.)
- Arrastar e soltar cards entre colunas
- Atualização automática de status no Zoho Projects e Google Sheets
- **Documentação**: `README.md`

### 2. 📅 Cálculo Automático de Dias na Fase
- Badge colorido mostrando tempo na fase atual
- Atualização em tempo real sem necessidade de refresh
- **Documentação**: `IMPLEMENTACAO_DIAS_FASE.md`, `MELHORIA_ATUALIZACAO_IMEDIATA_CARD.md`

### 3. 🏷️ Gestão Automática de Tags e Status
- Configuração centralizada em `mapeamento_colunas.json`
- Adição/remoção automática de tags no Zoho
- Atualização de status do projeto
- **Documentação**: `mapeamento_colunas.json` (comentado)

### 4. 🔄 Sincronização Multi-Plataforma
- **Zoho Projects**: Status, tags, campos customizados
- **Google Sheets**: Status principal, datas, informações do projeto
- **Banco de Dados Local**: Cache para performance
- **Documentação**: `ANALISE_DIAS_FASE_E_DATA_MUDANCA.md`

---

## 🆕 Funcionalidades Recentes

### ✅ Ações Automáticas para "Em Homologação" (13/10/2025)
Quando um card é movido para "Em Homologação":
- ✅ Remove tag "Em Implantação" no Zoho
- ✅ Adiciona tag "Em Homologação" no Zoho
- ✅ Preenche campo `data_de_homologacao` no Zoho
- ✅ Atualiza "Status Principal" na planilha
- ✅ Preenche coluna "Dt Homolog" na planilha

**Documentação**: 
- `FEATURE_EM_HOMOLOGACAO.md` (Documentação técnica completa)
- `RESUMO_EM_HOMOLOGACAO.md` (Resumo executivo)

---

## 📋 Funcionalidades por Transição de Coluna

### Aguardando Onboarding → Falta Liberar Servidor Infra
- Adiciona tag "Aguardando Infra"
- Remove tag "Aguardando Onboarding"
- Preenche `data_de_onboarding` ao **sair** da coluna

### Falta Liberar Servidor Infra → Em Andamento
- Remove tag "Aguardando Infra"
- Preenche `data_liberacao_servidor` no Zoho
- Atualiza coluna "Lib.Servidor" na planilha (DD/MM/YYYY)
- Busca e preenche coluna "VPN" com IPv6 (se disponível)

### [Qualquer] → Em Andamento - Implantação
- Adiciona tag "Em Implantação"
- Preenche `data_de_inicio_da_implantacao` no Zoho

### Em Andamento - Implantação → Em Homologação ⭐ **NOVO**
- Remove tag "Em Implantação"
- Adiciona tag "Em Homologação"
- Preenche `data_de_homologacao` no Zoho
- Atualiza coluna "Dt Homolog" na planilha
- Adiciona comentário na tarefa de validação do DEIP

### [Qualquer] → Em Virada
- Adiciona tag "Em Virada"

### [Qualquer] → Em Operação Assistida
- Muda status para "Operação Assistida"

### [Qualquer] → Aguardando Encerramento
- Adiciona tag "Aguardando Encerramento"

### [Qualquer] → Finalizado
- Muda status para "Finalizado"
- Executa workflow de preenchimento DPI
- Adiciona comentário de conclusão

### [Qualquer] → Projeto Parado
- Adiciona tag "Parado"
- Muda status para "Pendência"

### [Qualquer] → Cancelado
- Muda status para "Cancelado"

---

## 🔧 Arquivos de Configuração

### `mapeamento_colunas.json`
**Propósito**: Define comportamento de cada coluna do Kanban

**Estrutura**:
```json
{
  "Nome da Coluna": {
    "sheetStatus": "Status na Planilha",
    "zohoStatusId": "ID do Status no Zoho",
    "zohoTagsToAdd": ["IDs de tags para adicionar"],
    "zohoTagsToRemove": ["IDs de tags para remover"],
    "zohoCustomFields": {
      "nome_campo": "CURRENT_DATE"
    },
    "triggers": [...],
    "onExit": {
      "zohoCustomFields": {...}
    },
    "onTransition": {
      "from_Coluna_Origem": {
        "sheetColumns": {
          "Nome Coluna": "CURRENT_DATE_DDMMYYYY"
        }
      }
    }
  }
}
```

### `config.py`
**Propósito**: Constantes e IDs do sistema

**Principais seções**:
- IDs de Status do Zoho
- IDs de Tags do Zoho
- Configurações de API (Google, Zoho)
- Mapeamentos de donos, grupos, modelos

---

## 📊 Campos Customizados no Zoho

| Campo | Descrição | Formato | Quando Preenche |
|-------|-----------|---------|-----------------|
| `data_de_onboarding` | Data do onboarding | YYYY-MM-DD | Ao sair de "Aguardando Onboarding" |
| `data_liberacao_servidor` | Data de liberação do servidor | YYYY-MM-DD | Ao mover para "Em Andamento" |
| `data_de_inicio_da_implantacao` | Data de início da implantação | YYYY-MM-DD | Ao mover para "Em Andamento - Implantação" |
| `data_de_homologacao` ⭐ | Data de entrada em homologação | YYYY-MM-DD | Ao mover para "Em Homologação" |

---

## 📊 Colunas da Planilha Principal

| Coluna | Descrição | Formato | Quando Atualiza |
|--------|-----------|---------|-----------------|
| Status Principal | Status atual do projeto | Texto | Toda movimentação |
| Lib.Servidor | Data de liberação do servidor | DD/MM/YYYY | Infra → Em Andamento |
| VPN | IPv6 da VPN | Texto | Infra → Em Andamento |
| Dt Homolog ⭐ | Data de entrada em homologação | DD/MM/YYYY | Implantação → Em Homologação |

---

## 🔍 Placeholders Suportados

### Para Campos Customizados do Zoho:
- `CURRENT_DATE` → Formato: `YYYY-MM-DD` (ex: `2025-10-13`)

### Para Colunas da Planilha:
- `CURRENT_DATE_DDMMYYYY` → Formato: `DD/MM/YYYY` (ex: `13/10/2025`)
- `CURRENT_DATE` → Formato: `YYYY-MM-DD` (ex: `2025-10-13`)

---

## 📖 Documentação Disponível

### Implementações de Features
- `FEATURE_EM_HOMOLOGACAO.md` - Documentação completa da feature "Em Homologação"
- `FEATURE_BARRAS_PROGRESSO.md` - Sistema de barras de progresso
- `FEATURE_DATA_HOMOLOGACAO_PREVISTA.md` - Cálculo de data prevista
- `FEATURE_FERRAMENTAS_CARD.md` - Indicadores de ferramentas nos cards

### Resumos Executivos
- `RESUMO_EM_HOMOLOGACAO.md` - Resumo da implementação "Em Homologação"
- `RESUMO_IMPLEMENTACAO.md` - Resumo geral de implementações
- `RESUMO_ALTERACOES_GOOGLE_CALENDAR.md` - Integração com Google Calendar

### Implementações Concluídas
- `IMPLEMENTACAO_CONCLUIDA.md` - Status de implementações
- `IMPLEMENTACAO_DIAS_FASE.md` - Sistema de dias na fase
- `IMPLEMENTACAO_FILTROS_CONCLUIDA.md` - Sistema de filtros do Kanban

### Análises Técnicas
- `ANALISE_DIAS_FASE_E_DATA_MUDANCA.md` - Análise técnica do sistema de dias
- `ANALISE_PERFORMANCE.md` - Otimizações de performance

### Guias e Tutoriais
- `GUIA_CONFIGURACAO_TAREFAS.md` - Configuração de tarefas no Zoho
- `GUIA_RAPIDO_AJUSTE_DATAS.md` - Ajuste de datas de tarefas
- `GUIA_RAPIDO_GOOGLE_CALENDAR.md` - Integração Google Calendar

### Correções e Melhorias
- `MELHORIA_ATUALIZACAO_IMEDIATA_CARD.md` - Atualização imediata de cards
- `SOLUCAO_AUTO_RELOAD.md` - Auto-reload da interface

### Integrações
- `INTEGRACAO_GOOGLE_CALENDAR.md` - Sistema de calendário

---

## 🚀 Roadmap

### Em Desenvolvimento
- [ ] Notificações por e-mail em eventos críticos
- [ ] Relatórios de performance de projetos
- [ ] Dashboard de métricas gerenciais

### Planejado
- [ ] Integração com Slack/Teams para notificações
- [ ] API REST pública para integrações externas
- [ ] App mobile (visualização)

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask**: Framework web
- **SQLite3**: Banco de dados local (cache)
- **Requests**: Comunicação com APIs

### APIs Externas
- **Zoho Projects API v3**: Gestão de projetos
- **Google Drive API v3**: Armazenamento de arquivos
- **Google Sheets API v4**: Planilhas
- **Google Calendar API v3**: Agendamento

### Frontend
- **HTML5 + CSS3**: Interface
- **JavaScript (Vanilla)**: Interatividade
- **SortableJS**: Drag & drop do Kanban

---

## 📞 Suporte e Contribuição

### Reportar Problemas
1. Verificar logs no console do backend
2. Consultar documentação relevante
3. Criar issue com detalhes do erro

### Adicionar Nova Funcionalidade
1. Documentar no formato estabelecido
2. Atualizar este índice
3. Adicionar testes quando aplicável

---

## 📝 Convenções de Documentação

### Arquivos de Feature
- `FEATURE_*.md` - Documentação técnica completa
- `RESUMO_*.md` - Resumo executivo para usuários
- `IMPLEMENTACAO_*.md` - Detalhes de implementação

### Símbolos Utilizados
- ✅ - Implementado e testado
- 🚧 - Em desenvolvimento
- ⭐ - Nova funcionalidade
- ❌ - Deprecated/Removido

---

**Última atualização**: 13 de outubro de 2025  
**Versão do Sistema**: 2.0
