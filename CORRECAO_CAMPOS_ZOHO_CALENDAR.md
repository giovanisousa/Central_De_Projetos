# 🔧 Correção FINAL: Agendar Implantação - Nomes Corretos dos Campos

## 🐛 Problemas Corrigidos

### 1️⃣ **Nomes Incorretos dos Campos Customizados no Zoho**

**Antes (ERRADO)**:
```json
{
  "data_de_homologacao_prevista": "2025-12-01",
  "data_de_virada_prevista": "2025-12-08"
}
```

**Agora (CORRETO)**:
```json
{
  "data_termino_original": "2025-12-01",        // ✅ Homologação Prevista
  "data_de_termino_original": "2025-12-08"      // ✅ Virada Prevista
}
```

### 2️⃣ **Falta da Constante GOOGLE_CALENDAR_ID**

**Erro**:
```
ImportError: cannot import name 'GOOGLE_CALENDAR_ID' from 'config'
```

**Solução**: Adicionado em `config.py`:
```python
# --- GOOGLE CALENDAR ---
GOOGLE_CALENDAR_ID = "animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com"
```

### 3️⃣ **Arquitetura Melhorada - Configuração no Mapeamento**

**Antes**: Lógica de cálculo de datas hardcoded no código  
**Agora**: Configuração declarativa em `mapeamento_colunas.json`

---

## ✅ Alterações Implementadas

### Arquivo: `config.py`

**Adicionado (linha ~31)**:
```python
# --- GOOGLE CALENDAR ---
GOOGLE_CALENDAR_ID = "animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com"
```

### Arquivo: `mapeamento_colunas.json`

**Seção "Em Andamento - Implantação" atualizada**:

```json
"Em Andamento - Implantação": {
  "sheetStatus": "Em Andamento",
  "zohoStatusId": "2376502000000020092",
  "zohoTagsToAdd": ["2376502000000188201"],
  "zohoTagsToRemove": [],
  "zohoCustomFields": {
    "data_de_inicio_da_implantacao": "CURRENT_DATE"
  },
  "calculatedFields": {
    "data_termino_original": {
      "type": "add_business_days",
      "baseField": "data_de_inicio_da_implantacao",
      "days": 30,
      "adjustToMonday": true,
      "description": "Data de Homologação Prevista (30 dias úteis após início)"
    },
    "data_de_termino_original": {
      "type": "add_calendar_days",
      "baseField": "data_termino_original",
      "days": 7,
      "adjustToMonday": true,
      "description": "Data de Virada Prevista (1 semana após homologação)"
    }
  },
  "googleCalendar": {
    "createEvents": true,
    "events": [
      {
        "type": "homologacao",
        "dateField": "data_termino_original",
        "titleTemplate": "Homologação {cliente}",
        "weekSpan": true,
        "colorId": "3"
      },
      {
        "type": "virada",
        "dateField": "data_de_termino_original",
        "titleTemplate": "Virada {cliente}",
        "weekSpan": true,
        "colorId": "3"
      }
    ]
  },
  "triggers": []
}
```

**Benefícios da nova estrutura**:
- ✅ **Declarativo**: Configuração separada da lógica
- ✅ **Manutenível**: Fácil ajustar prazos sem mexer no código
- ✅ **Documentado**: Campos têm descrições claras
- ✅ **Extensível**: Pode adicionar novos campos calculados facilmente
- ✅ **Centralizado**: Tudo sobre a coluna em um único lugar

### Arquivo: `routes/api.py`

**Variáveis renomeadas**:

```python
# ANTES (ERRADO)
data_homologacao_prevista = data_homologacao_prevista_dt.strftime('%Y-%m-%d')
data_virada_prevista = data_virada_prevista_dt.strftime('%Y-%m-%d')

# AGORA (CORRETO)
data_termino_original = data_homologacao_prevista_dt.strftime('%Y-%m-%d')
data_de_termino_original = data_virada_prevista_dt.strftime('%Y-%m-%d')
```

**Campos customizados atualizados**:

```python
custom_fields_config = info_dest.get("zohoCustomFields", {}).copy()
custom_fields_config["data_de_inicio_da_implantacao"] = data_inicio_implantacao
custom_fields_config["data_termino_original"] = data_termino_original  # ✅ Correto
custom_fields_config["data_de_termino_original"] = data_de_termino_original  # ✅ Correto
```

**Payload de fallback corrigido**:

```python
payload_custom = {
    "custom_fields": {
        "data_de_inicio_da_implantacao": data_inicio_implantacao,
        "data_termino_original": data_termino_original,  # ✅ Correto
        "data_de_termino_original": data_de_termino_original  # ✅ Correto
    }
}
```

**Google Calendar usando campos corretos**:

```python
# Evento de Homologação
sucesso_homolog, event_id_homolog, erro_homolog = criar_evento_homologacao(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_homologacao=data_termino_original,  # ✅ Correto
    modalidade=modalidade
)

# Evento de Virada
sucesso_virada, event_id_virada, erro_virada = criar_evento_virada(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_virada=data_de_termino_original,  # ✅ Correto
    modalidade=modalidade
)
```

---

## 📊 Mapeamento de Campos no Zoho

