# 🚀 Guia Rápido - Google Calendar

## 📝 Resumo

Ao clicar em **"Agendar Implantação"**, o sistema agora cria automaticamente **2 eventos** no Google Calendar da equipe:

1. 📅 **Homologação {Cliente} (Remoto/Presencial)** → Segunda a Sexta da semana de homologação
2. 📅 **Virada {Cliente} (Remoto/Presencial)** → Segunda a Sexta da semana de virada

---

## ⚡ Uso Rápido

### No Frontend (Modal de Agendamento)

1. Usuário clica em "Agendar Implantação"
2. Preenche os campos:
   - Data de início
   - Implantador RIS
   - Implantador PACS
3. Clica em "Confirmar"

### No Backend (Automático)

```
✅ Calcula datas de homologação e virada
✅ Atualiza Zoho Projects
✅ Atualiza Planilha Google
✅ Processa tarefas
✅ 🆕 Cria eventos no Google Calendar ← NOVO!
✅ Sincroniza banco local
```

### Resultado

O usuário recebe mensagem de sucesso com os detalhes:

```
✅ Implantação iniciada com sucesso!

Detalhes:
- Campo customizado atualizado
- Planilha atualizada
- 15 tarefas atribuídas aos implantadores
- 📅 Eventos criados no Google Calendar:
  • Homologação: abc123def456
  • Virada: xyz789ghi012
```

---

## 📋 Configuração Inicial

### 1. Verificar Calendar ID

**Arquivo:** `config.py`

```python
GOOGLE_CALENDAR_ID = "animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com"
```

### 2. Verificar Scope de Calendar

**Arquivo:** `config.py`

```python
SCOPES_GOOGLE = [
    # ... outros scopes ...
    'https://www.googleapis.com/auth/calendar',  # ← Deve estar presente
]
```

### 3. Re-autenticar (Se Necessário)

Se os eventos não forem criados:

1. Fazer logout no sistema
2. Fazer login novamente
3. Aceitar permissões do Google Calendar

---

## 🔍 Verificação Rápida

### Testar Módulo

```bash
python test_google_calendar.py
```

**Saída esperada:**
```
🎉 TODOS OS TESTES PASSARAM! 🎉
✅ Testes executados: 18
✅ Sucessos: 18
```

### Logs no Console

Procurar por:

```
[INFO][INICIAR_IMPLANTACAO] ===== ETAPA 4: CRIANDO EVENTOS NO GOOGLE CALENDAR =====
[SUCCESS][INICIAR_IMPLANTACAO] Eventos criados com sucesso no Google Calendar
```

---

## 📅 Exemplos

### Exemplo 1: Segunda-feira (Padrão)

**Entrada:**
- Data início: 20/10/2025 (Segunda)
- Cliente: Hospital XYZ - NR 001

**Nome extraído:** Hospital XYZ ✨ (código removido automaticamente)

**Eventos:**
- Homologação: 20/10 a 24/10 (Seg-Sex) 🟡
- Virada: 27/10 a 31/10 (Seg-Sex) 🔴

### Exemplo 2: Quarta-feira (Meio da Semana)

**Entrada:**
- Data início: 22/10/2025 (Quarta)
- Cliente: Clínica ABC - AP 002

**Nome extraído:** Clínica ABC ✨ (código removido automaticamente)

**Eventos:**
- Homologação: 22/10 a 24/10 (Qua-Sex) 🟡
- Virada: 29/10 a 31/10 (Qua-Sex) 🔴

---

## 🛠️ Troubleshooting

### Problema: "Insufficient Permission"

**Solução:**
1. Logout do sistema
2. Login novamente
3. Aceitar permissões de Calendar

### Problema: Eventos não aparecem

**Verificar:**
1. Calendar ID está correto?
2. Usuário tem acesso ao calendário compartilhado?
3. Logs mostram sucesso?

### Problema: Datas erradas

**Verificar:**
1. Executar testes: `python test_google_calendar.py`
2. Verificar timezone: `America/Sao_Paulo`

---

## 📞 Contato

**Dúvidas?** Consulte a documentação completa em:
- 📄 `INTEGRACAO_GOOGLE_CALENDAR.md`

**Problemas?** Verifique os logs:
- 🔍 Procure por `[GOOGLE_CALENDAR]` nos logs do backend
- 🔍 Verifique `[INICIAR_IMPLANTACAO]` para fluxo completo
