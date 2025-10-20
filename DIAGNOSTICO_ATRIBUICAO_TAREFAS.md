# 🐛 Problema: Tarefas não sendo atribuídas aos implantadores

## ❌ Sintoma

Ao clicar em "Agendar Implantação":
- ✅ Implantadores são adicionados ao projeto com sucesso
- ❌ Tarefas NÃO são atribuídas aos implantadores

## 🔍 Causa Raiz Identificada

### Diferença entre API REST e V3

**Na criação do projeto (api.py linha ~390)** - Funciona apenas para GP:
```python
url_rest = f".../tasks/{task_id}/"
payload_rest = {"person_responsible": str(gp_zpuid)}  # ❌ Campo SINGULAR
```

**No ImplantacaoManager (funciona para implantadores)**:
```python
url = f".../tasks/{task_id}/"
payload = {"owners": owners_str}  # ✅ Campo PLURAL
```

### Por que isso importa?

| Campo | API | Uso | Limitação |
|-------|-----|-----|-----------|
| `person_responsible` | REST | Atribuir **1 pessoa responsável** | ❌ Apenas 1 usuário |
| `owners` | REST | Atribuir **múltiplos colaboradores** | ✅ Múltiplos usuários |

**Problema**: O código de "Agendar Implantação" em `routes/api.py` está usando `person_responsible`, que é limitado a **1 pessoa apenas**.

---

## ✅ Solução: Usar o campo `owners`

### Código Atual (❌ Errado) - `routes/api.py` linha ~1880-1895

```python
# Adicionar implantador ao projeto
sucesso_adicao = adicionar_implantador_e_atribuir_tarefas(
    project_id=project_id,
    nome_implantador=implantador_ris,
    tipo_projeto='RIS',
    access_token=access_token,
    portal_id=ZOHO_PORTAL_ID
)
```

### Análise do Fluxo

1. ✅ `adicionar_implantador_e_atribuir_tarefas()` é chamada
2. ✅ Implantador é adicionado ao projeto
3. ✅ `ImplantacaoManager.atribuir_tarefa()` é chamada
4. ✅ Usa o campo `owners` correto
5. ❓ **Mas por que não funciona?**

---

## 🔍 Investigação Profunda

Vou verificar se o problema está na forma como os ZPUIDs estão sendo passados ou se há algum outro erro silencioso.

### Possíveis Causas:

1. **ZPUID incorreto**: O nome do implantador não corresponde ao usuário na equipe
2. **Tarefas não encontradas**: As tarefas do template não materializaram ainda
3. **Permissões**: O implantador não tem permissão para ser atribuído
4. **Timeout**: A API está demorando demais

---

## 🧪 Teste de Diagnóstico

Vamos adicionar logs detalhados para identificar onde está falhando:

### Arquivo: `implantacao_manager.py` (adicionar mais logs)

```python
def atribuir_tarefa(
    self, 
    project_id: str, 
    task_id: str, 
    user_ids: List[str]
) -> Tuple[bool, Optional[str]]:
    """Atribui uma tarefa para um ou mais usuários"""
    url = f"{self.base_url}/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
    
    # Converter lista de IDs em string separada por vírgula
    owners_str = ",".join(user_ids)
    
    payload = {
        "owners": owners_str
    }
    
    # ✅ LOG DETALHADO
    print(f"[DEBUG][ATRIBUIR_TAREFA] URL: {url}")
    print(f"[DEBUG][ATRIBUIR_TAREFA] Payload: {payload}")
    print(f"[DEBUG][ATRIBUIR_TAREFA] User IDs: {user_ids}")
    
    try:
        response = requests.post(url, headers=self.headers, data=payload, timeout=30)
        
        # ✅ LOG DA RESPOSTA
        print(f"[DEBUG][ATRIBUIR_TAREFA] Status: {response.status_code}")
        print(f"[DEBUG][ATRIBUIR_TAREFA] Resposta: {response.text[:500]}")
        
        if response.status_code == 200:
            logger.info(f"✅ Tarefa {task_id} atribuída para {len(user_ids)} usuário(s)")
            return True, None
        else:
            error_msg = f"Status {response.status_code}: {response.text}"
            logger.error(f"❌ Erro ao atribuir tarefa {task_id}: {error_msg}")
            return False, error_msg
                
    except Exception as e:
        error_msg = f"Exceção: {str(e)}"
        logger.error(f"❌ Erro ao atribuir tarefa {task_id}: {error_msg}")
        traceback.print_exc()  # ✅ Adicionar stack trace
        return False, error_msg
```

---

## 🔧 Correções Sugeridas

### 1. Adicionar logs detalhados em `adicionar_implantador_e_atribuir_tarefas`

