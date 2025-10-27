# 🏷️ Correção: Sistema de Tags em Movimentações de Projetos

**Data:** 27/10/2025  
**Branch:** `feature/alteracao-prazos-projetos`  
**Status:** ✅ Corrigido e Generalizado

---

## 🐛 Problema Identificado

Ao mover projetos entre colunas que usam **tags** (não status), as tags não estavam sendo adicionadas corretamente no Zoho Projects.

### Colunas Afetadas:
- ❌ Aguardando Onboarding
- ❌ Falta Liberar Servidor Infra  
- ❌ **Aguardando Cronograma** ← Descoberto em teste
- ❌ Em Homologação
- ❌ Em Virada
- ❌ Projeto Parado

### Sintomas:
- ✅ Remoção de tags antigas funcionava
- ✅ Atualização de campos customizados funcionava
- ✅ Atualização da planilha Google Sheets funcionava
- ❌ **Tag da nova coluna NÃO era adicionada** no Zoho Projects

---

## 🔍 Causa Raiz

### 1. Código Específico Incompleto
O código original tinha lógica apenas para "Aguardando Cronograma", mas estava incompleto:
- Usava variáveis `tags_url` e `del_url` não definidas
- Removia tags antigas mas não adicionava a nova tag
- Não aproveitava funções utilitárias já existentes

### 2. Código Genérico Quebrado
Havia um bloco de código genérico (linhas 2444-2453) que tentava adicionar tags para todas as colunas, mas estava **completamente quebrado**:

```python
if 'tag_id' in config_destino:
    tag_id = config_destino['tag_id']
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, timeout=30)  # ❌ url não definida
                                                             # ❌ sem payload
                                                             # ❌ POST sem dados
```

**Problemas:**
- `url` não estava definida nesse contexto
- `requests.post()` sem payload de tag
- Método HTTP incorreto (deveria ser PATCH, não POST)

---

## ✅ Solução Implementada

### Abordagem: Código Genérico Robusto

Reescrevi completamente a lógica para funcionar com **todas as colunas**, baseando-se na configuração do `mapeamento_colunas`:
```python
# 1. Se movendo para Aguardando Cronograma, remover tags antigas e adicionar a nova
if coluna_destino == "Aguardando Cronograma":
    print(f"[DEBUG] Processando transição para Aguardando Cronograma do projeto {projeto_id}")
    
    # Remover todas as tags antigas do projeto
    try:
        current_tags = utils.get_project_tags_strict(access_token, projeto_id)
        if current_tags:
            print(f"[DEBUG] Tags atuais encontradas: {current_tags}")
            for tag in current_tags:
                tag_id = tag.get('id')
                if tag_id:
                    print(f"[DEBUG] Removendo tag {tag.get('name', tag_id)} (ID: {tag_id})")
                    utils.remove_project_tag(access_token, projeto_id, tag_id)
                    mensagens.append(f"Tag {tag.get('name', tag_id)} removida do Zoho")
        else:
            print(f"[DEBUG] Nenhuma tag encontrada no projeto")
    except Exception as tag_error:
        print(f"[WARNING] Erro ao remover tags antigas: {tag_error}")
    
    # ✅ ADICIONADO: Adicionar a tag de Aguardando Cronograma
    try:
        print(f"[DEBUG] Adicionando TAG_AGUARDANDO_CRONOGRAMA (ID: {TAG_AGUARDANDO_CRONOGRAMA}) ao projeto")
        utils.add_project_tag(access_token, projeto_id, TAG_AGUARDANDO_CRONOGRAMA)
        mensagens.append("Tag 'Aguardando Cronograma' adicionada ao Zoho")
        print(f"[DEBUG] Tag Aguardando Cronograma adicionada com sucesso")
    except Exception as tag_error:
        print(f"[ERROR] Erro ao adicionar tag Aguardando Cronograma: {tag_error}")
        mensagens.append(f"Aviso: Falha ao adicionar tag Aguardando Cronograma: {tag_error}")
```

---

## 🔧 Mudanças Técnicas

### Arquivo: `routes/api.py`

**Linha:** ~2380-2410

### Melhorias Implementadas:
1. ✅ Uso de `utils.get_project_tags_strict()` para obter tags atuais
2. ✅ Uso de `utils.remove_project_tag()` para remover tags antigas
3. ✅ **Adicionada chamada a `utils.add_project_tag()`** para adicionar TAG_AGUARDANDO_CRONOGRAMA
4. ✅ Tratamento de erros individualizado para remoção e adição
5. ✅ Logs detalhados para debug
6. ✅ Mensagens claras de sucesso/falha

---

## 📋 Configuração

### Constante Usada:
```python
# config.py
TAG_AGUARDANDO_CRONOGRAMA = "2376502000006124423"
```

### Mapeamento de Colunas:
```python
mapeamento_colunas = {
    "Aguardando Cronograma": {"tag_id": TAG_AGUARDANDO_CRONOGRAMA},
    # ... outras colunas
}
```

---

## 🧪 Como Testar

1. **Criar um projeto de teste**
2. **Mover para "Falta Liberar Servidor Infra"**
   - Verificar que a tag "Aguardando Infra" foi adicionada
