# 🐛 Issues Conhecidos

## ❌ Erro ao Adicionar Usuários ao Projeto - Escopo OAuth Insuficiente

**Status:** ✅ Causa Identificada - Pendente Resolução  
**Data:** 12/10/2025 | Atualizado: 15/10/2025  
**Prioridade:** Média

### Descrição
Ao tentar adicionar implantadores (RIS/PACS) ao projeto via API do Zoho, ocorre erro de permissão OAuth.

### Endpoint Afetado
```
POST https://projectsapi.zoho.com/api/v3/portal/{PORTAL_ID}/projects/{PROJECT_ID}/projectusers
```

### ✅ Descoberta (15/10/2025)

Após teste seguindo a **documentação oficial** do Zoho Projects API v3, identificamos que:

1. **Payload Correto** (conforme documentação):
   ```json
   {
     "userdetails": [{
       "email_id": "usuario@animati.com.br"
     }],
     "notify": false
   }
   ```
   - ✅ **NÃO** usar `zpuid` (não existe na documentação oficial)
   - ✅ Usar apenas `email_id` como campo obrigatório
   - ✅ Outros campos são opcionais: `profile_id`, `role_id`, `rate`, etc.

2. **Erro Real**:
   ```json
   {
     "error": {
       "status_code": "401",
       "title": "INVALID_OAUTHSCOPE",
       "error_type": "FIELDS_VALIDATION_ERROR",
       "details": [{
         "message": "Invalid OAuth scope."
       }]
     }
   }
   ```
   **Status Code:** 401 Unauthorized

### Causa Raiz Identificada

❌ **O token de acesso não possui escopo OAuth necessário para adicionar usuários ao projeto**

O erro 500 anterior era provavelmente um bug do Zoho ao tentar processar uma requisição sem permissão adequada.

### Escopos OAuth do Zoho Projects

**Escopo Necessário (provável):**
- `ZohoProjects.projectusers.CREATE` ou
- `ZohoProjects.projectusers.ALL` ou  
- `ZohoProjects.projects.ALL`

**Escopo Atual:**
- Provável que temos apenas escopo de leitura/escrita de projetos básicos
- Não temos escopo para gerenciar membros da equipe

### Payload Testado (Correto)
```json
{
  "userdetails": [{
    "email_id": "camilo.rodrigues@animati.com.br"
  }],
  "notify": false
}
```

### Próximos Passos para Resolução

1. **Investigar Escopos Disponíveis:**
   - Consultar documentação de OAuth do Zoho Projects
   - Identificar escopo específico para gerenciamento de usuários
   - Verificar se é `ZohoProjects.projectusers.ALL` ou similar

2. **Atualizar Configuração OAuth:**
   - Adicionar escopo necessário em `config.py` (similar ao que foi feito com Calendar)
   - Exemplo: Adicionar à lista de escopos do Zoho

3. **Re-autorizar Aplicação:**
   - Usuários precisarão fazer novo login OAuth
   - O Zoho solicitará permissão adicional para gerenciar membros da equipe
   - Novo token será gerado com permissões expandidas

4. **Re-testar:**
   - Executar `test_add_user_to_project.py` novamente
   - Verificar se requisição é autorizada (status 200)
   - Validar que usuário é adicionado ao projeto

5. **Implementar Funcionalidade:**
   - Após confirmação de funcionamento, implementar na função de criação de projeto
   - Adicionar tratamento de erros específico para escopo OAuth

### Workaround Temporário
Adicionar implantadores manualmente pelo painel web do Zoho Projects.

---

### Possíveis Causas
1. ❓ Problema temporário na API do Zoho
2. ❓ Permissões insuficientes no token de acesso
3. ❓ Formato do payload incompatível com a versão da API
4. ❓ ZPUID inválido para o portal específico
5. ❓ Usuário já existe no projeto (mas deveria retornar 200, não 500)

### Workarounds Temporários
- ✅ Adicionar implantadores manualmente no Zoho Projects antes de executar o agendamento
- ✅ Sistema continua funcionando para atribuir tarefas se os usuários já estiverem no projeto

### Próximos Passos
- [ ] Testar com diferentes combinações de usuários
- [ ] Verificar documentação atualizada da API do Zoho
- [ ] Verificar se há limitações de rate limit ou quota
- [ ] Tentar endpoint alternativo (v2 da API)
- [ ] Contactar suporte do Zoho se necessário

### Impacto
**Baixo** - As tarefas podem ser atribuídas manualmente ou após adicionar os implantadores ao projeto manualmente.

---

## ⚠️ Atualização de Datas Bloqueadas por Dependências de Tarefas

**Status:** Em Investigação  
**Data:** 13/10/2025  
**Prioridade:** Alta

### Descrição
Ao tentar atualizar a data de início de tarefas específicas que possuem dependências (predecessors/successors), a API do Zoho retorna erro 403 `CANNOT_MODIFY_DATE_WITH_DEPENDENCY_LAG`, mesmo usando o parâmetro `remove_dependency_lag: True` conforme documentado.

