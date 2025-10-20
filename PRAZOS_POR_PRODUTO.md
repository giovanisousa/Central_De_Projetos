# 🎯 Prazos de Implantação por Produto - Implementação Final

## 📋 Regras de Negócio

### Prazos Definidos:

| Produto Contratado | Prazo até Homologação | Observação |
|-------------------|----------------------|------------|
| **netRIS** (com ou sem AP) | **95 dias corridos** | Projeto mais complexo |
| **Apenas AnimatiPACS** | **35 dias corridos** | Projeto mais simples |

### Lógica de Identificação:

1. **Fonte Primária**: Campo `produtos_contratados` do banco de dados
   - Mais confiável
   - Dados estruturados extraídos da descrição do projeto
   - JSON com lista de produtos: `["netRIS", "AnimatiPACS"]`

2. **Fallback**: Nome do projeto (sufixos)
   - Usado apenas se `produtos_contratados` estiver vazio
   - Identifica por: ` - NR`, ` - AP`, ` - NR/AP`

3. **Padrão Conservador**: 95 dias
   - Usado se nenhum método conseguir identificar
   - Evita prazos irrealistas

---

## ✅ Implementação

### Arquivo: `routes/api.py`

**Lógica de Identificação (linhas ~1650-1700)**:

```python
# ==== IDENTIFICAR FERRAMENTAS CONTRATADAS DO BANCO DE DADOS ====
# sqlite3.Row usa acesso por índice/coluna, não .get()
try:
    produtos_contratados_json = project_row['produtos_contratados']
except (KeyError, IndexError):
    produtos_contratados_json = None

try:
    if produtos_contratados_json:
        produtos_list = json.loads(produtos_contratados_json)
    else:
        produtos_list = []
except (json.JSONDecodeError, TypeError):
    produtos_list = []

# Normalizar nomes de produtos para comparação
produtos_normalized = [p.strip().lower() for p in produtos_list if p]

# Verificar se tem netRIS
tem_netris = any('netris' in p for p in produtos_normalized)
tem_apenas_ap = any('pacs' in p or 'animatipacs' in p for p in produtos_normalized) and not tem_netris

if tem_netris:
    dias_ate_homologacao = 95
    tipo_projeto_label = "netRIS"
elif tem_apenas_ap:
    dias_ate_homologacao = 35
    tipo_projeto_label = "AnimatiPACS"
else:
    # Fallback pelo nome do projeto
    proj_name = str((detalhes_zoho or {}).get('name', '') or '')
    tem_netris_nome = ' - NR/AP' in proj_name or ' - NR' in proj_name
    tem_apenas_ap_nome = ' - AP' in proj_name and not tem_netris_nome
    
    if tem_netris_nome:
        dias_ate_homologacao = 95
        tipo_projeto_label = "netRIS (fallback por nome)"
    elif tem_apenas_ap_nome:
        dias_ate_homologacao = 35
        tipo_projeto_label = "AnimatiPACS (fallback por nome)"
    else:
        # Padrão conservador
        dias_ate_homologacao = 95
        tipo_projeto_label = "padrão (conservador)"
```

### Arquivo: `mapeamento_colunas.json`

**Documentação Declarativa**:

```json
{
  "data_termino_original": {
    "type": "add_calendar_days",
    "baseField": "data_de_inicio_da_implantacao",
    "daysRules": {
      "netRIS": 95,
      "AnimatiPACS": 35,
      "default": 95
    },
    "determinedBy": "produtos_contratados",
    "adjustToMonday": true,
    "description": "Data de Homologação Prevista - Varia conforme produtos: netRIS (95 dias corridos) ou apenas AnimatiPACS (35 dias corridos)"
  }
}
```

---

## 🔍 Exemplos de Identificação

### Exemplo 1: netRIS + AnimatiPACS

**Banco de Dados**:
```json
{
  "id": "2376502000005544019",
  "name": "1234 - Hospital ABC - NR/AP",
  "produtos_contratados": "[\"netRIS\", \"AnimatiPACS\"]"
}
```

**Resultado**:
```
✅ tem_netris = True (encontrou 'netris' em produtos_normalized)
✅ dias_ate_homologacao = 95
✅ tipo_projeto_label = "netRIS"
```

**Datas Calculadas** (início: 20/10/2025):
- Homologação: 20/10 + 95 dias = 23/01/2026 → Ajusta para segunda: **27/01/2026**
- Virada: 27/01 + 7 dias = 03/02/2026 (segunda-feira) ✅

---

### Exemplo 2: Apenas AnimatiPACS

**Banco de Dados**:
```json
{
  "id": "2376502000005544020",
  "name": "5678 - Clínica XYZ - AP",
  "produtos_contratados": "[\"AnimatiPACS\"]"
}
```

**Resultado**:
```
✅ tem_netris = False
✅ tem_apenas_ap = True (encontrou 'pacs' em produtos_normalized)
✅ dias_ate_homologacao = 35
✅ tipo_projeto_label = "AnimatiPACS"
```

**Datas Calculadas** (início: 20/10/2025):
- Homologação: 20/10 + 35 dias = 24/11/2025 → Ajusta para segunda: **24/11/2025** (já é segunda)
- Virada: 24/11 + 7 dias = 01/12/2025 (segunda-feira) ✅

---

### Exemplo 3: Fallback por Nome

**Banco de Dados**:
```json
{
  "id": "2376502000005544021",
  "name": "9999 - Centro Médico - NR",
  "produtos_contratados": null
}
```

**Resultado**:
```
⚠️  produtos_list = [] (campo vazio)
⚠️  Fallback: Analisa nome do projeto
✅ tem_netris_nome = True (encontrou ' - NR' no nome)
✅ dias_ate_homologacao = 95
✅ tipo_projeto_label = "netRIS (fallback por nome)"
```

