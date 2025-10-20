# 🎨 Diagrama Visual: Fluxo de Sincronização Completo

**Data**: 13 de outubro de 2025

---

## 📊 Fluxo Detalhado: Movendo para "Em Homologação"

```
┌──────────────────────────────────────────────────────────────────┐
│                         🎨 FRONTEND                               │
│                                                                   │
│  Usuário arrasta card de "Em Andamento - Implantação"           │
│           para "Em Homologação"                                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  POST /api/mover_projeto                                │   │
│  │  {                                                       │   │
│  │    "projeto_id": "2376502000005544019",                 │   │
│  │    "coluna_origem": "Em Andamento - Implantação",       │   │
│  │    "coluna_destino": "Em Homologação",                  │   │
│  │    "cliente_sheet": "Nome do Cliente"                   │   │
│  │  }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      💾 BACKEND - BANCO LOCAL                     │
│                                                                   │
│  ⏱️ Timestamp: 0ms - Atualização Imediata                        │
│                                                                   │
│  UPDATE projects SET                                              │
│    data_mudanca_status = '2025-10-13',                           │
│    status_atual = 'Em Homologação'                               │
│  WHERE id = '2376502000005544019'                                │
│                                                                   │
│  ✅ Log: [MOVE][DB] data_mudanca_status atualizada               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   📖 BACKEND - MAPEAMENTO JSON                    │
│                                                                   │
│  ⏱️ Timestamp: 10ms - Leitura de Configuração                    │
│                                                                   │
│  Lê: mapeamento_colunas.json["Em Homologação"]                  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ zohoStatusId: "2376502000000020092"                    │     │
│  │ zohoTagsToAdd: ["2376502000000983053"]                 │     │
│  │ zohoTagsToRemove: ["2376502000000188201"]              │     │
│  │ zohoCustomFields: {                                    │     │
│  │   "data_de_homologacao": "CURRENT_DATE"                │     │
│  │ }                                                       │     │
│  │ onTransition: {                                        │     │
│  │   "from_Em_Andamento_-_Implantação": {                 │     │
│  │     "sheetColumns": {                                  │     │
│  │       "Dt Homolog": "CURRENT_DATE_DDMMYYYY"            │     │
│  │     }                                                   │     │
│  │   }                                                     │     │
│  │ }                                                       │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                  🔧 BACKEND - RESOLVER PLACEHOLDERS               │
│                                                                   │
│  ⏱️ Timestamp: 15ms - Conversão de Valores                       │
│                                                                   │
│  "CURRENT_DATE" → "2025-10-13"                                   │
│  "CURRENT_DATE_DDMMYYYY" → "13/10/2025"                          │
│                                                                   │
│  ✅ Log: [DEBUG] Campo resolvido para data atual                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   🏢 BACKEND - ZOHO PROJECTS API                  │
│                                                                   │
│  ⏱️ Timestamp: 100ms - Requisição HTTP                           │
│                                                                   │
│  PATCH https://projectsapi.zoho.com/api/v3/.../projects/{id}    │
│                                                                   │
│  Payload:                                                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ {                                                       │     │
│  │   "status": {"id": "2376502000000020092"},             │     │
│  │   "custom_fields": {                                   │     │
│  │     "data_de_homologacao": "2025-10-13"                │     │
│  │   }                                                     │     │
│  │ }                                                       │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  Response: 200 OK ✅                                              │
│                                                                   │
│  Tags (separadamente):                                            │
│  - DELETE tag "2376502000000188201" (Em Implantação) ✅          │
│  - POST tag "2376502000000983053" (Em Homologação) ✅            │
│                                                                   │
│  ✅ Log: [MOVE][ZOHO] Projeto atualizado                         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│          💾 BACKEND - SINCRONIZAÇÃO BANCO ⭐ NOVO                 │
│                                                                   │
│  ⏱️ Timestamp: 150ms - SQL Update                                │
│                                                                   │
│  Função: _sincronizar_custom_fields_banco()                      │
│                                                                   │
│  Mapeamento:                                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ data_de_homologacao (Zoho) → data_homologacao (Banco) │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  UPDATE projects SET                                              │
│    data_homologacao = '2025-10-13'                               │
│  WHERE id = '2376502000005544019'                                │
│                                                                   │
│  ✅ Log: [DEBUG][DB] Preparando atualização                      │
│  ✅ Log: [DEBUG][DB] Campos sincronizados com Zoho               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│               📊 BACKEND - GOOGLE SHEETS API                      │
│                                                                   │
│  ⏱️ Timestamp: 500ms - Requisição HTTP                           │
│                                                                   │
│  1. Atualizar Status Principal                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Localizar linha do cliente na planilha                 │     │
│  │ Atualizar coluna "Status Principal" = "Em Homologação" │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ✅ Log: [MOVE][SHEET] Planilha atualizada                       │
│                                                                   │
│  2. Processar onTransition                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Detectar transição: "Em Andamento - Implantação"       │     │
│  │                  → "Em Homologação"                     │     │
│  │                                                         │     │
│  │ Atualizar coluna "Dt Homolog" = "13/10/2025"           │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ✅ Log: [DEBUG][SHEET] onTransition processado                  │
│  ✅ Log: [DEBUG][SHEET] Coluna 'Dt Homolog' atualizada           │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   🔙 BACKEND - RESPOSTA JSON                      │
│                                                                   │
│  ⏱️ Timestamp: 600ms - Total                                     │
│                                                                   │
│  {                                                                │
│    "sucesso": true,                                               │
│    "mensagem": "✅ Data mudança atualizada; Projeto atualizado   │
│                 no Zoho; Banco sincronizado; Planilha            │
│                 atualizada",                                      │
│    "dados_atualizados": {                                         │
│      "dias_na_fase": "Hoje",                                      │
│      "data_mudanca_status": "2025-10-13",                        │
│      "status_atual": "Em Homologação"                            │
│    }                                                              │
│  }                                                                │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   🎨 FRONTEND - ATUALIZAÇÃO UI                    │
│                                                                   │
│  ⏱️ Timestamp: 610ms - Renderização                              │
│                                                                   │
│  1. Card move visualmente para coluna "Em Homologação"          │
│  2. Badge "dias_na_fase" atualizado para "Hoje" (cor verde)     │
│  3. Dados do card atualizados sem refresh da página              │
│                                                                   │
│  ✅ Log: [CARD UPDATE] Card atualizado com novos dados           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Estado dos Dados Após Execução

### 🏢 Zoho Projects

```
Projeto: 2376502000005544019
├─ Status: "Em Andamento" (ID: 2376502000000020092)
├─ Tags:
│  ├─ ❌ "Em Implantação" (REMOVIDA)
│  └─ ✅ "Em Homologação" (ADICIONADA)
└─ Custom Fields:
   └─ data_de_homologacao: "2025-10-13" ✅
