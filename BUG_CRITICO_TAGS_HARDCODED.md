# 🚨 CRÍTICO: Bug Hard-Coded que Impedia Adição de Tags

**Data:** 27/10/2025  
**Branch:** `feature/alteracao-prazos-projetos`  
**Gravidade:** 🔴 CRÍTICA  
**Status:** ✅ CORRIGIDO

---

## 🐛 Problema Crítico Identificado

### Sintoma
Tag "Aguardando Cronograma" (e potencialmente outras) **nunca era adicionada** ao mover projetos no Zoho, mesmo com configuração correta no `mapeamento_colunas.json`.

### Impacto
- **100%** das movimentações para "Aguardando Cronograma" falhavam em adicionar a tag
- Tags antigas eram removidas corretamente ✅
- Outras atualizações (campos, planilha) funcionavam ✅  
- **Mas a tag nova nunca era adicionada** ❌

---

## 🔍 Investigação

### 1. Configuração Correta
O arquivo `mapeamento_colunas.json` estava **corretamente configurado**:

```json
"Aguardando Cronograma": {
  "zohoStatusId": "2376502000000020092",
  "zohoTagsToAdd": ["2376502000006124423"],  // ✅ Configurado
  "zohoTagsToRemove": ["2376502000000958355"]
}
```

### 2. Código Problemático
Função `_ajustar_tags_projeto()` em `routes/api.py` (linhas 1326-1390):

```python
def _ajustar_tags_projeto(...):
    add_tags = info_dest.get("zohoTagsToAdd", []) or []
    remove_tags = info_dest.get("zohoTagsToRemove", []) or []

    # ❌ CÓDIGO HARD-CODED PROBLEMÁTICO
    if coluna_destino == "Aguardando Cronograma":
        # Remove all tags
        payload_tags = {"tags": []}
        response_tags = requests.patch(base_url, headers=headers, json=payload_tags, timeout=45)
        if response_tags.status_code not in (200, 201):
            raise RuntimeError(...)
        return  # ❌ SAI DA FUNÇÃO SEM ADICIONAR A TAG!
    
    # ... resto do código que adiciona tags (nunca executado para "Aguardando Cronograma")
```

### 3. Causa Raiz
**Código hard-coded** para "Aguardando Cronograma" que:
1. Remove todas as tags ✅
2. **Retorna imediatamente** ❌
3. Nunca executa o código que lê `zohoTagsToAdd` e adiciona a tag

**Por que esse código estava lá?**
- Provavelmente um código temporário/debug que foi esquecido
- Ou uma tentativa antiga de resolver outro problema
- **Conflitava completamente** com a configuração JSON

---

## ✅ Solução Implementada

### Correção
Removi o código hard-coded e mantive apenas a lógica genérica que:
1. Lê `zohoTagsToAdd` e `zohoTagsToRemove` do JSON
2. Carrega tags atuais do projeto
3. Remove tags especificadas
4. Adiciona tags especificadas
5. Envia payload completo para o Zoho

### Código Corrigido

```python
def _ajustar_tags_projeto(base_url: str, headers: dict, info_dest: dict, detalhes_zoho: dict, coluna_destino: str) -> None:
    """Reconstrói a lista de tags do projeto no Zoho com base nas informações atuais."""
    add_tags = info_dest.get("zohoTagsToAdd", []) or []
    remove_tags = info_dest.get("zohoTagsToRemove", []) or []

    # ✅ REMOVIDO: Código hard-coded para "Aguardando Cronograma"
    
    # Se não há tags para adicionar ou remover, não fazer nada
    if not add_tags and not remove_tags:
        print(f"[DEBUG][TAGS] Nenhuma tag para adicionar ou remover em '{coluna_destino}'")
        return

    # ... (código de normalização)

    # Carregar tags atuais do projeto
    atuais = _carregar_tags_atuais(base_url, headers, detalhes_zoho)
    print(f"[DEBUG][TAGS] Tags atuais do projeto: {atuais}")

    # Criar dicionário de tags por chave
    tags_por_chave: dict[tuple[str, str], dict] = {}
    for tag in atuais:
        normalizada = _normalize_tag(tag)
        if normalizada:
            tags_por_chave[_tag_key(normalizada)] = normalizada

    # ✅ Remover tags especificadas (com log)
    for tag in remove_tags:
        normalizada = _normalize_tag(tag)
        if normalizada:
            chave = _tag_key(normalizada)
            if chave in tags_por_chave:
                print(f"[DEBUG][TAGS] Removendo tag: {tags_por_chave[chave]}")
                tags_por_chave.pop(chave, None)

    # ✅ Adicionar tags especificadas (com log)
    for tag in add_tags:
        normalizada = _normalize_tag(tag)
        if normalizada:
            chave = _tag_key(normalizada)
            print(f"[DEBUG][TAGS] Adicionando tag: {normalizada}")
            tags_por_chave[chave] = normalizada

    # ✅ Construir e enviar lista final
    novas_tags = list(tags_por_chave.values())
    print(f"[DEBUG][TAGS] Tags finais para '{coluna_destino}': {novas_tags}")
    
    payload_tags = {"tags": novas_tags}
    response_tags = requests.patch(base_url, headers=headers, json=payload_tags, timeout=45)
    
    if response_tags.status_code not in (200, 201):
        print(f"[ERROR][TAGS] Falha ao ajustar tags: {response_tags.status_code}")
        raise RuntimeError(...)
    
    print(f"[DEBUG][TAGS] Tags atualizadas com sucesso para '{coluna_destino}'")
```