```python
def adicionar_implantador_e_atribuir_tarefas(
    project_id: str,
    nome_implantador: str,
    tipo_projeto: str,
    access_token: str,
    portal_id: str = "868230290"
) -> Dict:
    """Adiciona UM implantador específico ao projeto e atribui tarefas"""
    
    resultado = {
        "sucesso": False,
        "usuario_adicionado": None,
        "tarefas_atribuidas": [],
        "tarefas_nao_encontradas": [],
        "tarefas_falharam": [],
        "mensagem": ""
    }
    
    try:
        manager = ImplantacaoManager(portal_id, access_token)
        
        # ✅ LOG: Início do processo
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Projeto: {project_id}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Nome: {nome_implantador}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Tipo: {tipo_projeto}")
        
        # 1. Carregar equipe de implantação
        equipe = manager.carregar_equipe_implantacao()
        chave_equipe = f"Implantação {tipo_projeto}"
        
        # ✅ LOG: Equipe carregada
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Equipe '{chave_equipe}': {len(equipe.get(chave_equipe, []))} membros")
        
        if chave_equipe not in equipe:
            resultado["mensagem"] = f"Tipo de projeto inválido: {tipo_projeto}"
            return resultado
        
        implantadores = equipe[chave_equipe]
        
        # 2. Encontrar o implantador pelo nome
        implantador_encontrado = None
        nome_normalizado = manager.normalizar_nome_tarefa(nome_implantador)
        
        # ✅ LOG: Busca do implantador
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Buscando: '{nome_normalizado}'")
        
        for implantador in implantadores:
            nome_impl_normalizado = manager.normalizar_nome_tarefa(implantador.get('name', ''))
            
            # Match exato ou parcial
            if nome_normalizado in nome_impl_normalizado or nome_impl_normalizado in nome_normalizado:
                implantador_encontrado = implantador
                print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Encontrado: {implantador.get('name')}")
                break
        
        if not implantador_encontrado:
            # ✅ LOG: Lista de implantadores disponíveis
            nomes_disponiveis = [imp.get('name') for imp in implantadores]
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ❌ Não encontrado!")
            print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Disponíveis: {nomes_disponiveis}")
            
            resultado["mensagem"] = f"Implantador '{nome_implantador}' não encontrado na equipe {tipo_projeto}"
            logger.warning(f"Implantador não encontrado: {nome_implantador}")
            return resultado
        
        email = implantador_encontrado.get('email')
        zpuid = implantador_encontrado.get('zpuid')
        nome = implantador_encontrado.get('name')
        
        # ✅ LOG: Dados do implantador
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] Email: {email}")
        print(f"[DEBUG][ADICIONAR_IMPLANTADOR] ZPUID: {zpuid}")
        
        # ... resto do código
```

---

## 🎯 Checklist de Validação

Execute o teste com os logs adicionados e verifique:

### 1. Implantador é encontrado?
```
[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Encontrado: Marcello Roza de Souza
[DEBUG][ADICIONAR_IMPLANTADOR] Email: marcello@animati.com.br
[DEBUG][ADICIONAR_IMPLANTADOR] ZPUID: 123456789
```

### 2. Tarefas são encontradas?
```
[DEBUG][ADICIONAR_IMPLANTADOR] 📋 31 tarefas para atribuir
[DEBUG][ADICIONAR_IMPLANTADOR] ✅ Tarefa encontrada: 'AP-01 - Tarefa de exemplo'
```

### 3. Atribuição está funcionando?
```
[DEBUG][ATRIBUIR_TAREFA] URL: https://projectsapi.zoho.com/restapi/portal/.../tasks/123456/
[DEBUG][ATRIBUIR_TAREFA] Payload: {'owners': '123456789'}
[DEBUG][ATRIBUIR_TAREFA] Status: 200
✅ Tarefa 123456 atribuída para 1 usuário(s)
```

---

## 📊 Comparação: Criação vs Implantação

| Aspecto | Criação do Projeto | Agendar Implantação |
|---------|-------------------|---------------------|
| **API** | REST v1 | REST v1 |
| **Campo** | `person_responsible` | `owners` |
| **Usuários** | 1 (GP) | 1-N (Implantadores) |
| **Funciona?** | ✅ Sim | ❌ Não (investigar) |

---

## 🚀 Próximos Passos

1. **Adicionar logs detalhados** no código conforme sugerido acima
2. **Executar teste** com "Agendar Implantação"
3. **Analisar logs** para identificar onde está falhando:
   - Implantador não encontrado?
   - Tarefas não encontradas?
   - API retornando erro?
4. **Corrigir problema específico** baseado nos logs

---

**Data**: 19/10/2025  
**Status**: 🔍 Investigação em andamento  
**Ação necessária**: Adicionar logs e executar teste