```

### 💾 Banco de Dados Local

```sql
SELECT * FROM projects WHERE id = '2376502000005544019';

┌───────────────────────┬──────────────────┬───────────────────┐
│ Campo                 │ Valor            │ Status            │
├───────────────────────┼──────────────────┼───────────────────┤
│ status_atual          │ Em Homologação   │ ✅ Atualizado     │
│ data_mudanca_status   │ 2025-10-13       │ ✅ Atualizado     │
│ data_homologacao      │ 2025-10-13       │ ✅ Sincronizado   │
│ dias_na_fase          │ Hoje             │ ✅ Calculado      │
└───────────────────────┴──────────────────┴───────────────────┘
```

### 📊 Google Sheets

```
Planilha Principal - Linha do Cliente
├─ Status Principal: "Em Homologação" ✅
└─ Dt Homolog: "13/10/2025" ✅
```

### 🎨 Interface do Usuário

```
Card Visual:
┌─────────────────────────────────────┐
│ 📋 Cliente - Código 123             │
│                                     │
│ GP: Giovani Sousa                   │
│ Status: Em Homologação              │
│                                     │
│ ⏱️ Dias na Fase: [Hoje] 🟢          │
└─────────────────────────────────────┘
```

---

## ⚡ Timeline de Performance

```
0ms    ━━ Requisição recebida
10ms   ━━ Banco local atualizado (data_mudanca_status)
15ms   ━━ Mapeamento JSON carregado
20ms   ━━ Placeholders resolvidos
100ms  ━━ Zoho atualizado (status + custom fields)
120ms  ━━ Tags ajustadas no Zoho
150ms  ━━ Banco sincronizado (data_homologacao) ⭐
500ms  ━━ Planilha atualizada (Status + Dt Homolog)
600ms  ━━ Resposta enviada ao frontend
610ms  ━━ Interface atualizada