### Endpoint Afetado
```
PATCH https://projectsapi.zoho.com/api/v3/portal/{PORTAL_ID}/projects/{PROJECT_ID}/tasks/{TASK_ID}
```

### Payload Enviado
```json
{
  "start_date": "2025-10-23T00:00:00.000Z",
  "remove_dependency_lag": true
}
```

### Resposta da API
```json
{
  "error": {
    "title": "CANNOT_MODIFY_DATE_WITH_DEPENDENCY_LAG",
    "details": [{
      "message": "Alterar a data removerá o intervalo de tempo definido entre oTarefa e seu Tarefas predecessor"
    }]
  }
}
```
**Status Code:** 403 Forbidden

### Contexto
- **Funcionalidade:** Ajuste automático de datas de tarefas específicas para corresponder à data de início da implantação
- **Tarefas Afetadas:**
  - "Realizar reunião com cliente para entendimento do fluxo do cliente (RIS/PACS)"
  - "Checar o DEIP e os Docs de Infra"
  - "Envio dos Docs de Infra"

### Comportamento Observado
1. ✅ Tarefas **sem** dependências têm suas datas atualizadas com sucesso
2. ❌ Tarefas **com** dependências retornam erro 403, mesmo com `remove_dependency_lag: True`
3. ⚠️ O parâmetro `remove_dependency_lag` parece ser ignorado pela API

### Possíveis Causas
1. ❓ Bug na API do Zoho - parâmetro `remove_dependency_lag` não está funcional
2. ❓ Permissões insuficientes no token de acesso para modificar dependências
3. ❓ Parâmetro requer sintaxe diferente ou campo adicional não documentado
4. ❓ Restrição da API que requer remoção explícita de dependências antes da atualização de data

### Soluções Investigadas
- ❌ **Tentativa 1:** Usar parâmetro `remove_dependency_lag: True` (não funcionou)
- ⏳ **Tentativa 2:** Abordagem em múltiplas etapas:
  1. GET para obter dependências da tarefa
  2. DELETE para remover dependências
  3. PATCH para atualizar a data
  4. (Opcional) POST para restaurar dependências

### Workarounds Temporários
- ✅ Tarefas sem dependências continuam sendo atualizadas normalmente
- ⚠️ Estatística `datas_bloqueadas_dependencia` rastreia tarefas bloqueadas
- ⚠️ Avisos no log indicam quais tarefas não puderam ser atualizadas

### Próximos Passos
- [ ] Pesquisar endpoints da API do Zoho para gerenciar dependências de tarefas
- [ ] Implementar solução em múltiplas etapas (GET → DELETE → PATCH)
- [ ] Testar se remoção explícita de dependências permite atualização de data
- [ ] Avaliar impacto da remoção de dependências no cronograma do projeto
- [ ] Considerar opção de restaurar dependências após atualização da data
- [ ] Contactar suporte do Zoho se abordagem técnica não funcionar

### Impacto
**Médio** - Algumas tarefas específicas não têm suas datas ajustadas automaticamente, mas isso não impede o funcionamento do sistema. Usuários podem ajustar manualmente no Zoho Projects se necessário.

### Código Relacionado
- **Arquivo:** `implantacao_tarefas.py`
- **Função:** `atualizar_data_inicio_tarefa()`
- **Configuração:** `config.py` → `TAREFAS_AJUSTE_DATA_IMPLANTACAO`
- **Testes:** `test_ajuste_datas_tarefas.py` (25 testes passando - 100%)

---

## 📋 Melhorias Pendentes

### Mensagem Genérica na Tarefa de Validação do DEIP

**Status:** Pendente Correção  
**Data:** 15/10/2025  
**Prioridade:** Baixa

#### Descrição
Atualmente, quando um card é movido para **"Falta Liberar Servidor Infra"**, é adicionado um comentário genérico na tarefa "Validação do DEIP" informando apenas que o projeto foi movido, sem contexto específico sobre a ação necessária.

#### Problema Atual

**Tarefa Afetada:** "Validação do DEIP"

**Mensagem Atual:**
```
Projeto movido para 'Falta Liberar Servidor Infra'. Onboarding realizado.
```

**Problema:** 
- ❌ Mensagem genérica sem ação clara
- ❌ Não solicita explicitamente a liberação do servidor
- ❌ Falta contexto sobre o que precisa ser feito

#### Comportamento Desejado

**Mensagem Sugerida:**
```
Onboarding realizado com sucesso! 

Por favor, solicitar à equipe de infraestrutura a liberação do servidor para início das atividades de implantação.

Após a liberação, atualizar o status do projeto para "Em Andamento".
```

**OU (mais direto):**
```
@{Equipe Infra}, favor liberar o servidor para início da implantação.

Detalhes do projeto: [link ou descrição]
```

#### Implementação

**Arquivo:** `mapeamento_colunas.json`

**Localização:** Seção "Falta Liberar Servidor Infra" → triggers → taskComment "Validação do DEIP"

