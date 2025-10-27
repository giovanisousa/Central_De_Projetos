# Feature: Agendar Homologação

**Data**: 27 de outubro de 2025  
**Status**: ✅ Implementado

---

## 🎯 Objetivo

Implementar modal "Agendar Homologação" que permite:
1. Selecionar data de homologação
2. Atribuir implantadores (RIS e/ou PACS)
3. Mover projeto para "Em Homologação"
4. Atribuir tarefas de homologação aos implantadores
5. Atualizar planilha com a data informada

---

## 🔧 Implementação

### Arquivos Criados

#### 1. `tarefas_homologacao_ris.json`
```json
[
  "02.01.01 - Validação do DEIP",
  "02.01.02 - Homologação Worklist",
  "02.01.03 - Homologação Retorno de Laudo",
  "02.01.04 - Homologação Cadastros Importados",
  "02.01.05 - Validação Fluxo Completo RIS",
  "02.01.06 - Teste de Performance RIS",
  "02.01.07 - Homologação Relatórios RIS"
]
```

#### 2. `tarefas_homologacao_pacs.json`
```json
[
  "02.02.01 - Validação Visualização PACS",
  "02.02.02 - Homologação Upload de Imagens",
  "02.02.03 - Homologação Integração DICOM",
  "02.02.04 - Teste de Performance PACS",
  "02.02.05 - Validação Armazenamento",
  "02.02.06 - Homologação Viewer Animati"
]
```

### Novo Endpoint: `/api/agendar_homologacao`

**Método**: `POST`

**Payload**:
```json
{
  "project_id": "2376502000006237137",
  "data_homologacao": "2025-11-15",
  "implantador_ris": "usuario.ris@animati.com.br",
  "implantador_pacs": "usuario.pacs@animati.com.br"
}
```

**Resposta de Sucesso**:
```json
{
  "sucesso": true,
  "mensagem": "Homologação agendada com sucesso!",
  "detalhes": [
    "Tag adicionada no Zoho",
    "Campo data_de_homologacao atualizado",
    "Implantador RIS 'usuario.ris@animati.com.br' adicionado ao projeto",
    "Implantador PACS 'usuario.pacs@animati.com.br' adicionado ao projeto",
    "7 tarefas de homologação RIS atribuídas",
    "6 tarefas de homologação PACS atribuídas",
    "Planilha atualizada: Status='Em Homologação', Dt Homolog='15/11/2025'"
  ]
}
```

---

## 🔄 Fluxo de Execução

```
Frontend: Modal "Agendar Homologação"
    ↓ [Usuário preenche data e seleciona implantadores]
    ↓
POST /api/agendar_homologacao
{
  project_id,
  data_homologacao,
  implantador_ris?,
  implantador_pacs?
}
    ↓
┌─────────────────────────────────────────────────────┐
│ 1. Mover para "Em Homologação"                      │
│    - Atualizar status no Zoho                       │
│    - Remover tag "Em Andamento - Implantação"       │
│    - Adicionar tag "Em Homologação"                 │
│    - Preencher campo data_de_homologacao (Zoho)     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 2. Adicionar Implantadores ao Projeto              │
│    - adicionar_usuario_projeto(implantador_ris)     │
│    - adicionar_usuario_projeto(implantador_pacs)    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 3. Atribuir Tarefas de Homologação                 │
│    - Carregar tarefas_homologacao_ris.json          │
│    - atribuir_tarefa_por_nome() para cada tarefa    │
│    - Carregar tarefas_homologacao_pacs.json         │
│    - atribuir_tarefa_por_nome() para cada tarefa    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 4. Atualizar Planilha Principal                    │
│    - Coluna "Status Principal" = "Em Homologação"   │
│    - Coluna "Dt Homolog" = data informada (DD/MM)   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 5. Sincronizar Banco de Dados Local                │
│    - synchronize_single_project()                   │
│    - Atualizar cache com novos dados                │
└─────────────────────────────────────────────────────┘
    ↓
Retornar sucesso com detalhes das operações
```

---

## 📋 Implementação do Frontend

### Modal HTML (sugestão)

