# Correção: Sincronização de Fases/Milestones

## Problema Identificado

Após clicar em "Agendar Implantação" e o projeto ser movido para a coluna "Em Andamento - Implantação", **as fases (milestones) não estavam sendo salvas no banco de dados local**, consequentemente não exibindo o percentual de conclusão das fases no Kanban.

### Comportamento Esperado
- As fases são criadas no Zoho Projects junto com o projeto
- Quando um projeto está na fase de infraestrutura, as fases devem aparecer no banco de dados
- No Kanban, deve aparecer o percentual de conclusão das fases
- Após "Agendar Implantação", as demais fases devem continuar visíveis

### Comportamento Observado
- Tabela `fases` estava vazia no banco de dados
- Kanban não exibia percentual de conclusão
- Sincronização periódica funcionava, mas sincronização individual (durante ações do usuário) não

## Análise da Causa Raiz

A função `synchronize_single_project()` em `sync_zoho.py` era responsável por sincronizar um projeto específico quando ações eram executadas (como "Agendar Implantação" via `iniciar_implantacao()`).

### Fluxo de Chamadas
```
routes/api.py: iniciar_implantacao()
    ↓
routes/api.py: _sincronizar_db_local_forcado()
    ↓
sync_zoho.py: synchronize_single_project()
    ↓
database.py: upsert_project()  ✅ (projeto sincronizado)
    ✗ sync_fases() NÃO ERA CHAMADO
```

### Comparação: Sincronização Completa vs. Individual

**Sincronização completa (funcionava):**
```python
# sync_zoho.py: synchronize_projects()
for project in projects:
    upsert_project(project)
    sync_fases(project_id, access_token)  # ✅ CHAMADO
    sync_listas_e_tarefas(...)
```

**Sincronização individual (não funcionava):**
```python
# sync_zoho.py: synchronize_single_project()
upsert_project(project)
# ✗ sync_fases() NÃO ERA CHAMADO
```

## Solução Implementada

### Modificação em `sync_zoho.py`

Adicionada chamada a `sync_fases()` na função `synchronize_single_project()`:

```python
def synchronize_single_project(project_id, access_token):
    # ... código existente ...
    
    upsert_project(project)
    print(f"Sincronizado projeto único: {project.get('name')} (ID: {project.get('id')})")
    
    # NOVO: Sincronizar também as fases/milestones do projeto
    print(f"  - Sincronizando fases do projeto {project_id}...")
    try:
        sync_fases(project_id, access_token)
        print(f"  - Fases sincronizadas com sucesso para o projeto {project_id}")
    except Exception as e:
        print(f"  - Erro ao sincronizar fases do projeto {project_id}: {e}")
    
    return True
```

### Benefícios da Correção

1. **Paridade funcional**: Sincronização individual agora tem o mesmo comportamento da sincronização completa
2. **Robustez**: Try-except garante que falha na sincronização de fases não impeça a sincronização do projeto
3. **Logging**: Mensagens de debug para rastreamento
4. **Imediatismo**: Fases disponíveis imediatamente após ações do usuário, sem precisar esperar sincronização periódica

## Impacto

### Antes da Correção
- ❌ Fases não sincronizadas após "Agendar Implantação"
- ❌ Percentual não exibido no Kanban
- ⚠️ Dados só apareciam após sincronização periódica (delay)

### Após a Correção
- ✅ Fases sincronizadas imediatamente após qualquer atualização de projeto individual
- ✅ Percentual de conclusão visível no Kanban
- ✅ Dados consistentes em tempo real

## Contexto Técnico

### Estrutura da Tabela `fases`
```sql
CREATE TABLE IF NOT EXISTS fases (
    id TEXT PRIMARY KEY,
    projeto_id TEXT NOT NULL,
    nome TEXT NOT NULL,
    status TEXT,
    percentual_conclusao INTEGER DEFAULT 0,
    FOREIGN KEY (projeto_id) REFERENCES projects(id)
);
```

### Endpoint Zoho API
- **Listar fases**: `GET /portal/{portal_id}/projects/{project_id}/phases`
- **Detalhe da fase**: `GET /portal/{portal_id}/projects/{project_id}/phases/{phase_id}`
  - Retorna `completion_percent` usado para exibir progresso

### Função `sync_fases()`
1. Busca lista de milestones/fases do projeto
2. Para cada fase, busca detalhes (incluindo `completion_percent`)
3. Salva no banco via `upsert_fase()`

## Testes Recomendados

1. ✅ Criar novo projeto no Zoho
2. ✅ Verificar se fases aparecem no banco após primeiro sincronização
3. ✅ Clicar em "Agendar Implantação"
4. ✅ Verificar se fases permanecem no banco e são atualizadas
5. ✅ Confirmar exibição de percentual no Kanban
6. ✅ Testar com projetos em diferentes colunas/status

## Arquivos Modificados

- ✅ `sync_zoho.py` - Adicionada sincronização de fases em `synchronize_single_project()`

## Relacionado

- Correção anterior: `CORRECAO_ATRIBUICAO_TAREFAS_IMPLANTADOR.md` (tags de "Aguardando Cronograma")
- Sincronização completa: Função `synchronize_projects()` sempre funcionou corretamente
- Sistema de fases: Usado para exibir barras de progresso no Kanban

## Data da Correção

2025-XX-XX (a ser preenchida após merge)