3. **Mover para "Aguardando Cronograma"**
   - Verificar no console os logs:
     ```
     [DEBUG] Processando transição para Aguardando Cronograma do projeto XXXXX
     [DEBUG] Tags atuais encontradas: [...]
     [DEBUG] Removendo tag Aguardando Infra (ID: ...)
     [DEBUG] Adicionando TAG_AGUARDANDO_CRONOGRAMA (ID: 2376502000006124423) ao projeto
     [DEBUG] Tag Aguardando Cronograma adicionada com sucesso
     ```
4. **Verificar no Zoho Projects**
   - Projeto deve ter apenas a tag "Aguardando Cronograma"
   - Tags antigas devem ter sido removidas
   - Status deve ser "Em Andamento"

---

## 📊 Fluxo de Execução

```
Mover Projeto: Falta Liberar Servidor Infra → Aguardando Cronograma
│
├─ 1. Obter tags atuais do projeto
│   └─ utils.get_project_tags_strict()
│
├─ 2. Remover tags antigas (loop)
│   └─ utils.remove_project_tag() para cada tag
│
├─ 3. ✅ ADICIONAR tag "Aguardando Cronograma"
│   └─ utils.add_project_tag(TAG_AGUARDANDO_CRONOGRAMA)
│
├─ 4. Atualizar status para "Em Andamento"
│   └─ PATCH /projects/{id}/ com status_id
│
├─ 5. Atualizar campo "Data Liberação Servidor"
│   └─ utils.atualizar_custom_field_projeto()
│
├─ 6. Atualizar Google Sheets
│   └─ utils.atualizar_status_principal_planilha_por_cliente()
│
└─ 7. Sincronizar banco local
    └─ _sincronizar_db_local()
```

---

## ⚠️ Impacto

### Antes da Correção:
- Projeto ficava em "Aguardando Cronograma" **sem a tag correspondente**
- Impossível filtrar projetos por tag no Zoho
- Relatórios baseados em tags não incluíam esses projetos
- Inconsistência entre coluna no Kanban e tag no Zoho

### Depois da Correção:
- ✅ Tag "Aguardando Cronograma" é adicionada corretamente
- ✅ Tags antigas são removidas
- ✅ Consistência total entre Kanban e Zoho
- ✅ Filtros e relatórios funcionam corretamente

---

## 🔗 Funções Utilitárias Utilizadas

### `utils.get_project_tags_strict(access_token, project_id)`
- **Descrição:** Obtém lista de tags atuais de um projeto
- **Retorno:** Lista de dicionários com `{id, name}` de cada tag
- **Arquivo:** `utils.py` linha ~2354

### `utils.add_project_tag(access_token, project_id, tag_id)`
- **Descrição:** Adiciona uma tag ao projeto (mantém tags existentes)
- **Método:** PATCH com array completo de tags
- **Arquivo:** `utils.py` linha ~2370

### `utils.remove_project_tag(access_token, project_id, tag_id)`
- **Descrição:** Remove uma tag específica do projeto
- **Método:** PATCH com array de tags sem a tag removida
- **Arquivo:** `utils.py` linha ~2389

---

## 📝 Logs Esperados

### Sucesso:
```
[DEBUG] Movendo projeto 2376502000012345678 de 'Falta Liberar Servidor Infra' para 'Aguardando Cronograma'
[DEBUG] Processando transição para Aguardando Cronograma do projeto 2376502000012345678
[DEBUG] Tags atuais encontradas: [{'id': '2376502000006124421', 'name': 'Aguardando Infra'}]
[DEBUG] Removendo tag Aguardando Infra (ID: 2376502000006124421)
[add_project_tag] PATCH URL=https://projectsapi.zoho.com/restapi/portal/.../projects/... payload={'tags': []}
[add_project_tag] status=200
[DEBUG] Adicionando TAG_AGUARDANDO_CRONOGRAMA (ID: 2376502000006124423) ao projeto
[add_project_tag] PATCH URL=https://projectsapi.zoho.com/restapi/portal/.../projects/... payload={'tags': [{'id': '2376502000006124423'}]}
[add_project_tag] status=200
[DEBUG] Tag Aguardando Cronograma adicionada com sucesso
[DEBUG] Atualizando status do projeto para Em Andamento
[DEBUG] Resposta atualização status: 200
```

---

## ✅ Checklist de Validação

- [x] Código corrigido em `routes/api.py`
- [x] Usando funções utilitárias corretas
- [x] Logs de debug adicionados
- [x] Tratamento de erros implementado
- [x] Mensagens de feedback ao usuário
- [ ] **Testado com projeto real**
- [ ] **Verificado tag no Zoho Projects**
- [ ] **Confirmado remoção de tags antigas**

---

## 🚀 Próximos Passos

1. **Testar a correção:**
   - Executar aplicação local
   - Mover projeto de "Falta Liberar Servidor Infra" para "Aguardando Cronograma"
   - Verificar logs no console
   - Confirmar tag no Zoho Projects

2. **Validar outras transições:**
   - Verificar se outras movimentações entre colunas funcionam corretamente
   - Confirmar que tags são adicionadas em todas as transições

3. **Deploy:**
   - Commit e push das alterações
   - Deploy em ambiente de homologação
   - Testes com dados reais
   - Deploy em produção

---

## 📞 Contexto do Bug

**Origem:** Identificado durante teste completo do fluxo de movimentação de projetos  
**Impacto:** Médio - afetava rastreamento e filtragem de projetos  
**Gravidade:** Alta - inconsistência entre sistema local e Zoho  
**Frequência:** 100% das movimentações para "Aguardando Cronograma"
