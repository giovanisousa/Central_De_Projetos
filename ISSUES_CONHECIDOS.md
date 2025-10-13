# 🐛 Issues Conhecidos

## ❌ Erro 500 ao Adicionar Usuários ao Projeto

**Status:** Pendente investigação  
**Data:** 12/10/2025  
**Prioridade:** Média

### Descrição
Ao tentar adicionar implantadores (RIS/PACS) ao projeto via API do Zoho, ocorre erro 500 (Internal Server Error).

### Endpoint Afetado
```
POST https://projectsapi.zoho.com/api/v3/portal/{PORTAL_ID}/projects/{PROJECT_ID}/projectusers
```

### Payload Enviado
```json
{
  "userdetails": [{
    "email_id": "implantador@animati.com.br",
    "zpuid": "2376502000000080073"
  }],
  "notify": "false"
}
```

### Resposta da API
```
Status Code: 500
Message: Internal Server Error
```

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

## ✅ Issues Resolvidos

### Data de Início da Implantação Sempre com Data Atual
**Status:** ✅ Resolvido  
**Data:** 12/10/2025

**Problema:** Campo `data_de_inicio_da_implantacao` era preenchido com a data atual em vez da data selecionada no modal.

**Solução:** Removido placeholder `"CURRENT_DATE"` do `mapeamento_colunas.json`, permitindo que o código defina explicitamente a data do modal.

**Arquivo Modificado:** `mapeamento_colunas.json` (linha 69)

---

**Última atualização:** 12/10/2025