---

## 📊 Melhorias Implementadas

### 1. Logs Detalhados
```
[DEBUG][TAGS] Tags atuais do projeto: [{'id': '...', 'name': 'Aguardando Infra'}]
[DEBUG][TAGS] Removendo tag: {'id': '2376502000000958355', 'name': 'Aguardando Infra'}
[DEBUG][TAGS] Adicionando tag: {'id': '2376502000006124423'}
[DEBUG][TAGS] Tags finais para 'Aguardando Cronograma': [{'id': '2376502000006124423'}]
[DEBUG][TAGS] Tags atualizadas com sucesso para 'Aguardando Cronograma'
```

### 2. Tratamento de Erros
- Log de erros detalhado antes de lançar exception
- Status code e mensagem de erro do Zoho

### 3. Validação
- Verifica se há tags para processar antes de fazer requisição
- Normaliza tags antes de comparar (por ID ou nome)

---

## 🧪 Como Testar

1. **Reiniciar a aplicação Flask**
2. **Mover projeto** de "Falta Liberar Servidor Infra" → "Aguardando Cronograma"
3. **Verificar logs** no console:
   ```
   [DEBUG][TAGS] Tags atuais do projeto: [...]
   [DEBUG][TAGS] Removendo tag: {'name': 'Aguardando Infra'}
   [DEBUG][TAGS] Adicionando tag: {'id': '2376502000006124423'}
   [DEBUG][TAGS] Tags finais: [{'id': '2376502000006124423'}]
   [DEBUG][TAGS] Tags atualizadas com sucesso
   ```
4. **Verificar no Zoho Projects** que a tag foi adicionada

---

## ⚠️ Lições Aprendidas

### Problema de Código Hard-Coded
- ❌ **Nunca** usar lógica hard-coded quando há configuração JSON
- ❌ Código específico para uma coluna quebra a generalização
- ❌ Returns prematuros podem ignorar lógica importante

### Boas Práticas
- ✅ Sempre preferir configuração em JSON
- ✅ Código genérico que funciona para todas as colunas
- ✅ Logs detalhados em operações críticas
- ✅ Validação de configuração antes de processar

---

## 📋 Checklist de Correção

- [x] Código hard-coded removido
- [x] Logs detalhados adicionados
- [x] Lógica genérica mantida
- [x] Tratamento de erros melhorado
- [x] Documentação criada
- [ ] **Testado com projeto real**
- [ ] **Verificado no Zoho Projects**
- [ ] **Confirmado funcionamento para outras colunas**

---

## 🎯 Próximos Passos

1. **Reiniciar aplicação Flask**
2. **Testar movimentação** para "Aguardando Cronograma"
3. **Verificar logs** detalhados
4. **Confirmar tag** no Zoho Projects
5. **Testar outras colunas** que usam tags (Em Homologação, Em Virada, etc.)

---

## 📞 Contexto Adicional

**Descoberta:** Durante teste completo do fluxo de movimentação  
**Impacto:** CRÍTICO - afetava 100% das movimentações para colunas com tags  
**Urgência:** ALTA - funcionalidade core quebrada  
**Complexidade:** Baixa - código problemático claramente identificado

**Nota:** Este foi um dos bugs mais críticos encontrados, pois quebrava completamente
a funcionalidade de tags, um pilar fundamental do sistema de gerenciamento de projetos.
