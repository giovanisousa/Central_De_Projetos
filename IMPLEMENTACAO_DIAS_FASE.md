# ✅ Implementação Concluída: Sistema de Dias na Fase

## 🎯 Objetivo
Implementar um sistema preciso de contagem de dias que um projeto permanece em cada fase/status do Kanban.

## 🔑 Solução Implementada: Campo Calculado Dinamicamente

### **Abordagem Escolhida:**
- ✅ **`data_mudanca_status`**: Campo no banco que armazena a data da última mudança de status
- ✅ **`dias_na_fase`**: Calculado SEMPRE em tempo real (não armazenado)
- ✅ Sem necessidade de jobs/cron para atualização
- ✅ Sempre preciso e atualizado

### **Como Funciona:**
```python
# Hoje moveu projeto → data_mudanca_status = 2025-10-13
# Hoje acessa painel → (2025-10-13 - 2025-10-13) = 0 dias → "Hoje"
# Amanhã acessa → (2025-10-14 - 2025-10-13) = 1 dia → "1d"
# Depois acessa → (2025-10-15 - 2025-10-13) = 2 dias → "2d"
```

---

## 📝 Mudanças Realizadas

### 1. **Migration do Banco de Dados** (`database.py`)
```sql
ALTER TABLE projects ADD COLUMN data_mudanca_status TEXT
```
- ✅ Novo campo criado
- ✅ Inicializado com `data_inicio` ou `data_criacao` para projetos existentes
- ✅ Migration executada automaticamente no `init_db()`

### 2. **Proteção contra Sobrescrita** (`database.py` - `upsert_project()`)
```python
'data_mudanca_status': None,  # Não sobrescreve se já existe

# SQL Update protegido:
data_mudanca_status = COALESCE(projects.data_mudanca_status, excluded.data_mudanca_status)
```
- ✅ `data_mudanca_status` **NÃO É SOBRESCRITA** em sincronizações do Zoho
- ✅ Apenas atualizada manualmente ao mover card

### 3. **Nova Função de Cálculo** (`utils.py`)
```python
def calcular_dias_na_fase_from_status(data_mudanca_status: str) -> str:
    """
    Calcula dias na fase baseado na data_mudanca_status.
    
    Returns:
        "Hoje", "1d", "2d", etc. ou "N/D"
    """
    if not data_mudanca_status:
        return 'N/D'
    
    data_base = _parse_date_any(data_mudanca_status)
    hoje = date.today()
    dias = (hoje - data_base).days
    
    if dias < 0:
        return 'Futuro'
    elif dias == 0:
        return 'Hoje'
    else:
        return f"{dias}d"
```
- ✅ Função limpa e precisa
- ✅ Sempre calcula em tempo real
- ✅ Sem dependência de datas específicas de cada fase

### 4. **Atualização Imediata ao Mover Card** (`routes/api.py` - `/mover_projeto`)
```python
# ========================================
# ATUALIZAÇÃO CRÍTICA: data_mudanca_status
# ========================================
data_atual = date.today().strftime('%Y-%m-%d')
cursor.execute(
    "UPDATE projects SET data_mudanca_status = ?, status_atual = ? WHERE id = ?",
    (data_atual, coluna_destino, projeto_id)
)
```
- ✅ `data_mudanca_status` atualizada **IMEDIATAMENTE** ao mover card
- ✅ Executada **ANTES** de qualquer sincronização
- ✅ Garantia de precisão

### 5. **Sincronização Simplificada** (`routes/api.py` - `_sincronizar_db_local()`)
```python
def _sincronizar_db_local(projeto_id: str, access_token: str, coletor_mensagens: list):
    """
    IMPORTANTE: data_mudanca_status já foi atualizada ANTES desta função,
    então a sincronização do Zoho não deve sobrescrevê-la (protegida em upsert_project).
    """
    # Apenas sincroniza - não toca em data_mudanca_status
    project_updated = synchronize_single_project(projeto_id, access_token)
```
- ✅ Removida complexidade desnecessária
- ✅ Confia na proteção do `upsert_project()`
- ✅ Mais confiável e simples

### 6. **Endpoint de Consulta Otimizado** (`routes/api.py` - `/dias-na-fase/<id>`)
```python
@api_bp.route('/dias-na-fase/<project_id>', methods=['GET'])
def api_dias_na_fase(project_id):
    """
    Calcula SEMPRE em tempo real a partir de data_mudanca_status.
    Cache apenas para evitar múltiplas queries ao banco (TTL: 5s).
    """
    # Busca data_mudanca_status do banco
    project_row = database.get_project_by_id(project_id)
    data_mudanca = project_row.get('data_mudanca_status')
    
    # Calcula em tempo real
    valor = utils.calcular_dias_na_fase_from_status(data_mudanca)
    
    return jsonify({
        "project_id": project_id,
        "dias_na_fase": valor,
        "data_mudanca_status": data_mudanca
    })
```
- ✅ Cache mínimo (5s) apenas para queries ao banco
- ✅ Valor calculado SEMPRE em tempo real
- ✅ Retorna também `data_mudanca_status` para debug

### 7. **Cálculo no Carregamento** (`routes/api.py` - `/carregar_projetos`)
```python
# Busca data_mudanca_status do banco
project_row = database.get_project_by_id(projeto_id)
data_mudanca_status = project_row.get('data_mudanca_status')

# Calcula dinamicamente
dias_na_fase_calc = utils.calcular_dias_na_fase_from_status(data_mudanca_status)

info_projeto = {
    # ...
    'dias_na_fase': dias_na_fase_calc,  # ✅ Calculado dinamicamente
    # ...
}
```
- ✅ Cada projeto tem dias_na_fase calculado ao carregar
- ✅ Sempre atualizado, mesmo sem reload da página

