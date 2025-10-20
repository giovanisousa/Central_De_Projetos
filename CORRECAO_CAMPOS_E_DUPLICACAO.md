# 🐛 Correção Final: Nomes de Campos e Duplicação de Eventos

## ❌ Problemas Identificados no Teste

### Problema 1: **Campos Trocados no Zoho**

**Sintoma**:
- Campo `data_de_termino_original` recebia a data de **VIRADA** (09/02/2026)
- Mas deveria receber a data de **HOMOLOGAÇÃO**

**Causa**:
Confusão nos nomes dos campos:
```python
# ❌ ERRADO (antes)
data_termino_original = data_homologacao  # Campo sem o prefixo "data_de_"
data_de_termino_original = data_virada     # Campo com prefixo "data_de_"
```

**Nomes Corretos** (confirmados pelo usuário):
- ✅ `data_de_termino_original` = **Data de Homologação Prevista**
- ✅ `data_de_virada_original` = **Data de Virada Prevista**

---

### Problema 2: **Eventos Duplicados no Google Calendar**

**Sintoma**:
- 2 eventos de Homologação criados
- 2 eventos de Virada criados
- Total: 4 eventos em vez de 2

**Causa**:
Código JavaScript com **event listener duplicado** para o formulário `play-form`:
```javascript
// Listener 1 (linha ~825)
playForm.addEventListener('submit', async (ev) => {
    // ... chama /api/iniciar_implantacao
});

// Listener 2 (linha ~1267) - ❌ DUPLICADO!
document.getElementById('play-form')?.addEventListener('submit', async function(e) {
    // ... chama /api/iniciar_implantacao novamente
});
```

**Resultado**:
- Cada clique no botão "Agendar" executava a API **2 vezes**
- Cada execução criava os 2 eventos → Total: 4 eventos

---

## ✅ Soluções Implementadas

### Correção 1: Nomes dos Campos do Zoho

#### 1.1. Variáveis renomeadas:

**ANTES** (❌ Errado):
```python
# Campo sem prefixo "data_de_"
data_termino_original = data_homologacao_prevista_dt.strftime('%Y-%m-%d')

# Campo com prefixo "data_de_" (mas usado para virada)
data_de_termino_original = data_virada_prevista_dt.strftime('%Y-%m-%d')
```

**AGORA** (✅ Correto):
```python
# Campo com prefixo "data_de_" = Homologação
data_de_termino_original = data_homologacao_prevista_dt.strftime('%Y-%m-%d')

# Campo com prefixo "data_de_virada_" = Virada
data_de_virada_original = data_virada_prevista_dt.strftime('%Y-%m-%d')
```

#### 1.2. Logs atualizados:

```python
print(f"[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:")
print(f"[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: {data_inicio_implantacao}")
print(f"[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista (data_de_termino_original): {data_de_termino_original}")
print(f"[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista (data_de_virada_original): {data_de_virada_original}")
```

#### 1.3. Atribuição dos campos customizados:

```python
custom_fields_config["data_de_inicio_da_implantacao"] = data_inicio_implantacao
custom_fields_config["data_de_termino_original"] = data_de_termino_original  # Homologação
custom_fields_config["data_de_virada_original"] = data_de_virada_original     # Virada
```

#### 1.4. Payload do fallback:

```python
payload_custom = {
    "custom_fields": {
        "data_de_inicio_da_implantacao": data_inicio_implantacao,
        "data_de_termino_original": data_de_termino_original,  # Homologação
        "data_de_virada_original": data_de_virada_original     # Virada
    }
}
```

#### 1.5. Criação dos eventos do Google Calendar:

```python
# Evento de Homologação
sucesso_homolog, event_id_homolog, erro_homolog = criar_evento_homologacao(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_homologacao=data_de_termino_original,  # ✅ Homologação
    modalidade=modalidade
)

# Evento de Virada
sucesso_virada, event_id_virada, erro_virada = criar_evento_virada(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_virada=data_de_virada_original,  # ✅ Virada
    modalidade=modalidade
)
```

---

### Correção 2: Event Listener Duplicado Removido

**Arquivo**: `templates/index.html`

**ANTES** (❌ Duplicado):
```javascript
// Listener 1 (linha ~825) - Mantido
playForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    // ... lógica completa
});

// Listener 2 (linha ~1267) - ❌ REMOVIDO!
document.getElementById('play-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    // ... mesma lógica (duplicada)
});
```

**AGORA** (✅ Único listener):
```javascript
// Apenas o listener original (linha ~825)
playForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    
    const projectId = document.getElementById('play-project-id').value;
    const dataInicio = document.getElementById('data_inicio_implantacao').value;
    const implRIS = document.getElementById('implantador_ris')?.value || '';
    const implPACS = document.getElementById('implantador_pacs')?.value || '';

    const resp = await fetch('/api/iniciar_implantacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            project_id: projectId,
            data_inicio_implantacao: dataInicio,
            implantador_ris: implRIS,
            implantador_pacs: implPACS
        })
    });
    
    // ... tratamento de resposta
});

// Listener 2 removido completamente
```

---

## 🎯 Resultado Esperado

### No Zoho Projects:

| Campo | Valor Esperado (Exemplo) | Descrição |
|-------|--------------------------|-----------|
| `data_de_inicio_da_implantacao` | 27/10/2025 | Início da implantação |
| **`data_de_termino_original`** | **02/02/2026** | **Data de Homologação Prevista** ✅ |
| **`data_de_virada_original`** | **09/02/2026** | **Data de Virada Prevista** ✅ |

