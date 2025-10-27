# 📅 Alteração de Prazo: Projetos RIS de 95 para 60 dias

**Data:** 2025-01-XX  
**Branch:** `feature/alteracao-prazos-projetos`  
**Status:** ✅ Concluído

---

## 📋 Resumo da Mudança

Alteração do prazo padrão para cálculo da data de homologação prevista de projetos **netRIS**:
- **Antes:** 95 dias corridos
- **Depois:** 60 dias corridos
- **PACS:** Mantido em 35 dias (sem alteração)

---

## 🎯 Motivação

Decisão tomada em reunião para adequar o prazo de implantação de projetos RIS à realidade operacional da equipe.

---

## 🔧 Arquivos Alterados

### 1. Código-fonte (routes/api.py)

**Linhas modificadas:** 1745-1810

#### Mudanças:
1. **Linha 1749** - Comentário atualizado:
   ```python
   # Calcula data_homologacao_prevista (60 dias corridos para netRIS, 35 para PACS)
   ```

2. **Linha 1774** - Detecção principal de RIS:
   ```python
   dias_ate_homologacao = 60  # netRIS → 60 dias
   ```

3. **Linha 1788** - Fallback por nome do projeto:
   ```python
   dias_ate_homologacao = 60  # Contém RIS → 60 dias
   ```

4. **Linha 1797** - Padrão conservador:
   ```python
   dias_ate_homologacao = 60  # Conservador → 60 dias
   ```

### 2. Documentação

#### PRAZOS_POR_PRODUTO.md
- ✅ Tabela de regras (linha 9)
- ✅ Descrição do padrão conservador (linha 23)
- ✅ Configuração JSON (linha 99)
- ✅ Exemplo de cálculo (linhas 122-127)
- ✅ Logs de debug - detecção RIS (linha 208)
- ✅ Logs de debug - fallback (linha 226)
- ✅ Checklist de validação (linhas 331, 334)

#### LEVANTAMENTO_FUNCIONALIDADES.md
- ✅ Lista de funcionalidades (linha 187)
- ✅ Regras de cálculo (linha 200)

#### CORRECAO_CAMPOS_E_DUPLICACAO.md
- ✅ Mapeamento de campos (linha 253)

#### CORRECAO_DATA_VIRADA_FMT.md
- ✅ Teste de validação (linha 161)

---

## 📊 Impacto nos Cálculos

### Exemplo Prático:

**Data de Início:** 20/10/2025 (segunda-feira)

#### Antes (95 dias):
- 20/10 + 95 dias = 23/01/2026 (sexta)
- Ajuste para segunda = 27/01/2026
- Virada (+7 dias) = 03/02/2026 (segunda)

#### Depois (60 dias):
- 20/10 + 60 dias = 19/12/2025 (sexta)
- Ajuste para segunda = 22/12/2025
- Virada (+7 dias) = 29/12/2025 (segunda)

**Diferença:** ~35 dias a menos no cronograma total

---

## 🎨 Impacto Visual

### Indicador de Proximidade
A feature de destaque visual para projetos próximos à homologação continua funcionando:
- **RIS:** Destaque quando faltarem ≤ 30 dias
- **PACS:** Destaque quando faltarem ≤ 15 dias

### Contador Regressivo
- Badge verde: dias restantes > 0
- Badge vermelho: dias restantes < 0 (em atraso)

---

## 📅 Google Calendar

Os eventos criados automaticamente no Google Calendar usarão as novas datas:
- **Evento de Homologação:** Calculado com 60 dias (RIS)
- **Evento de Virada:** Homologação + 7 dias
- **Duração:** Segunda a sexta (5 dias)

---

## ⚠️ Pontos de Atenção

### Projetos em Andamento
- Projetos já agendados com o prazo de 95 dias **NÃO serão afetados**
- As datas já calculadas permanecem as mesmas
- Apenas novos agendamentos usarão 60 dias

### Dados Históricos
- Banco de dados mantém registros com as datas antigas
- Não há migração automática de datas existentes
- Relatórios históricos refletem os prazos vigentes na época

### Testes Necessários
- [ ] Agendar nova implantação de projeto RIS
- [ ] Verificar cálculo de data_homologacao_prevista
- [ ] Verificar cálculo de data_virada_prevista
- [ ] Confirmar eventos no Google Calendar
- [ ] Validar indicador visual de proximidade
- [ ] Verificar contador regressivo

---

## 🔍 Validação

### Comando para Buscar Referências ao Prazo Antigo:
```powershell
# Buscar "95 dias" em arquivos de documentação
grep -r "95 dias" *.md

# Buscar padrão "95" próximo a palavras-chave
grep -rE "\b95\b.{0,30}(dia|prazo|RIS|homolog)" *.md *.py
```

**Resultado esperado:** Nenhuma ocorrência (todas atualizadas)

---

## 📝 Checklist de Implementação

- [x] Atualizar código em `routes/api.py`
- [x] Atualizar `PRAZOS_POR_PRODUTO.md`
- [x] Atualizar `LEVANTAMENTO_FUNCIONALIDADES.md`
- [x] Atualizar `CORRECAO_CAMPOS_E_DUPLICACAO.md`
- [x] Atualizar `CORRECAO_DATA_VIRADA_FMT.md`
- [x] Validar que não há mais referências a "95 dias"
- [ ] Testar em ambiente de desenvolvimento
- [ ] Testar em ambiente de homologação
- [ ] Validar com equipe de implantação
- [ ] Deploy em produção

---

## 🚀 Próximos Passos

1. **Teste Local:**
   - Executar aplicação localmente
   - Agendar implantação de projeto RIS de teste
   - Verificar logs de debug no terminal
   - Confirmar datas calculadas

2. **Validação de UI:**
   - Verificar modal de agendamento
   - Confirmar campos de data preenchidos
   - Validar indicador visual
   - Testar contador regressivo

3. **Deploy:**
   - Merge para branch principal
   - Deploy em homologação
   - Testes com dados reais
   - Deploy em produção

---

## 📞 Contato

Em caso de dúvidas ou problemas relacionados a esta alteração, verificar:
1. Logs de debug no console (buscar por `[DEBUG][INICIAR_IMPLANTACAO]`)
2. Validar produtos_contratados no banco de dados
3. Conferir se o projeto tem "netRIS" ou "RIS" no nome/produtos