Total: ~600ms ⚡
```

---

## 🔄 Comparação: Sincronização Antes vs Depois

### ❌ Antes (Sem Sincronização Automática)

```
0ms    ━━ Movimentação do card
100ms  ━━ Zoho atualizado
500ms  ━━ Planilha atualizada
600ms  ━━ Resposta ao usuário
       
       ⏰ Banco desatualizado...
       
~5min  ━━ Sincronização periódica roda
       ━━ Banco finalmente atualizado ❌
```

**Problema**: 5 minutos com dados inconsistentes!

### ✅ Depois (Com Sincronização Automática)

```
0ms    ━━ Movimentação do card
100ms  ━━ Zoho atualizado
150ms  ━━ Banco sincronizado ⚡ (imediato)
500ms  ━━ Planilha atualizada
600ms  ━━ Resposta ao usuário

✅ Todos os sistemas consistentes em <1s
```

**Benefício**: Dados sempre sincronizados!

---

## 🎯 Pontos de Sincronização

```
                    Movimentação de Card
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
   🏢 Zoho            💾 Banco            📊 Sheets
   Projects           de Dados           Principal
        │                  │                  │
        ├─ Status          ├─ status_atual    ├─ Status Principal
        ├─ Tags            ├─ data_mudanca    ├─ Dt Homolog
        └─ Custom Fields   └─ data_homolog... └─ (outras colunas)
                                  ↑
                                  │
                        ⭐ Sincronização Automática
                           (150ms após Zoho)
```

---

## 📋 Checklist de Validação Visual

Após mover um card, verificar:

```
✅ Frontend
   └─ Badge "Hoje" aparece imediatamente

✅ Console Backend
   ├─ [MOVE][DB] data_mudanca_status atualizada
   ├─ [DEBUG][DB] data_homologacao sincronizada ⭐
   ├─ [MOVE][ZOHO] Projeto atualizado no Zoho
   └─ [MOVE][SHEET] Planilha atualizada

✅ Zoho Projects
   ├─ Tag "Em Implantação" removida
   ├─ Tag "Em Homologação" adicionada
   └─ Campo data_de_homologacao preenchido

✅ Banco de Dados
   ├─ status_atual = "Em Homologação"
   ├─ data_mudanca_status = hoje
   └─ data_homologacao = hoje ⭐

✅ Google Sheets
   ├─ Status Principal = "Em Homologação"
   └─ Dt Homolog = DD/MM/YYYY
```

---

## 🔧 Extensibilidade

Para adicionar um novo campo sincronizado:

```python
# Em routes/api.py, função _sincronizar_custom_fields_banco()

campo_para_coluna = {
    'data_de_homologacao': 'data_homologacao',
    'data_de_onboarding': 'data_de_onboarding',
    'data_liberacao_servidor': 'data_liberacao_servidor',
    'data_de_inicio_da_implantacao': 'data_inicio_implantacao',
    'data_de_virada': 'data_virada',
    # ⭐ Adicionar novo campo aqui:
    'seu_novo_campo': 'coluna_banco',
}
```

**Pronto!** Funciona automaticamente para todas as transições. 🎉

---

**Diagrama criado em**: 13 de outubro de 2025  
**Versão**: 1.0
