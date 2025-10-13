# Debug: Logs Detalhados para Atualização de Card

**Data:** 13/10/2025  
**Status:** 🔍 DEBUGGING

---

## 🎯 Objetivo

Adicionar logs detalhados para entender por que o card não está sendo atualizado imediatamente após a movimentação.

---

## 📝 Logs Adicionados

### Console do Navegador

A função `enviarMovimentoParaServidor()` agora exibe logs detalhados em cada etapa:

```javascript
// 1. Envio da requisição
[enviarMovimentoParaServidor] Enviando... {projetoId, colunaOrigem, colunaDestino, clienteSheet}

// 2. Resposta HTTP recebida
[enviarMovimentoParaServidor] HTTP 200 body: {...}

// 3. Parse do JSON
[enviarMovimentoParaServidor] Resposta parseada: {...}

// 4. Verificação de sucesso
[enviarMovimentoParaServidor] ✅ Sucesso! dados_atualizados: {...}

// 5. Busca do card no DOM
[enviarMovimentoParaServidor] Buscando card com ID: 2376502000003549073
[enviarMovimentoParaServidor] Card encontrado: <div class="kanban-card">

// 6. Busca do badge
[enviarMovimentoParaServidor] Badge encontrado: <span class="dias-badge">

// 7. Atualização do badge
[enviarMovimentoParaServidor] Atualizando badge de "5d" para "Hoje"

// 8. Confirmação final
[enviarMovimentoParaServidor] ✅ Card atualizado! dias_fase="Hoje" data_mudanca="2025-10-13"
```

### Logs de Erro (caso algo falhe)

```javascript
// Se JSON inválido
[enviarMovimentoParaServidor] Erro ao parsear JSON: SyntaxError...

// Se sucesso = false
[enviarMovimentoParaServidor] ❌ Falha: {erro: "..."}

// Se card não encontrado
[enviarMovimentoParaServidor] ⚠️ Card não encontrado no DOM

// Se badge não encontrado
[enviarMovimentoParaServidor] ⚠️ Badge não encontrado no card

// Se dados_atualizados não presente
[enviarMovimentoParaServidor] ⚠️ dados_atualizados não presente na resposta

// Se exceção
[enviarMovimentoParaServidor] ❌ Exceção: Error...
```

---

## 🧪 Como Testar Agora

### 1. Limpar Console do Navegador
- Pressione **F12** para abrir DevTools
- Na aba **Console**, clique no ícone 🚫 para limpar logs antigos

### 2. Mover um Card
- Arraste um card de uma coluna para outra
- Exemplo: "Aguardando Onboarding" → "Falta Liberar Servidor Infra"

### 3. Observar Logs no Console

Você deve ver uma sequência de logs como:

```
[enviarMovimentoParaServidor] Enviando... 
  {projetoId: "2376502000003549073", colunaOrigem: "Aguardando Onboarding", ...}

[enviarMovimentoParaServidor] HTTP 200 body: {"sucesso":true,"mensagem":"...","dados_atualizados":{...}}

[enviarMovimentoParaServidor] Resposta parseada: 
  {sucesso: true, mensagem: "...", dados_atualizados: {...}}

[enviarMovimentoParaServidor] ✅ Sucesso! dados_atualizados: 
  {dias_na_fase: "Hoje", data_mudanca_status: "2025-10-13", status_atual: "Falta Liberar..."}

[enviarMovimentoParaServidor] Buscando card com ID: 2376502000003549073

[enviarMovimentoParaServidor] Card encontrado: 
  <div class="kanban-card" data-id="2376502000003549073">...</div>

[enviarMovimentoParaServidor] Badge encontrado: 
  <span class="dias-badge">5d</span>

[enviarMovimentoParaServidor] Atualizando badge de "5d" para "Hoje"

[enviarMovimentoParaServidor] ✅ Card atualizado! dias_fase="Hoje" data_mudanca="2025-10-13"
```

### 4. Verificar Visualmente

- O badge do card deve exibir **"Hoje"** ✅
- A cor deve ser **verde** (dentro do SLA)

---

## 🔍 O Que Procurar nos Logs

### Cenário 1: Backend não retorna `dados_atualizados`