```html
<div id="modalAgendarHomologacao" class="modal">
  <div class="modal-content">
    <span class="close">&times;</span>
    <h2>Agendar Homologação</h2>
    
    <form id="formAgendarHomologacao">
      <input type="hidden" id="project_id_homolog" name="project_id">
      
      <div class="form-group">
        <label for="data_homologacao">Data de Homologação *</label>
        <input type="date" id="data_homologacao" name="data_homologacao" required>
      </div>
      
      <div class="form-group">
        <label for="implantador_ris_homolog">Implantador RIS</label>
        <select id="implantador_ris_homolog" name="implantador_ris">
          <option value="">Selecione...</option>
          <!-- Carregar dinamicamente da equipe_implantacao_classificada.json -->
        </select>
      </div>
      
      <div class="form-group">
        <label for="implantador_pacs_homolog">Implantador PACS</label>
        <select id="implantador_pacs_homolog" name="implantador_pacs">
          <option value="">Selecione...</option>
          <!-- Carregar dinamicamente da equipe_implantacao_classificada.json -->
        </select>
      </div>
      
      <div class="form-actions">
        <button type="button" class="btn-cancelar">Cancelar</button>
        <button type="submit" class="btn-agendar">Agendar Homologação</button>
      </div>
    </form>
  </div>
</div>
```

### JavaScript (sugestão)

```javascript
// Abrir modal ao clicar em "Agendar Homologação" no card
function abrirModalAgendarHomologacao(projectId, nomeProjeto) {
  document.getElementById('project_id_homolog').value = projectId;
  document.getElementById('modalAgendarHomologacao').style.display = 'block';
  
  // Carregar implantadores
  carregarImplantadoresHomologacao();
}

// Carregar lista de implantadores
async function carregarImplantadoresHomologacao() {
  try {
    const response = await fetch('/api/equipe_implantacao');
    const equipe = await response.json();
    
    const selectRIS = document.getElementById('implantador_ris_homolog');
    const selectPACS = document.getElementById('implantador_pacs_homolog');
    
    // Popular selects com a equipe
    equipe.RIS.forEach(implantador => {
      const option = document.createElement('option');
      option.value = implantador.email;
      option.textContent = implantador.nome;
      selectRIS.appendChild(option);
    });
    
    equipe.PACS.forEach(implantador => {
      const option = document.createElement('option');
      option.value = implantador.email;
      option.textContent = implantador.nome;
      selectPACS.appendChild(option);
    });
  } catch (error) {
    console.error('Erro ao carregar implantadores:', error);
  }
}

// Enviar formulário
document.getElementById('formAgendarHomologacao').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const payload = {
    project_id: formData.get('project_id'),
    data_homologacao: formData.get('data_homologacao'),
    implantador_ris: formData.get('implantador_ris'),
    implantador_pacs: formData.get('implantador_pacs')
  };
  
  try {
    const response = await fetch('/api/agendar_homologacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.sucesso) {
      alert('Homologação agendada com sucesso!');
      document.getElementById('modalAgendarHomologacao').style.display = 'none';
      
      // Recarregar página ou atualizar card
      location.reload();
    } else {
      alert('Erro: ' + result.erro);
    }
  } catch (error) {
    alert('Erro ao agendar homologação: ' + error);
  }
});
```

---

## 🎨 Integração com o Kanban

### Onde Adicionar o Botão

No card do projeto, quando estiver na coluna **"Em Andamento - Implantação"**, adicionar botão:

```html
<button class="btn-agendar-homologacao" onclick="abrirModalAgendarHomologacao('${projectId}', '${projectName}')">
  📅 Agendar Homologação
</button>
```

### Estilo do Botão (sugestão)

```css
.btn-agendar-homologacao {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
  width: 100%;
}

.btn-agendar-homologacao:hover {
  background-color: #45a049;
}
```

---

## 🔍 Validações

O endpoint realiza as seguintes validações:

1. ✅ Usuário autenticado
2. ✅ `project_id` obrigatório
3. ✅ `data_homologacao` obrigatória (formato YYYY-MM-DD)
4. ✅ Projeto existe no banco de dados
5. ⚠️ Implantadores são opcionais (RIS e/ou PACS)

---

## 📊 Campos Atualizados