**Antes vs Depois**:
```diff
- data_de_termino_original: 09/02/2026 ❌ (errado - era data de virada)
+ data_de_termino_original: 02/02/2026 ✅ (correto - data de homologação)

- data_de_termino_original: 09/02/2026 ❌ (campo errado)
+ data_de_virada_original: 09/02/2026 ✅ (campo correto - data de virada)
```

---

### No Google Calendar:

**Antes** (❌ Duplicado):
```
📅 Homologação - 9861 - Projeto teste (02-06/02/2026) ← Evento 1
📅 Homologação - 9861 - Projeto teste (02-06/02/2026) ← Evento 2 (DUPLICADO)
📅 Virada - 9861 - Projeto teste (09-13/02/2026) ← Evento 3
📅 Virada - 9861 - Projeto teste (09-13/02/2026) ← Evento 4 (DUPLICADO)
```

**Agora** (✅ Único):
```
📅 Homologação - 9861 - Projeto teste (02-06/02/2026) ← Único evento
📅 Virada - 9861 - Projeto teste (09-13/02/2026) ← Único evento
```

---

### Nos Logs:

**Logs esperados**:
```
[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:
[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: 2025-10-27
[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista (data_de_termino_original): 2026-02-02
[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista (data_de_virada_original): 2026-02-09

[DEBUG][INICIAR_IMPLANTACAO] Configuração modificada com datas:
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_inicio_da_implantacao: 2025-10-27
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_termino_original: 2026-02-02
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_virada_original: 2026-02-09

[DEBUG][GOOGLE_CALENDAR] Criando evento de Homologação:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Homologação 9861 - Projeto teste (Remoto)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 02/02/2026 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 06/02/2026 (Friday)
[INFO][GOOGLE_CALENDAR] ✅ Evento de Homologação criado com sucesso!

[DEBUG][GOOGLE_CALENDAR] Criando evento de Virada:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Virada 9861 - Projeto teste (Remoto)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 09/02/2026 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 13/02/2026 (Friday)
[INFO][GOOGLE_CALENDAR] ✅ Evento de Virada criado com sucesso!
```

**Observação importante**: Agora deve aparecer **apenas uma vez** cada bloco de logs!

---

## 📊 Mapeamento Completo dos Campos

### Campos Customizados do Zoho (confirmados):

| Campo no Zoho | Tipo | Descrição | Calculado Como |
|--------------|------|-----------|----------------|
| `data_de_inicio_da_implantacao` | date | Data de início da implantação | Selecionada pelo usuário |
| `data_de_termino_original` | date | **Data de Homologação Prevista** | Início + 95 dias (netRIS) ou 35 dias (PACS) → segunda-feira |
| `data_de_virada_original` | date | **Data de Virada Prevista** | Homologação + 7 dias → segunda-feira |

### Eventos do Google Calendar:

| Evento | Campo Base | Duração | Cor |
|--------|-----------|---------|-----|
| **Homologação** | `data_de_termino_original` | Segunda a sexta (5 dias) | Magenta |
| **Virada** | `data_de_virada_original` | Segunda a sexta (5 dias) | Magenta |

---

## 🔍 Arquivos Alterados

### 1. `routes/api.py` (linhas ~1719-1950)

**Mudanças**:
- ✅ Renomeado `data_termino_original` → `data_de_termino_original`
- ✅ Renomeado `data_de_termino_original` → `data_de_virada_original`
- ✅ Todos os logs atualizados
- ✅ Atribuições dos campos customizados corrigidas
- ✅ Chamadas para criar eventos corrigidas

### 2. `templates/index.html` (linha ~1267-1310)

**Mudanças**:
- ✅ Removido event listener duplicado para `play-form`
- ✅ Agora apenas **uma chamada** à API por clique

---

## 🧪 Checklist de Validação

### Teste 1: Verificar campos no Zoho
- [ ] Campo `data_de_termino_original` preenchido com data de **HOMOLOGAÇÃO** (ex: 02/02/2026)
- [ ] Campo `data_de_virada_original` preenchido com data de **VIRADA** (ex: 09/02/2026)
- [ ] Ambas as datas calculadas corretamente baseadas nos produtos

### Teste 2: Verificar eventos no Google Calendar
- [ ] **Apenas 1** evento de Homologação criado
- [ ] **Apenas 1** evento de Virada criado
- [ ] Sem eventos duplicados
- [ ] Datas corretas (segunda a sexta de cada semana)

### Teste 3: Verificar logs
- [ ] Cada bloco de logs aparece **apenas uma vez**
- [ ] Logs mostram os nomes corretos dos campos
- [ ] Nenhum erro `UnboundLocalError`

---

## 🚀 Teste Final

Execute o teste completo:

```powershell
python app.py
```

1. Clique no botão ▶️ "Agendar Implantação"
2. Preencha os dados e confirme
3. Verifique:
   - ✅ Zoho: 2 campos preenchidos com datas corretas
   - ✅ Calendar: 2 eventos criados (sem duplicatas)
   - ✅ Logs: Cada mensagem aparece apenas 1 vez

---

**Data**: 19/10/2025  
**Status**: ✅ Corrigido - Pronto para teste final  
**Arquivos Alterados**: 
- `routes/api.py` (nomes dos campos)
- `templates/index.html` (event listener duplicado removido)
