# ✅ Checklist de Testes: Movimentação para "Em Homologação"

**Data**: 13 de outubro de 2025  
**Feature**: Ações automáticas ao mover card para "Em Homologação"

---

## 🎯 Objetivo do Teste

Validar que todas as ações automáticas são executadas corretamente quando um projeto é movido para a coluna "Em Homologação" no dashboard Kanban.

---

## 📋 Pré-requisitos

### ✅ Preparação do Ambiente
- [ ] Servidor Flask rodando (`python app.py`)
- [ ] Navegador aberto em `http://localhost:5000`
- [ ] Usuário autenticado com Google
- [ ] Acesso ao console do navegador (F12 → Console)
- [ ] Acesso ao console do backend (terminal onde rodou `python app.py`)

### ✅ Preparação do Projeto de Teste
- [ ] Projeto existe na coluna **"Em Andamento - Implantação"**
- [ ] Projeto possui a tag **"Em Implantação"** no Zoho Projects
- [ ] Coluna **"Dt Homolog"** está vazia na Planilha Principal
- [ ] Campo **"data_de_homologacao"** está vazio no Zoho Projects

---

## 🧪 Execução do Teste

### Passo 1: Preparação
1. [ ] Abrir o Zoho Projects no navegador
2. [ ] Localizar o projeto de teste
3. [ ] **Anotar**:
   - Nome do projeto: ____________________________
   - ID do projeto: ____________________________
   - Tags atuais: ____________________________
   - Campo "data_de_homologacao": ____________________________

4. [ ] Abrir a Planilha Principal do Google Sheets
5. [ ] Localizar a linha do projeto
6. [ ] **Anotar**:
   - Status Principal atual: ____________________________
   - Valor da coluna "Dt Homolog": ____________________________

### Passo 2: Executar Movimentação
1. [ ] No dashboard Kanban, localizar o card do projeto
2. [ ] Verificar que está na coluna **"Em Andamento - Implantação"**
3. [ ] **Arrastar o card** para a coluna **"Em Homologação"**
4. [ ] Aguardar confirmação visual (card se move para nova coluna)
5. [ ] Observar se badge "dias_na_fase" atualiza para **"Hoje"**

### Passo 3: Verificar Logs do Backend
Procurar no console do backend por:
```
[MOVE][DB] Projeto ...: data_mudanca_status = 2025-10-13
[DEBUG][SHEET] Processando onTransition para 'Em Andamento - Implantação' -> 'Em Homologação'
[DEBUG][SHEET] Atualizando coluna 'Dt Homolog' para '13/10/2025'
[DEBUG][SHEET] Coluna 'Dt Homolog' atualizada com sucesso
```

- [ ] Log de atualização do banco encontrado
- [ ] Log de processamento do onTransition encontrado
- [ ] Log de atualização da coluna "Dt Homolog" encontrado
- [ ] Sem erros nos logs

### Passo 4: Verificar Console do Navegador
Procurar por:
```javascript
[CARD UPDATE] Atualizando card ... com novos dados
Badge atualizado para: Hoje
```

- [ ] Log de atualização do card encontrado
- [ ] Badge atualizado para "Hoje"
- [ ] Sem erros de JavaScript

---

## ✅ Validações

### 1. Zoho Projects

#### Tags
Acessar o projeto no Zoho Projects e verificar:
- [ ] Tag **"Em Implantação"** foi **removida** ❌
- [ ] Tag **"Em Homologação"** foi **adicionada** ✅
- [ ] Nenhuma outra tag foi alterada

#### Campo Customizado "Data de Homologação"
- [ ] Campo **"data_de_homologacao"** foi preenchido
- [ ] Valor está no formato: **YYYY-MM-DD** (ex: `2025-10-13`)
- [ ] Data corresponde à data atual

#### Status
- [ ] Status permanece como **"Em Andamento"**

### 2. Planilha Principal do Google Sheets

Abrir a planilha e localizar a linha do projeto:
- [ ] Coluna **"Status Principal"** = **"Em Homologação"** ✅
- [ ] Coluna **"Dt Homolog"** = **data atual** no formato `DD/MM/YYYY` (ex: `13/10/2025`) ✅
- [ ] Outras colunas não foram alteradas indevidamente

