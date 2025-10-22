# Arquivos para Limpeza - Central de Projetos

## 📋 Categorias de Arquivos para Remoção

### 🧪 Arquivos de Teste (teste_*.py)
Arquivos criados durante desenvolvimento e debugging dos campos de implantadores:

- `teste_api_v3.py`
- `teste_atualizacao_final_implantadores.py`
- `teste_atualizar_implantadores_completo.py`
- `teste_campos_implantadores_direto.py` ✅ **MANTER (teste que funcionou)**
- `teste_campos_texto.py`
- `teste_envio_formato_correto.py`
- `teste_final_campos_texto.py`
- `teste_formato_correto_zoho.py`
- `teste_nome_completo.py`
- `teste_restapi_v1.py`
- `teste_restapi_v1_maiusculo.py`
- `teste_restapi_v1_post_formdata.py`
- `teste_usuarios_equipes_corretas.py`
- `teste_zpuid_formatos.py`
- `teste_zpuids_corretos.py`

### 🧪 Arquivos de Teste (testar_*.py)

- `testar_custom_fields_structure.py`
- `testar_filtros_implementados.py`
- `testar_leitura_implantadores.py`
- `testar_novo_formato_implantadores.py`
- `testar_ordenacao.py`
- `testar_todos_formatos_nomes.py`

### 🧪 Arquivos de Teste (test_*.py)

- `test_add_user_detailed.py`
- `test_add_user_final.py`
- `test_add_user_to_project.py`
- `test_ajuste_datas_tarefas.py`
- `test_alternative_endpoint.py`
- `test_completo_ferramentas.py`
- `test_custom_field.py`
- `test_date_format.py`
- `test_descobrir_ids.py`
- `test_endpoint_progresso.py`
- `test_endpoint_progresso_completo.py`
- `test_extrair_nome_cliente.py`
- `test_google_calendar.py`
- `test_implantacao_tarefas.py`
- `test_implantadores.py`
- `test_novo_projeto_produto.py`
- `test_pasta_drive.py`
- `test_payload.py`
- `test_progresso_fix.py`
- `test_quick_extraction.py`
- `test_simple.py`
- `test_status_change.py`
- `test_task_assignment.py`
- `test_task_finding.py`
- `test_with_access_token.py`

### 🔍 Arquivos de Debug

- `debug_busca_cliente.py`
- `debug_implantadores_zoho.py`
- `debug_projeto.py`

### 🔍 Arquivos de Diagnóstico

- `diagnostico_completo_custom_fields.py`
- `diagnostico_payload_implantadores.py`

### 🔍 Arquivos de Verificação

- `verificar_atualizacao.py`
- `verificar_campos_no_projeto.py`
- `verificar_fases_ris.py`
- `verificar_formato_manual.py`
- `verificar_projeto_zoho.py`
- `verificar_resposta_post.py`
- `verify_token_scopes.py`
- `validate_status_ids.py`
- `validar_filtro_projetos.py`

### 🔍 Arquivos de Descoberta/Investigação

- `descobrir_nomes_exatos_campos.py`
- `descobrir_picklist_values.py`
- `descobrir_usuarios_validos.py`
- `discover_all_status.py`
- `investigar_custom_fields_completo.py`

### 🔍 Arquivos de Busca

- `buscar_todos_custom_fields.py`
- `buscar_zpuids_v1.py`
- `check_custom_fields.py`

### 📦 Arquivos Antigos/Não Utilizados

- `app_antigo.py` - Versão antiga do app principal
- `analisar_pacs.py`
- `customizados.py`
- `ipv6.py`
- `projeto.py`
- `usuario.py`
- `zoho_fields.py`

### 📝 Arquivos de Utilitário que PODEM ser mantidos para consultas futuras

- `gerar_zoho_token.py` ✅ **MANTER (útil para regenerar tokens)**
- `gerar_json_equipe.py` ✅ **MANTER (gera equipe_implantacao_classificada.json)**
- `get_custom_fields.py` - Consultar campos custom
- `get_custom_fields_v3.py` - Consultar campos custom v3
- `get_layout_fields.py` - Consultar layout
- `get_project_details.py` - Consultar detalhes projeto
- `get_project_layout.py` - Consultar layout projeto
- `list_custom_fields.py` - Listar campos custom
- `listar_usuarios_projeto.py` - Listar usuários
- `find_completed_status.py` - Encontrar status completado

### 📋 Arquivos PRINCIPAIS (NÃO REMOVER)

- `app.py` ✅ **PRINCIPAL**
- `config.py` ✅ **PRINCIPAL**
- `database.py` ✅ **PRINCIPAL**
- `google_calendar.py` ✅ **PRINCIPAL**
- `implantacao_config.py` ✅ **PRINCIPAL**
- `implantacao_manager.py` ✅ **PRINCIPAL**
- `implantacao_tarefas.py` ✅ **PRINCIPAL**
- `phases.py` ✅ **PRINCIPAL**
- `sync_zoho.py` ✅ **PRINCIPAL**
- `utils.py` ✅ **PRINCIPAL**
- `dryrun_zoho_payload.py` ✅ **PRINCIPAL**
- `buscar_tarefas.py` ✅ **PRINCIPAL**
- `create_real_zoho_project.py` ✅ **PRINCIPAL**
- `routes/api.py` ✅ **PRINCIPAL**
- `routes/main.py` ✅ **PRINCIPAL**

## 🗑️ Resumo de Ações Recomendadas

### Remover imediatamente (58 arquivos):
- Todos os `teste_*.py` (exceto `teste_campos_implantadores_direto.py`)
- Todos os `testar_*.py`
- Todos os `test_*.py`
- Todos os `debug_*.py`
- Todos os `diagnostico_*.py`
- Todos os `verificar_*.py` e `validar_*.py`
- Todos os `descobrir_*.py` e `investigar_*.py`
- Arquivos antigos: `app_antigo.py`, `analisar_pacs.py`, etc.

### Mover para pasta `/scripts` (utilitários, 10 arquivos):
- `gerar_zoho_token.py`
- `gerar_json_equipe.py`
- `get_custom_fields.py`
- `get_custom_fields_v3.py`
- `get_layout_fields.py`
- `get_project_details.py`
- `get_project_layout.py`
- `list_custom_fields.py`
- `listar_usuarios_projeto.py`
- `find_completed_status.py`

### Manter na raiz (14 arquivos principais):
- `app.py`
- `config.py`
- `database.py`
- `google_calendar.py`
- `implantacao_config.py`
- `implantacao_manager.py`
- `implantacao_tarefas.py`
- `phases.py`
- `sync_zoho.py`
- `utils.py`
- `dryrun_zoho_payload.py`
- `buscar_tarefas.py`
- `create_real_zoho_project.py`
- `teste_campos_implantadores_direto.py` (teste que funcionou - para referência)