**Alteração Sugerida:**
```json
{
  "type": "taskComment",
  "taskName": "Validação do DEIP",
  "template": "Onboarding realizado com sucesso! Por favor, solicitar à equipe de infraestrutura a liberação do servidor para início das atividades de implantação."
}
```

#### Impacto
**Baixo** - Melhoria de UX e clareza de comunicação. Não afeta funcionalidade crítica.

---

### Notificações em Tarefas ao Mover para "Falta Liberar Servidor Infra"

**Status:** Pendente Implementação  
**Data:** 15/10/2025  
**Prioridade:** Média

#### Descrição
Quando um card é movido de **"Aguardando Onboarding"** para **"Falta Liberar Servidor Infra"**, o sistema deve enviar comentários automáticos nas tarefas de integração e importação informando que os grupos foram criados.

#### Comportamento Desejado

**Evento:** Card movido de "Aguardando Onboarding" → "Falta Liberar Servidor Infra"

**Ações:**
1. Adicionar comentário na(s) tarefa(s) de **Integração**:
   ```
   Grupos criados com sucesso. Servidor aguardando liberação pela infraestrutura.
```2. Adicionar comentário na(s) tarefa(s) de **Importação**:
   ```
   Grupos criados com sucesso. Servidor aguardando liberação pela infraestrutura.
   ```

#### Tarefas Candidatas
- Tarefas com nome contendo: "integração", "worklist", "retorno de laudos"
- Tarefas com nome contendo: "importação", "cadastros", "prontuários"

#### Implementação Sugerida
Adicionar em `mapeamento_colunas.json` na seção **"Falta Liberar Servidor Infra"**:

```json
{
  "Falta Liberar Servidor Infra": {
    "triggers": [
      {
        "type": "taskComment",
        "taskNamePattern": "(integr|worklist|laudo)",
        "template": "Grupos criados com sucesso. Servidor aguardando liberação pela infraestrutura.",
        "optional": true
      },
      {
        "type": "taskComment", 
        "taskNamePattern": "(import|cadastro|prontu)",
        "template": "Grupos criados com sucesso. Servidor aguardando liberação pela infraestrutura.",
        "optional": true
      }
    ]
  }
}
```

**Observação:** Requer implementação de busca por regex em `taskNamePattern` na função `_executar_triggers()`.

---

### Notificações em Tarefas ao Sair de "Falta Liberar Servidor Infra"

**Status:** Pendente Implementação  
**Data:** 15/10/2025  
**Prioridade:** Média

#### Descrição
Quando um card é movido **DE** "Falta Liberar Servidor Infra" **PARA** qualquer outra coluna (normalmente "Em Andamento"), o sistema deve enviar comentários automáticos nas tarefas de integração e importação informando que o servidor foi liberado.

#### Comportamento Desejado

**Evento:** Card movido de "Falta Liberar Servidor Infra" → (qualquer coluna de destino)

**Ações:**
1. Adicionar comentário na(s) tarefa(s) de **Integração**:
   ```
   Servidor liberado pela infraestrutura. Podem dar sequência nas atividades de integração.
   ```

2. Adicionar comentário na(s) tarefa(s) de **Importação**:
   ```
   Servidor liberado pela infraestrutura. Podem dar sequência nas atividades de importação.
   ```

#### Tarefas Candidatas
- Tarefas com nome contendo: "integração", "worklist", "retorno de laudos", "RIS/HIS"
- Tarefas com nome contendo: "importação", "cadastros", "prontuários"

#### Implementação Sugerida
Adicionar em `mapeamento_colunas.json` na seção **"Falta Liberar Servidor Infra"** usando `onExit`:

```json
{
  "Falta Liberar Servidor Infra": {
    "onExit": {
      "triggers": [
        {
          "type": "taskComment",
          "taskNamePattern": "(integr|worklist|laudo|ris|his)",
          "template": "Servidor liberado pela infraestrutura. Podem dar sequência nas atividades de integração.",
          "optional": true
        },
        {
          "type": "taskComment",
          "taskNamePattern": "(import|cadastro|prontu)",
          "template": "Servidor liberado pela infraestrutura. Podem dar sequência nas atividades de importação.",
          "optional": true
        }
      ]
    }
  }
}
```

**Observações:**
- Requer implementação de `onExit.triggers` na função `api_mover_projeto()`
- Requer suporte a `taskNamePattern` com regex na função `_executar_triggers()`
- Triggers devem ser `optional: true` para não bloquear movimentação se tarefas não existirem

---

## ✅ Issues Resolvidos

### Data de Início da Implantação Sempre com Data Atual
**Status:** ✅ Resolvido  
**Data:** 12/10/2025

**Problema:** Campo `data_de_inicio_da_implantacao` era preenchido com a data atual em vez da data selecionada no modal.

**Solução:** Removido placeholder `"CURRENT_DATE"` do `mapeamento_colunas.json`, permitindo que o código defina explicitamente a data do modal.

**Arquivo Modificado:** `mapeamento_colunas.json` (linha 69)

---

**Última atualização:** 15/10/2025