### 3. Banco de Dados Local ⭐ **ATUALIZADO**

No console do backend, executar:
```python
import database
project = database.get_project_by_id("SEU_PROJECT_ID")
print(f"Status atual: {project['status_atual']}")
print(f"Data mudança: {project['data_mudanca_status']}")
print(f"Data homologação: {project['data_homologacao']}")  # ⭐ NOVO
```

- [ ] `status_atual` = **"Em Homologação"**
- [ ] `data_mudanca_status` = **data atual** (formato: `YYYY-MM-DD`)
- [ ] `data_homologacao` = **data atual** (formato: `YYYY-MM-DD`) ⭐ **NOVO**

### 4. Interface do Dashboard

- [ ] Card está visualmente na coluna **"Em Homologação"**
- [ ] Badge "dias_na_fase" mostra **"Hoje"** (cor: verde/azul)
- [ ] Nome do cliente está correto
- [ ] Outras informações do card estão corretas

---

## 🔍 Testes Adicionais

### Teste de Persistência (Opcional)
1. [ ] Atualizar a página (F5)
2. [ ] Card permanece na coluna "Em Homologação"
3. [ ] Badge "dias_na_fase" continua mostrando "Hoje"
4. [ ] Dados no Zoho e Planilha permanecem corretos

### Teste no Dia Seguinte (Opcional)
1. [ ] Aguardar até o dia seguinte (14/10/2025)
2. [ ] Acessar o dashboard
3. [ ] Badge "dias_na_fase" deve mostrar **"1d"**
4. [ ] Campo "data_de_homologacao" no Zoho continua com **13/10/2025**

---

## 📸 Evidências (Opcional)

### Screenshots Recomendados
1. [ ] Card antes da movimentação (coluna "Em Andamento - Implantação")
2. [ ] Card depois da movimentação (coluna "Em Homologação" com badge "Hoje")
3. [ ] Tags no Zoho Projects após movimentação
4. [ ] Campo "data_de_homologacao" preenchido no Zoho
5. [ ] Colunas atualizadas na Planilha Principal
6. [ ] Logs do backend confirmando as operações

---

## ❌ Problemas Encontrados

### Problema 1: _________________________________
**Descrição**: ___________________________________________  
**Logs**:
```
[Cole os logs relevantes aqui]
```
**Resolvido**: [ ] Sim [ ] Não  
**Solução**: ___________________________________________

### Problema 2: _________________________________
**Descrição**: ___________________________________________  
**Logs**:
```
[Cole os logs relevantes aqui]
```
**Resolvido**: [ ] Sim [ ] Não  
**Solução**: ___________________________________________

---

## 📊 Resultado Geral

### Status do Teste
- [ ] ✅ **APROVADO** - Todas as validações passaram
- [ ] ⚠️ **APROVADO COM RESSALVAS** - Alguns problemas menores encontrados
- [ ] ❌ **REPROVADO** - Problemas críticos encontrados

### Resumo
- **Data do teste**: _______________
- **Testador**: _______________
- **Projeto testado**: _______________
- **Total de validações**: 20+
- **Validações aprovadas**: _____ / 20+
- **Problemas encontrados**: _____

### Observações Finais
```
[Adicione aqui qualquer observação relevante sobre o teste]
```

---

## 🚀 Próximos Passos

### Se o teste passou:
- [ ] Testar com mais 2-3 projetos diferentes
- [ ] Validar em produção
- [ ] Documentar sucesso no JIRA/sistema de gestão
- [ ] Comunicar à equipe que feature está pronta

### Se o teste falhou:
- [ ] Analisar logs detalhadamente
- [ ] Reportar problemas ao desenvolvedor
- [ ] Aguardar correções
- [ ] Executar teste novamente

---

## 📞 Contatos

**Em caso de problemas técnicos:**
- Verificar documentação: `FEATURE_EM_HOMOLOGACAO.md`
- Consultar resumo: `RESUMO_EM_HOMOLOGACAO.md`
- Verificar índice: `INDICE_FUNCIONALIDADES.md`

**Checklist criado por**: GitHub Copilot  
**Versão**: 1.0  
**Data**: 13/10/2025