**Log esperado:**
```
[enviarMovimentoParaServidor] ⚠️ dados_atualizados não presente na resposta
```

**Solução:** Verificar se o endpoint `/api/mover_projeto` está retornando o campo `dados_atualizados`

---

### Cenário 2: Card não encontrado no DOM

**Log esperado:**
```
[enviarMovimentoParaServidor] ⚠️ Card não encontrado no DOM
```

**Possíveis causas:**
- Card foi removido do DOM antes da resposta chegar
- Atributo `data-id` não corresponde ao `projetoId`
- Card está em uma coluna diferente após animação

---

### Cenário 3: Badge não encontrado no card

**Log esperado:**
```
[enviarMovimentoParaServidor] ⚠️ Badge não encontrado no card
```

**Possíveis causas:**
- Classe `.dias-badge` não existe no HTML do card
- Badge foi removido durante renderização
- HTML do card mudou após atualização recente

---

### Cenário 4: Erro HTTP

**Log esperado:**
```
[enviarMovimentoParaServidor] HTTP 500 body: {...}
[enviarMovimentoParaServidor] ❌ Falha: {erro: "..."}
```

**Solução:** Verificar logs do servidor Flask no terminal

---

## 📊 Checklist de Diagnóstico

Execute este passo a passo e anote os resultados:

- [ ] **Passo 1:** Abrir DevTools (F12) e ir para Console
- [ ] **Passo 2:** Limpar console (🚫)
- [ ] **Passo 3:** Mover um card
- [ ] **Passo 4:** Verificar se aparece log: `[enviarMovimentoParaServidor] Enviando...`
  - ❌ Se NÃO: Problema na captura do evento de drop
  - ✅ Se SIM: Continuar
  
- [ ] **Passo 5:** Verificar se aparece log: `[enviarMovimentoParaServidor] HTTP 200`
  - ❌ Se NÃO ou HTTP 500: Problema no backend
  - ✅ Se SIM: Continuar
  
- [ ] **Passo 6:** Verificar se aparece log: `[enviarMovimentoParaServidor] Resposta parseada:`
  - ❌ Se aparecer erro de parse: JSON inválido do backend
  - ✅ Se SIM: Continuar
  
- [ ] **Passo 7:** Verificar se aparece log: `✅ Sucesso! dados_atualizados:`
  - ❌ Se NÃO: Backend não retornou `sucesso: true` ou `dados_atualizados`
  - ✅ Se SIM: Continuar
  
- [ ] **Passo 8:** Verificar se aparece log: `Card encontrado:`
  - ❌ Se aparecer "não encontrado": Card não está no DOM
  - ✅ Se SIM: Continuar
  
- [ ] **Passo 9:** Verificar se aparece log: `Badge encontrado:`
  - ❌ Se aparecer "não encontrado": Badge não existe no card
  - ✅ Se SIM: Continuar
  
- [ ] **Passo 10:** Verificar se aparece log: `Atualizando badge de ... para "Hoje"`
  - ✅ Se SIM: Atualização deve estar funcionando!
  
- [ ] **Passo 11:** Verificar visualmente se badge exibe "Hoje"
  - ❌ Se NÃO: CSS pode estar sobrescrevendo ou bug na aplicação de cor
  - ✅ Se SIM: **FUNCIONOU!** 🎉

---

## 📋 Próximos Passos Baseado nos Resultados

### Se TUDO funcionar (todos os logs aparecem + badge mostra "Hoje")
✅ Implementação correta! Pode fazer commit:
```bash
git add .
git commit -m "feat: atualiza dias_fase imediatamente após mover card"
```

### Se backend não retornar `dados_atualizados`
🔧 Verificar `routes/api.py` linha ~870-885

### Se card não for encontrado
🔧 Verificar se `data-id` está correto no HTML do card

### Se badge não for encontrado
🔧 Verificar se classe `.dias-badge` existe no card

### Se nenhum log aparecer
🔧 Verificar se a função está sendo chamada corretamente

---

## 🚀 Servidor Status

✅ Servidor reiniciado em: http://127.0.0.1:5000  
✅ Logs detalhados ativados no frontend  
✅ Pronto para teste

**Aguardando resultados dos testes...**
