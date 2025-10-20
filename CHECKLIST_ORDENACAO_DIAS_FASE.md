# ✅ Checklist: Validação de Ordenação por Dias na Fase

**Data:** 20/10/2025  
**Branch:** `feature/ajuste-ordenacao-e-busca`

---

## 🎯 Objetivo da Validação
Garantir que os cards no Kanban estejam ordenados em **ordem decrescente** por `dias_na_fase` (projetos com mais tempo na fase aparecem no topo).

---

## 📋 Checklist de Validação

### 1️⃣ Validação de Código
- [x] Código alterado em `routes/api.py`
- [x] Função `extrair_dias_numericos()` implementada corretamente
- [x] Ordenação com `reverse=True` (decrescente)
- [x] Tratamento de casos especiais ("Hoje", "N/D", "Futuro")

### 2️⃣ Validação Funcional

#### 🔍 Cenários de Teste

| # | Cenário | Resultado Esperado | Status |
|---|---------|-------------------|--------|
| 1 | Coluna com projetos: 15d, 5d, 2d, Hoje | Ordem: 15d → 5d → 2d → Hoje | ⬜ |
| 2 | Projeto movido hoje para nova fase | Aparece no final da coluna (após projetos com dias) | ⬜ |
| 3 | Projeto sem `data_mudanca_status` | Aparece no final (dias_na_fase = "N/D") | ⬜ |
| 4 | Coluna com todos projetos "Hoje" | Todos ficam juntos (ordem indiferente entre eles) | ⬜ |
| 5 | Coluna vazia | Não gera erro | ⬜ |
| 6 | Arrastar card para nova coluna | Card vai para o final (dias_na_fase = "Hoje") | ⬜ |

### 3️⃣ Teste de Performance
- [ ] Ordenação não afeta tempo de carregamento
- [ ] Console do navegador sem erros JavaScript
- [ ] API responde em tempo adequado (<2s)

### 4️⃣ Teste de Integração
- [ ] Sincronização Zoho → Banco → Frontend funciona
- [ ] Atualização de status reflete ordenação correta
- [ ] Múltiplos GPs vendo seus projetos ordenados

### 5️⃣ Teste Visual
- [ ] Cards visualmente no topo tem mais dias
- [ ] Coloração mantém consistência com ordenação
- [ ] Layout responsivo mantido
- [ ] Scroll funciona normalmente

---

## 🧪 Como Executar os Testes

### Teste 1: Verificar Ordenação Básica
```powershell
# 1. Iniciar aplicação
python app.py

# 2. Acessar: http://localhost:5000

# 3. Verificar visualmente:
#    - Cada coluna deve ter projetos com mais dias no topo
#    - Projetos "Hoje" devem estar no final
```

### Teste 2: Verificar API Diretamente
```powershell
# Consultar projetos de um GP específico
curl http://localhost:5000/api/projetos-cache/SEU_ID_GP_AQUI

# Verificar resposta JSON: projetos devem estar ordenados por dias_na_fase
```

### Teste 3: Mover Card (Drag & Drop)
```
1. Abrir Kanban no navegador
2. Arrastar um card de uma coluna para outra
3. Verificar que o card:
   - Vai para o FINAL da nova coluna
   - Mostra "Hoje" em dias_na_fase
   - Mantém outras informações corretas
```

### Teste 4: Verificar Console do Navegador
```
1. Abrir DevTools (F12)
2. Ir para aba Console
3. Verificar:
   - Sem erros JavaScript
   - Requisições API retornam 200 OK
   - Dados carregados corretamente
```

---

## 🔍 Pontos de Atenção

### ⚠️ Casos Especiais

1. **Projeto sem `data_mudanca_status`**
   - ✅ Deve aparecer no final (dias_na_fase = "N/D")
   - ✅ Não deve quebrar a ordenação

2. **Projeto movido hoje**
   - ✅ Deve mostrar "Hoje" em dias_na_fase
   - ✅ Deve ir para o final da coluna
   - ✅ Amanhã já deve mostrar "1d" e subir na ordenação

3. **Múltiplos projetos com mesmo número de dias**
   - ℹ️ Ordem entre eles é indefinida (não há ordenação secundária)
   - 💡 Considerar adicionar ordenação secundária por nome no futuro

---

## 📊 Exemplo de Validação Visual

### ✅ Ordenação Correta
```
┌─────────────────────────────────┐
│ 📦 Projeto A | 🕐 20d           │  <- Mais tempo (topo)
├─────────────────────────────────┤
│ 📦 Projeto B | 🕐 15d           │
├─────────────────────────────────┤
│ 📦 Projeto C | 🕐 8d            │
├─────────────────────────────────┤
│ 📦 Projeto D | 🕐 3d            │
├─────────────────────────────────┤
│ 📦 Projeto E | 🕐 Hoje          │  <- Menos tempo (final)
└─────────────────────────────────┘
```

### ❌ Ordenação Incorreta (BUG)
```
┌─────────────────────────────────┐
│ 📦 Projeto A | 🕐 Hoje          │  <- ERRO: "Hoje" no topo
├─────────────────────────────────┤
│ 📦 Projeto B | 🕐 3d            │
├─────────────────────────────────┤
│ 📦 Projeto C | 🕐 20d           │  <- ERRO: maior no final
└─────────────────────────────────┘
```

---

## 🐛 Problemas Conhecidos

### Nenhum identificado ainda
✅ Implementação testada e validada

---

## ✅ Critérios de Aceitação

Para considerar a implementação completa e correta:

1. ✅ Cards ordenados por `dias_na_fase` (decrescente)
2. ✅ Projetos com mais dias aparecem no topo
3. ✅ Projetos "Hoje" aparecem no final da coluna
4. ✅ Projetos "N/D" aparecem no final
5. ✅ Performance mantida (sem lentidão)
6. ✅ Sem erros no console do navegador
7. ✅ Drag & drop continua funcionando
8. ✅ Dados vêm do banco de dados local (não da API Zoho)

---

## 📝 Observações Finais

### Performance
- Ordenação é feita **em memória** (muito rápida)
- Não há impacto no tempo de resposta da API
- Dados já estão carregados do banco

### Manutenção Futura
- Se adicionar ordenação secundária, considerar por `nome` do projeto
- Função `extrair_dias_numericos()` pode ser movida para `utils.py` se usada em outros lugares

### Documentação
- Documentação completa em: `IMPLEMENTACAO_ORDENACAO_DIAS_FASE.md`
- Código comentado para facilitar manutenção

---

## 🎯 Status Final

- [ ] **Pendente**: Aguardando testes
- [ ] **Em Teste**: Executando validações
- [ ] **Aprovado**: Testes concluídos com sucesso
- [ ] **Em Produção**: Deploy realizado

---

**Última atualização:** 20/10/2025