---

## 🔄 Fluxo Completo

### **Cenário: Usuário move card de "Em Andamento" para "Em Homologação"**

1. **Frontend** envia requisição POST para `/api/mover_projeto`
   ```json
   {
     "projeto_id": "123",
     "coluna_origem": "Em Andamento",
     "coluna_destino": "Em Homologação",
     "cliente_sheet": "Cliente XYZ"
   }
   ```

2. **Backend atualiza `data_mudanca_status` IMEDIATAMENTE**
   ```sql
   UPDATE projects 
   SET data_mudanca_status = '2025-10-13', 
       status_atual = 'Em Homologação' 
   WHERE id = '123'
   ```
   - ✅ `data_mudanca_status` = `2025-10-13`
   - ✅ `status_atual` = `Em Homologação`

3. **Backend atualiza Zoho** (status/tags via API)

4. **Backend atualiza Planilha Google Sheets**

5. **Backend sincroniza do Zoho**
   - Busca dados atualizados do Zoho
   - `upsert_project()` **NÃO sobrescreve** `data_mudanca_status`
   - Outros campos são atualizados normalmente

6. **Frontend recebe resposta de sucesso**

7. **Frontend busca dias_na_fase atualizado**
   ```javascript
   fetch(`/api/dias-na-fase/123`)
   // Retorna: { "dias_na_fase": "Hoje" }
   ```

8. **Amanhã (2025-10-14), usuário acessa o painel:**
   ```javascript
   fetch(`/api/dias-na-fase/123`)
   // Calcula: (2025-10-14 - 2025-10-13) = 1 dia
   // Retorna: { "dias_na_fase": "1d" }
   ```

9. **Depois de amanhã (2025-10-15):**
   ```javascript
   fetch(`/api/dias-na-fase/123`)
   // Calcula: (2025-10-15 - 2025-10-13) = 2 dias
   // Retorna: { "dias_na_fase": "2d" }
   ```

---

## ✅ Garantias da Implementação

### **1. Precisão**
- ✅ `data_mudanca_status` atualizada atomicamente ao mover card
- ✅ Cálculo sempre baseado na data correta
- ✅ Sem race conditions

### **2. Performance**
- ✅ Cálculo muito rápido (subtração de datas)
- ✅ Cache de 5s para queries ao banco (evita sobrecarga)
- ✅ Não impacta UX

### **3. Confiabilidade**
- ✅ Campo protegido contra sobrescrita
- ✅ Migration automática para projetos existentes
- ✅ Fallback para "N/D" se data não disponível

### **4. Manutenibilidade**
- ✅ Código limpo e bem documentado
- ✅ Lógica centralizada em funções específicas
- ✅ Fácil debug e auditoria

---

## 🧪 Como Testar

### **Teste 1: Verificar Migration**
```python
python app.py
# Saída esperada:
# "Migração: Coluna 'data_mudanca_status' adicionada à tabela projects"
# "Migração: Coluna 'data_mudanca_status' inicializada para projetos existentes"
```

### **Teste 2: Mover Card e Verificar**
1. Acesse o painel Kanban
2. Mova um card de coluna
3. Verifique console do navegador:
   ```
   [enviarMovimentoParaServidor] Enviando...
   ✅ Data de mudança de status atualizada para 2025-10-13
   ```
4. Recarregue a página
5. Verifique que `dias_na_fase` mostra "Hoje"

### **Teste 3: Verificar Cálculo Dinâmico**
1. No dia seguinte, acesse o painel
2. Verifique que `dias_na_fase` mostra "1d" automaticamente
3. Sem necessidade de sincronização manual

### **Teste 4: Verificar API Diretamente**
```bash
curl http://localhost:5000/api/dias-na-fase/2376502000005544019
```
Resposta esperada:
```json
{
  "project_id": "2376502000005544019",
  "dias_na_fase": "Hoje",
  "data_mudanca_status": "2025-10-13"
}
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto | ❌ Antes | ✅ Depois |
|---------|---------|----------|
| **Precisão** | Baseado em datas de fases específicas (pode estar errado) | Baseado em `data_mudanca_status` (sempre correto) |
| **Atualização** | Dependia de sincronização completa | Atualizado imediatamente ao mover |
| **Race Condition** | Sim (sync sobrescrevia valores) | Não (campo protegido) |
| **Performance** | Cache de 90s com valor estático | Cálculo dinâmico rápido |
| **Manutenção** | Complexo (várias datas para gerenciar) | Simples (uma única fonte de verdade) |
| **Confiabilidade** | Baixa (dependia de múltiplos fatores) | Alta (lógica direta) |

---

## 📌 Próximos Passos (Opcional)

1. **Adicionar índice no banco** (se performance for crítica):
   ```sql
   CREATE INDEX idx_data_mudanca_status ON projects(data_mudanca_status);
   ```

2. **Adicionar auditoria de mudanças**:
   - Criar tabela `historico_mudancas_status`
   - Registrar todas as movimentações
   - Permitir rastreamento completo

3. **Dashboard de métricas**:
   - Tempo médio em cada fase
   - Projetos com mais tempo em cada fase
   - Alertas para projetos "travados"

---

## 🎉 Conclusão

A implementação está **completa e funcional**. O sistema agora:

- ✅ **Zera** `dias_na_fase` ao mover card (mostra "Hoje")
- ✅ **Incrementa** automaticamente a cada dia que passa
- ✅ **Não requer** manutenção ou jobs programados
- ✅ **É preciso** e confiável
- ✅ **É performático** e escalável

**Status:** 🟢 PRONTO PARA PRODUÇÃO

---

**Documento gerado em:** 13/10/2025  
**Implementado por:** Análise e Desenvolvimento Automatizado  
**Branch:** `feature/datas-banco-de-dados`