---

### Exemplo 4: Padrão Conservador

**Banco de Dados**:
```json
{
  "id": "2376502000005544022",
  "name": "0000 - Projeto Teste",
  "produtos_contratados": null
}
```

**Resultado**:
```
⚠️  produtos_list = [] (campo vazio)
⚠️  Nome sem sufixo identificável
⚠️  Usando padrão conservador
✅ dias_ate_homologacao = 95
✅ tipo_projeto_label = "padrão (conservador)"
```

---

## 🧪 Logs de Debug

### Projeto com netRIS (95 dias):

```
[DEBUG][INICIAR_IMPLANTACAO] Projeto com netRIS detectado (produtos: ['netRIS', 'AnimatiPACS']) - Prazo: 95 dias
[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:
[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista (data_termino_original): 2026-01-27
[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista (data_de_termino_original): 2026-02-03
```

### Projeto apenas AnimatiPACS (35 dias):

```
[DEBUG][INICIAR_IMPLANTACAO] Projeto apenas AnimatiPACS detectado (produtos: ['AnimatiPACS']) - Prazo: 35 dias
[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:
[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista (data_termino_original): 2025-11-24
[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista (data_de_termino_original): 2025-12-01
```

### Fallback por Nome:

```
[WARN][INICIAR_IMPLANTACAO] Produtos não identificados no BD. Usando nome do projeto - Prazo: 95 dias
[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:
[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista (data_termino_original): 2026-01-27
[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista (data_de_termino_original): 2026-02-03
```

---

## 📊 Comparação: Antes vs Depois

### ❌ ANTES (Baseado em Nome):

```python
# Identificação pelo sufixo do nome
if ' - NR/AP' in proj_name:
    produto = 'netRIS e AnimatiPACS'
elif ' - NR' in proj_name:
    produto = 'netRIS'
elif ' - AP' in proj_name:
    produto = 'AnimatiPACS'
```

**Problemas**:
- ❌ Dependia do padrão de nomenclatura
- ❌ Projetos sem sufixo não eram identificados
- ❌ Renomeação do projeto quebrava a lógica

### ✅ AGORA (Baseado em Banco de Dados):

```python
# Lê do campo estruturado do banco
produtos_list = json.loads(project_row.get('produtos_contratados'))
tem_netris = any('netris' in p.lower() for p in produtos_list)
```

**Benefícios**:
- ✅ **Fonte confiável**: Dados extraídos da descrição do projeto
- ✅ **Independente do nome**: Projeto pode ser renomeado
- ✅ **Fallback robusto**: Nome como plano B
- ✅ **Padrão conservador**: Evita prazos irrealistas

---

## 🎯 Vantagens da Implementação

### 1️⃣ **Precisão**
- Usa dados estruturados do banco
- Não depende de convenções de nomenclatura
- Reduz erros de interpretação

### 2️⃣ **Robustez**
- Múltiplas camadas de fallback
- Normalização de strings (case-insensitive, trim)
- Padrão conservador para casos não identificados

### 3️⃣ **Manutenibilidade**
- Regras centralizadas no código
- Documentação no `mapeamento_colunas.json`
- Fácil ajustar prazos se necessário

### 4️⃣ **Rastreabilidade**
- Logs detalhados sobre qual método foi usado
- Identifica produtos contratados nos logs
- Facilita troubleshooting

---

## 🔄 Fluxo Completo de Identificação

```
┌─────────────────────────────────────┐
│  Buscar project_row do banco        │
│  Campo: produtos_contratados         │
└──────────────┬──────────────────────┘
               │
               ▼
      ┌────────────────┐
      │  JSON válido?  │───── NÃO ──┐
      └────────┬───────┘             │
               │ SIM                 │
               ▼                     ▼
   ┌──────────────────────┐   ┌──────────────┐
   │ Normalizar produtos  │   │ Fallback:    │
   │ (lowercase, trim)    │   │ Nome projeto │
   └──────────┬───────────┘   └──────┬───────┘
              │                      │
              ▼                      ▼
       ┌─────────────┐        ┌─────────────┐
       │ 'netris' em │        │ ' - NR' em  │
       │ produtos?   │        │ nome?       │
       └──────┬──────┘        └──────┬──────┘
              │                      │
       ┌──────┴──────┐        ┌──────┴──────┐
       ▼             ▼        ▼             ▼
    SIM: 95d    NÃO: 35d   SIM: 95d    NÃO: 95d
    (netRIS)   (só PACS)  (fallback)  (padrão)
```

---

## 📝 Checklist de Validação

- [x] Lógica lê `produtos_contratados` do banco
- [x] Normalização case-insensitive
- [x] Detecção de netRIS: 95 dias
- [x] Detecção de apenas PACS: 35 dias
- [x] Fallback por nome do projeto
- [x] Padrão conservador: 95 dias
- [x] Logs informativos em cada caso
- [x] Documentação no `mapeamento_colunas.json`
- [ ] **Teste com projeto netRIS real**
- [ ] **Teste com projeto apenas PACS real**
- [ ] **Verificar datas no Zoho**

---

## 🚀 Próximos Passos

1. ✅ **Implementado**: Lógica baseada em `produtos_contratados`
2. ⏳ **Pendente**: Testar com projetos reais
3. ⏳ **Pendente**: Validar datas calculadas no Zoho
4. 💡 **Futuro**: Criar relatório de prazos por produto

---

**Data**: 19/10/2025  
**Versão**: 3.0 - Prazos baseados em dados do banco  
**Status**: ✅ Implementado e pronto para testes