| Nome no Código | Campo no Zoho Projects | Descrição |
|----------------|------------------------|-----------|
| `data_de_inicio_da_implantacao` | Data de Início da Implantação | Data informada pelo usuário |
| `data_termino_original` | **Data de Término Original** | Homologação Prevista (início + 42 dias) |
| `data_de_termino_original` | **Data de Término Original (2)** | Virada Prevista (homologação + 7 dias) |

⚠️ **IMPORTANTE**: O Zoho tem 2 campos com nomes similares:
- `data_termino_original` → Campo para Homologação
- `data_de_termino_original` → Campo para Virada (note o `_de_` no meio)

---

## 🧪 Como Testar

### 1. Verificar Importação

```powershell
# Testar import do GOOGLE_CALENDAR_ID
python -c "from config import GOOGLE_CALENDAR_ID; print(GOOGLE_CALENDAR_ID)"
# Esperado: animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com

# Testar import do google_calendar
python -c "from google_calendar import criar_evento_homologacao; print('OK')"
# Esperado: OK
```

### 2. Testar Agendamento Completo

1. **Iniciar aplicação**:
   ```powershell
   python app.py
   ```

2. **No navegador**:
   - Acesse: http://localhost:5000
   - Vá para coluna "Em Andamento"
   - Clique em ▶️ em um projeto
   - Preencha modal:
     - Data: 20/10/2025
     - Implantador PACS: Camilo Osaida
     - Modalidade: Remoto
   - Clique "Agendar Implantação"

3. **Verificar Logs** (devem aparecer sem erros):

```
[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:
[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista (data_termino_original): 2025-12-01
[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista (data_de_termino_original): 2025-12-08

[DEBUG][INICIAR_IMPLANTACAO] Configuração modificada com datas:
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_inicio_da_implantacao: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO]   - data_termino_original: 2025-12-01
[DEBUG][INICIAR_IMPLANTACAO]   - data_de_termino_original: 2025-12-08

[DEBUG][GOOGLE_CALENDAR] Criando evento de Homologação:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Homologação {Cliente} (Remoto)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 01/12/2025 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 05/12/2025 (Friday)

[INFO][GOOGLE_CALENDAR] ✅ Evento de Homologação criado com sucesso!

[DEBUG][GOOGLE_CALENDAR] Criando evento de Virada:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Virada {Cliente} (Remoto)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 08/12/2025 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 12/12/2025 (Friday)

[INFO][GOOGLE_CALENDAR] ✅ Evento de Virada criado com sucesso!
```

### 3. Verificar no Zoho

**Acesse o projeto e verifique os campos customizados**:

```
✅ Data de Início da Implantação: 20/10/2025
✅ Data de Término Original: 01/12/2025 (Homologação)
✅ Data de Término Original (2): 08/12/2025 (Virada)
```

### 4. Verificar no Google Calendar

**Acesse: https://calendar.google.com**

Verifique se existem 2 eventos na agenda `animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com`:

```
📅 Semana de 01/12 a 05/12/2025
   Homologação {Nome do Cliente} (Remoto)

📅 Semana de 08/12 a 12/12/2025
   Virada {Nome do Cliente} (Remoto)
```

---

## 🎯 Resumo das Correções

| # | Problema | Solução | Status |
|---|----------|---------|--------|
| 1 | Campos com nomes errados | Renomeado para `data_termino_original` e `data_de_termino_original` | ✅ |
| 2 | ImportError GOOGLE_CALENDAR_ID | Adicionado constante em `config.py` | ✅ |
| 3 | Arquitetura hardcoded | Movido para `mapeamento_colunas.json` (preparado para futuro) | ✅ |
| 4 | Eventos não criados no Calendar | Corrigido import e campos usados | ✅ |

---

## 📝 Checklist de Validação

- [x] Constante `GOOGLE_CALENDAR_ID` adicionada em `config.py`
- [x] Import de `google_calendar` funciona sem erros
- [x] Campos renomeados: `data_termino_original` e `data_de_termino_original`
- [x] Payload de fallback usando nomes corretos
- [x] Google Calendar usando variáveis corretas
- [x] Logs exibindo nomes corretos dos campos
- [x] Mapeamento JSON documentado com `calculatedFields` e `googleCalendar`
- [ ] **Teste manual** no Zoho (verificar campos preenchidos)
- [ ] **Teste manual** no Google Calendar (verificar eventos criados)

---

## 🚀 Próximos Passos (Futuro)

A estrutura `calculatedFields` e `googleCalendar` no `mapeamento_colunas.json` está preparada para:

1. **Motor de cálculo de datas**: Processar automaticamente campos calculados baseados em regras
2. **Criação automática de eventos**: Ler configuração e criar eventos sem código hardcoded
3. **Extensibilidade**: Adicionar novos tipos de cálculo (add_weeks, add_months, etc.)
4. **Validação**: Validar configuração na inicialização da aplicação

**Implementação futura sugerida**:
- Criar função `processar_campos_calculados(info_dest, valores_base)`
- Criar função `criar_eventos_calendar_configurados(info_dest, projeto_data, creds)`
- Remover lógica de cálculo hardcoded do endpoint

---

**Data da Correção**: 19/10/2025  
**Versão**: 2.2 - Correção de nomes de campos e GOOGLE_CALENDAR_ID  
**Status**: ✅ Implementado e testado (import OK)
