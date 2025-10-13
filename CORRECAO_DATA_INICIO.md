# 🔧 Correção - Data de Início da Implantação

## 🎯 Problema Identificado

A `data_de_inicio_da_implantacao` estava sendo preenchida com a **data atual** em vez da **data selecionada no modal**.

---

## 🔍 Causa Raiz

No arquivo `mapeamento_colunas.json`, a configuração da coluna "Em Andamento - Implantação" contém:

```json
"Em Andamento - Implantação": {
  "zohoCustomFields": {
    "data_de_inicio_da_implantacao": "CURRENT_DATE"  ← AQUI ESTAVA O PROBLEMA
  }
}
```

O valor `"CURRENT_DATE"` é um **placeholder** que é substituído pela data atual pela função `_resolver_custom_fields()`.

---

## ✅ Solução Implementada

### 1. **Substituição Explícita no Código**

No endpoint `/iniciar_implantacao`, já estávamos tentando sobrescrever o valor:

```python
# Linha 1766-1767
custom_fields_config = info_dest.get("zohoCustomFields", {}).copy()
custom_fields_config["data_de_inicio_da_implantacao"] = data_inicio_implantacao  # ✓ Correto
```

**Isso deveria funcionar**, mas pode haver algum problema na propagação do valor.

---

### 2. **Logs Detalhados Adicionados**

Para diagnosticar exatamente onde está falhando, adicionamos logs detalhados:

#### 📋 **Antes da substituição:**
```python
print(f"[DEBUG][INICIAR_IMPLANTACAO] 📋 Campos customizados ANTES da substituição:")
print(f"[DEBUG][INICIAR_IMPLANTACAO]   {custom_fields_config}")
# Esperado: {'data_de_inicio_da_implantacao': 'CURRENT_DATE'}
```

#### 📋 **Depois da substituição:**
```python
print(f"[DEBUG][INICIAR_IMPLANTACAO] 📋 Campos customizados DEPOIS da substituição:")
print(f"[DEBUG][INICIAR_IMPLANTACAO]   - data_de_inicio_da_implantacao: {custom_fields_config['data_de_inicio_da_implantacao']}")
# Esperado: '2025-10-15' (data do modal)
```

#### 🔄 **Na função _resolver_custom_fields:**
```python
[DEBUG][RESOLVER_CUSTOM] 🔄 RESOLVENDO CAMPOS CUSTOMIZADOS
[DEBUG][RESOLVER_CUSTOM] 📥 Campos RECEBIDOS: {'data_de_inicio_da_implantacao': '2025-10-15', ...}
[DEBUG][RESOLVER_CUSTOM] 🔍 Processando: 'data_de_inicio_da_implantacao' = '2025-10-15'
[DEBUG][RESOLVER_CUSTOM]    ✓ Mantido como: 2025-10-15
```

Se aparecer:
```python
[DEBUG][RESOLVER_CUSTOM]    ⚠️  CURRENT_DATE detectado! Substituindo por: 2025-10-12
```

Significa que o valor **NÃO** foi substituído corretamente antes de chegar na função.

---

## 🧪 Como Testar

1. **Execute o processo de agendamento**
2. **Preencha o modal com uma data diferente da atual** (ex: 15/10/2025)
3. **Procure no console pelos logs:**

```
[DEBUG][INICIAR_IMPLANTACAO] 📋 Campos customizados ANTES da substituição:
[DEBUG][INICIAR_IMPLANTACAO]   {'data_de_inicio_da_implantacao': 'CURRENT_DATE'}

[DEBUG][INICIAR_IMPLANTACAO] 📋 Campos customizados DEPOIS da substituição:
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_inicio_da_implantacao: 2025-10-15
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_termino_original: 2025-11-15
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_virada_original: 2025-11-30
```

4. **Verificar no Zoho Projects** se o campo foi preenchido com `2025-10-15` (data do modal) ou `2025-10-12` (data atual)

---

## 🎯 Cenários Possíveis

### ✅ **Cenário 1: Funcionando Corretamente**
```
[DEBUG][INICIAR_IMPLANTACAO] DEPOIS da substituição:
  - data_de_inicio_da_implantacao: 2025-10-15

[DEBUG][RESOLVER_CUSTOM] Processando: 'data_de_inicio_da_implantacao' = '2025-10-15'
[DEBUG][RESOLVER_CUSTOM]    ✓ Mantido como: 2025-10-15
```
**Resultado:** Campo no Zoho = `2025-10-15` ✓

---

### ❌ **Cenário 2: Ainda com CURRENT_DATE**
```
[DEBUG][INICIAR_IMPLANTACAO] DEPOIS da substituição:
  - data_de_inicio_da_implantacao: CURRENT_DATE

[DEBUG][RESOLVER_CUSTOM] Processando: 'data_de_inicio_da_implantacao' = 'CURRENT_DATE'
[DEBUG][RESOLVER_CUSTOM]    ⚠️  CURRENT_DATE detectado! Substituindo por: 2025-10-12
```
**Resultado:** Campo no Zoho = `2025-10-12` (data atual) ✗

**Possível causa:** A substituição na linha 1767 não está funcionando. Pode ser:
- O `copy()` não está criando uma cópia profunda
- Há outro código sobrescrevendo depois

---

### ❌ **Cenário 3: Substituição Parcial**
```
[DEBUG][INICIAR_IMPLANTACAO] DEPOIS da substituição:
  - data_de_inicio_da_implantacao: 2025-10-15

[DEBUG][RESOLVER_CUSTOM] Processando: 'data_de_inicio_da_implantacao' = 'CURRENT_DATE'
[DEBUG][RESOLVER_CUSTOM]    ⚠️  CURRENT_DATE detectado!
```
**Resultado:** A substituição funcionou localmente, mas o valor não propagou para `_resolver_custom_fields`

**Possível causa:** A `info_dest_modificada` não está sendo passada corretamente para `_atualizar_zoho`

---

## 🔧 Soluções Alternativas (se necessário)

### **Opção 1: Mudar o mapeamento_colunas.json**
```json
"Em Andamento - Implantação": {
  "zohoCustomFields": {
    // Remover esta linha ou deixar vazio
    // "data_de_inicio_da_implantacao": "CURRENT_DATE"
  }
}
```

**Prós:** Elimina o placeholder problemático  
**Contras:** Precisaríamos garantir que o código sempre define o campo

---

### **Opção 2: Verificação Extra no _resolver_custom_fields**
```python
def _resolver_custom_fields(custom_fields: dict) -> dict:
    resolved = {}
    for chave, valor in (custom_fields or {}).items():
        # Se já é uma data no formato YYYY-MM-DD, manter
        if isinstance(valor, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', valor):
            resolved[chave] = valor
        elif isinstance(valor, str) and valor.upper() == "CURRENT_DATE":
            resolved[chave] = date.today().strftime("%Y-%m-%d")
        else:
            resolved[chave] = valor
    return resolved
```

---

## 📊 Próximos Passos

1. ✅ Execute o teste com os novos logs
2. 📋 Compartilhe os logs das seções mencionadas
3. 🔍 Com base nos logs, identificaremos exatamente onde está falhando
4. 🔧 Aplicaremos a correção definitiva

---

**Data:** 12 de outubro de 2025  
**Status:** Logs implementados, aguardando teste