### Zoho Projects
- Status → "Em Homologação"
- Tag → Adiciona "Em Homologação", Remove "Em Andamento - Implantação"
- Campo customizado `data_de_homologacao` → Data informada (YYYY-MM-DD)
- Membros do projeto → Adiciona implantadores selecionados
- Tarefas → Atribui tarefas de homologação aos implantadores

### Google Sheets (Planilha Principal)
- Coluna "Status Principal" → "Em Homologação"
- Coluna "Dt Homolog" → Data informada (DD/MM/YYYY)

### Banco de Dados Local
- `status_atual` → "Em Homologação"
- `data_mudanca_status` → Data atual
- `data_homologacao` → Data informada
- `full_data_json` → Atualizado com dados do Zoho

---

## 🧪 Testes

### Teste Manual

1. **Pré-condições**:
   - Projeto em "Em Andamento - Implantação"
   - Implantadores cadastrados no sistema
   - Tarefas de homologação existem no Zoho Projects

2. **Passos**:
   - Abrir modal "Agendar Homologação"
   - Selecionar data futura
   - Selecionar implantador RIS
   - Selecionar implantador PACS
   - Clicar em "Agendar Homologação"

3. **Resultados Esperados**:
   - Projeto movido para "Em Homologação"
   - Implantadores adicionados ao projeto no Zoho
   - Tarefas RIS atribuídas ao implantador RIS
   - Tarefas PACS atribuídas ao implantador PACS
   - Planilha atualizada com status e data
   - Mensagem de sucesso exibida

---

## 🔗 Dependências

### Funções Utilizadas

- `utils.obter_access_token()` - Obtém token de acesso do Zoho
- `utils.carregar_mapeamento_colunas()` - Carrega configuração de colunas
- `utils.adicionar_usuario_projeto()` - Adiciona usuário ao projeto
- `utils.atribuir_tarefa_por_nome()` - Atribui tarefa a um usuário
- `utils.extrair_cliente_planilha()` - Extrai nome do cliente
- `utils.update_col_value_by_cliente_tolerant()` - Atualiza valor na planilha
- `utils.build_google_credentials_from_session()` - Credenciais Google
- `_atualizar_zoho()` - Atualiza projeto no Zoho
- `_sincronizar_db_local_forcado()` - Sincroniza banco local

### Arquivos de Configuração

- `tarefas_homologacao_ris.json` - Lista de tarefas RIS
- `tarefas_homologacao_pacs.json` - Lista de tarefas PACS
- `mapeamento_colunas.json` - Configuração da coluna "Em Homologação"
- `equipe_implantacao_classificada.json` - Lista de implantadores

---

## 🚀 Próximos Passos

### Frontend
- [ ] Criar modal HTML
- [ ] Implementar JavaScript para abrir/fechar modal
- [ ] Carregar lista de implantadores dinamicamente
- [ ] Validar data (não permitir datas passadas)
- [ ] Adicionar botão "Agendar Homologação" no card
- [ ] Exibir mensagens de sucesso/erro
- [ ] Atualizar card após agendamento

### Backend
- [x] Endpoint `/api/agendar_homologacao` criado
- [x] Arquivos de tarefas de homologação criados
- [ ] Testar atribuição de tarefas
- [ ] Validar se tarefas existem no projeto
- [ ] Adicionar logs detalhados

### Melhorias Futuras
- [ ] Notificar implantadores por email
- [ ] Criar evento no Google Calendar
- [ ] Validar se projeto está em fase adequada
- [ ] Dashboard de homologações agendadas
- [ ] Histórico de homologações

---

## 📝 Observações

- A data de homologação é informada pelo usuário (não calculada automaticamente)
- Implantadores são opcionais - pode agendar sem selecionar
- Se tarefa não existir no projeto, será registrado warning mas não falha
- Atribuição funciona apenas para tarefas já criadas no projeto
- Sistema atualiza tanto Zoho quanto planilha em uma única operação

---

**Arquivos Modificados**:
- `routes/api.py` - Novo endpoint `agendar_homologacao()`
- Adicionado `import copy`

**Arquivos Criados**:
- `tarefas_homologacao_ris.json`
- `tarefas_homologacao_pacs.json`
- `FEATURE_AGENDAR_HOMOLOGACAO.md` (este arquivo)
