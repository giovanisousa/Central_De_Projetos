# Plano de Implementação dos Filtros no Código Principal

## Objetivo
Implementar os filtros validados no arquivo `sync_zoho.py` para que apenas projetos relevantes sejam salvos no banco de dados.

## Alterações Necessárias

### 1. Atualizar `config.py`
Adicionar as constantes para validação de proprietários:

```python
# Nomes dos proprietários válidos (a API retorna apenas o nome, não o ID)
PROPRIETARIOS_VALIDOS = {
    "Giovani de Sousa",
    "Giovani",
    "Willian dos Anjos",
    "willian.anjos",
    "Willian Anjos",
}
```

### 2. Atualizar `sync_zoho.py`
Criar uma função de validação e aplicar nos dois pontos onde projetos são processados.

#### A) Adicionar função de validação no início do arquivo:

```python
from config import (
    ZOHO_PORTAL_ID, 
    PROPRIETARIOS_VALIDOS,
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
)

# IDs dos status que devem ser EXCLUÍDOS
STATUS_EXCLUIDOS = {
    STATUS_CANCELADO_ID,
    STATUS_FINALIZADO_ID,
    STATUS_CONCLUIDO_ID
}


def projeto_deve_ser_salvo(project_data):
    """
    Verifica se um projeto atende aos critérios para ser salvo no banco.
    
    Critérios:
    1. Proprietário deve ser Giovani OU Willian
    2. Status NÃO deve ser Cancelado, Finalizado ou Concluído
    
    Args:
        project_data: Dicionário com os dados do projeto da API do Zoho
        
    Returns:
        bool: True se o projeto deve ser salvo, False caso contrário
    """
    # Valida proprietário
    owner = project_data.get('owner', {})
    owner_name = owner.get('name', '')
    proprietario_valido = owner_name in PROPRIETARIOS_VALIDOS
    
    # Valida status
    status = project_data.get('status', {})
    status_id = str(status.get('id', ''))
    status_valido = status_id not in STATUS_EXCLUIDOS
    
    # Retorna True apenas se AMBOS os critérios forem atendidos
    return proprietario_valido and status_valido
```

#### B) Aplicar filtro na função `synchronize_projects()`:

Localizar o trecho:
```python
for project in projects:
    try:
        upsert_project(project)
        print(f"  -> Sincronizado projeto: {project.get('name')} (ID: {project.get('id')})")
```

Substituir por:
```python
for project in projects:
    try:
        # Aplica filtro antes de salvar
        if not projeto_deve_ser_salvo(project):
            owner_name = project.get('owner', {}).get('name', 'Desconhecido')
            status_name = project.get('status', {}).get('name', 'Desconhecido')
            print(f"  -> Projeto ignorado: {project.get('name')} - Proprietário: {owner_name}, Status: {status_name}")
            continue
            
        upsert_project(project)
        print(f"  -> Sincronizado projeto: {project.get('name')} (ID: {project.get('id')})")
```

#### C) Aplicar filtro na função `synchronize_single_project()`:

Localizar o trecho:
```python
project = _extract_project_from_response(data, project_id)
if project:
    upsert_project(project)
    print(f"Sincronizado projeto único: {project.get('name')} (ID: {project.get('id')})")
    return True
```

Substituir por:
```python
project = _extract_project_from_response(data, project_id)
if project:
    # Aplica filtro antes de salvar
    if not projeto_deve_ser_salvo(project):
        owner_name = project.get('owner', {}).get('name', 'Desconhecido')
        status_name = project.get('status', {}).get('name', 'Desconhecido')
        print(f"Projeto ignorado (não atende critérios): {project.get('name')} - Proprietário: {owner_name}, Status: {status_name}")
        return False
        
    upsert_project(project)
    print(f"Sincronizado projeto único: {project.get('name')} (ID: {project.get('id')})")
    return True
```

### 3. Limpeza do Banco de Dados (Opcional)
Se desejar remover projetos já existentes que não atendem aos critérios:

```python
# Script para limpar banco de dados
import sqlite3
from config import PROPRIETARIOS_VALIDOS, STATUS_CANCELADO_ID, STATUS_FINALIZADO_ID, STATUS_CONCLUIDO_ID

conn = sqlite3.connect('zoho_cache.db')
cursor = conn.cursor()

# Buscar todos os projetos
cursor.execute('SELECT id, nome, gp, status_atual FROM projects')
projetos = cursor.fetchall()

removidos = 0
for proj in projetos:
    proj_id, nome, gp, status = proj
    
    # Verificar se deve ser removido
    gp_invalido = gp not in PROPRIETARIOS_VALIDOS
    status_invalido = status in ['Cancelado', 'Completed', 'Concluído', 'Finalizado']
    
    if gp_invalido or status_invalido:
        cursor.execute('DELETE FROM projects WHERE id = ?', (proj_id,))
        print(f"Removido: {nome} - GP: {gp}, Status: {status}")
        removidos += 1

conn.commit()
print(f"\nTotal de projetos removidos: {removidos}")
conn.close()
```

## Testes

### 1. Teste de Validação
```bash
python validar_filtro_projetos.py
```
Verifique se os números continuam corretos (116 válidos, 292 rejeitados).

### 2. Teste de Sincronização
```bash
# Backup do banco atual
copy zoho_cache.db zoho_cache.db.backup

# Limpar banco para teste limpo
# Ou simplesmente executar a sincronização
```

### 3. Verificar no aplicativo
```bash
python app.py
```
Acesse http://localhost:5000 e verifique se apenas os projetos esperados aparecem no kanban.

## Checklist de Implementação

- [ ] 1. Adicionar constante `PROPRIETARIOS_VALIDOS` no `config.py`
- [ ] 2. Adicionar imports no `sync_zoho.py`
- [ ] 3. Adicionar função `projeto_deve_ser_salvo()` no `sync_zoho.py`
- [ ] 4. Aplicar filtro na função `synchronize_projects()`
- [ ] 5. Aplicar filtro na função `synchronize_single_project()`
- [ ] 6. Testar com `python validar_filtro_projetos.py`
- [ ] 7. Fazer backup do banco de dados
- [ ] 8. Executar sincronização e verificar logs
- [ ] 9. Testar aplicação web
- [ ] 10. (Opcional) Limpar projetos antigos do banco

## Observações

- Os filtros são aplicados **antes** de salvar no banco
- Projetos ignorados são registrados nos logs para auditoria
- A função `upsert_project` não precisa ser alterada
- Sincronizações futuras já virão filtradas automaticamente
