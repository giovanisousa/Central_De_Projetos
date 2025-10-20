# 📋 Implementação: Ordenação por Dias na Fase

**Data:** 20/10/2025  
**Branch:** `feature/ajuste-ordenacao-e-busca`  
**Objetivo:** Ordenar cards do Kanban por dias na fase (decrescente)

---

## 🎯 Objetivo

Os cards em cada coluna do Kanban devem ser apresentados em **ordem decrescente** do campo `dias_na_fase`, priorizando projetos que estão há mais tempo na fase atual (no topo da coluna).

---

## 📊 Contexto

### Antes da Mudança
- Cards eram ordenados alfabeticamente por `nome` do projeto
- Não havia priorização visual de projetos com mais tempo na fase
- Dificultava identificar gargalos e projetos que precisam de atenção

### Depois da Mudança
- Cards ordenados por `dias_na_fase` em ordem **decrescente**
- Projetos com mais dias na fase aparecem no **topo** da coluna
- Facilita identificação imediata de projetos que precisam de atenção

---

## 🔧 Implementação Técnica

### Arquivo Modificado
`routes/api.py` - Endpoint `/api/projetos-cache/<id_do_gp>`

### Mudança Realizada

#### ❌ Código Antigo (linha ~675)
```python
for status, projetos in projetos_por_status.items():
    projetos_por_status[status] = sorted(projetos, key=lambda p: p['nome'])
```

#### ✅ Código Novo
```python
# Função auxiliar para converter dias_na_fase em número para ordenação
def extrair_dias_numericos(projeto):
    """
    Converte o valor de dias_na_fase para número para ordenação.
    - "Hoje" -> 0
    - "1d", "2d", etc -> 1, 2, etc
    - "N/D" -> -1 (vai para o final)
    - "Futuro" -> -2 (vai para o final)
    """
    dias_str = projeto.get('dias_na_fase', 'N/D')
    if dias_str == 'Hoje':
        return 0
    elif dias_str == 'N/D':
        return -1
    elif dias_str == 'Futuro':
        return -2
    elif isinstance(dias_str, str) and dias_str.endswith('d'):
        try:
            return int(dias_str[:-1])  # Remove o 'd' e converte para int
        except ValueError:
            return -1
    else:
        return -1

# Ordena cada coluna por dias_na_fase (DECRESCENTE: mais dias no topo)
for status, projetos in projetos_por_status.items():
    projetos_por_status[status] = sorted(projetos, key=extrair_dias_numericos, reverse=True)
```

---

## 🔍 Lógica de Ordenação

### Conversão de Valores

| Valor `dias_na_fase` | Valor Numérico | Ordem na Coluna |
|---------------------|----------------|-----------------|
| `"15d"` | 15 | 1º (topo) |
| `"10d"` | 10 | 2º |
| `"5d"` | 5 | 3º |
| `"1d"` | 1 | 4º |
| `"Hoje"` | 0 | 5º |
| `"N/D"` | -1 | Último |
| `"Futuro"` | -2 | Último |

### Comportamento
1. **Projetos com mais dias**: Aparecem **primeiro** (topo)
2. **Projetos recentes** ("Hoje"): Aparecem no final dos projetos válidos
3. **Projetos sem data** ("N/D"): Vão para o final
4. **Projetos futuros**: Vão para o final

---

## 📦 Fonte de Dados

### ✅ Dados do Banco de Dados
A ordenação utiliza dados **já armazenados no banco de dados local**, sem fazer novas chamadas à API do Zoho:

```python
# Busca data_mudanca_status do banco
project_row = database.get_project_by_id(projeto_id)
if project_row:
    data_mudanca_status = project_row['data_mudanca_status']

# Calcula dias_na_fase dinamicamente
dias_na_fase_calc = utils.calcular_dias_na_fase_from_status(data_mudanca_status)
```

### Campo Utilizado
- **`dias_na_fase`**: Calculado pela função `utils.calcular_dias_na_fase_from_status()`
- **Base**: Campo `data_mudanca_status` armazenado na tabela `projects`
- **Formato**: String ("Hoje", "1d", "2d", etc.)

---

## 🎨 Impacto Visual no Frontend

### Exemplo de Coluna Ordenada

**Coluna: "Em Andamento"**
```
┌─────────────────────────────────┐
│ 📦 Projeto A - Cliente X        │
│ 🕐 15d | ⏱️ 45d total          │  <- Mais tempo na fase
├─────────────────────────────────┤
│ 📦 Projeto B - Cliente Y        │
│ 🕐 10d | ⏱️ 30d total          │
├─────────────────────────────────┤
│ 📦 Projeto C - Cliente Z        │
│ 🕐 3d | ⏱️ 10d total           │
├─────────────────────────────────┤
│ 📦 Projeto D - Cliente W        │
│ 🕐 Hoje | ⏱️ 5d total          │  <- Entrou hoje na fase
└─────────────────────────────────┘
```

---

## ✅ Benefícios

### 1. **Priorização Visual Imediata**
- Projetos que precisam de atenção aparecem no topo
- Fácil identificação de gargalos

### 2. **Gestão de Tempo Eficiente**
- GPs podem focar em projetos com mais tempo na fase
- Reduz risco de projetos "esquecidos"

### 3. **Performance Mantida**
- Ordenação em memória (muito rápida)
- Sem impacto na performance da API
- Dados já estão no banco local

### 4. **Compatível com Coloração**
- A coloração por dias na fase continua funcionando
- Agora com ordenação que reforça a prioridade visual

---

## 🧪 Como Testar

### 1. **Teste Visual no Frontend**
```powershell
# Execute a aplicação
python app.py

# Acesse: http://localhost:5000
# Verifique se os cards estão ordenados por dias_na_fase (decrescente)
```

### 2. **Verificar API Diretamente**
```powershell
# Teste o endpoint (substitua o ID do GP)
curl http://localhost:5000/api/projetos-cache/2376502000000011001
```

### 3. **Casos de Teste**

| Cenário | Resultado Esperado |
|---------|-------------------|
| Coluna com projetos de 1d, 5d, 10d | Ordem: 10d → 5d → 1d |
| Projeto movido hoje para nova fase | Aparece no final da coluna (dias_na_fase = "Hoje") |
| Projeto sem data_mudanca_status | Aparece no final (dias_na_fase = "N/D") |
| Coluna com mistura de valores | Ordem: maiores dias → menores → "Hoje" → "N/D" |

---

## 📝 Notas Técnicas

### Formato do Campo `dias_na_fase`
O campo é uma **string** com os seguintes formatos possíveis:
- `"Hoje"`: Projeto mudou de status hoje
- `"1d"`, `"2d"`, `"10d"`, etc.: Número de dias + "d"
- `"N/D"`: Data não disponível
- `"Futuro"`: Data futura (caso raro)

### Função de Conversão
A função `extrair_dias_numericos()` é **local ao endpoint** e não afeta outras partes do sistema. Ela apenas converte o valor string para número para fins de ordenação.

### Ordenação Reversa
O parâmetro `reverse=True` garante ordem **decrescente**:
```python
sorted(projetos, key=extrair_dias_numericos, reverse=True)
```

---

## 🔄 Próximos Passos

- [ ] Testar ordenação em ambiente de desenvolvimento
- [ ] Validar com equipe se ordenação atende necessidade
- [ ] Considerar ordenação secundária (ex: por nome se dias iguais)
- [ ] Documentar no manual do usuário

---

## 📚 Arquivos Relacionados

- `routes/api.py` - Endpoint que retorna projetos ordenados
- `utils.py` - Função `calcular_dias_na_fase_from_status()`
- `database.py` - Armazena `data_mudanca_status`
- `templates/index.html` - Interface Kanban que exibe os cards

---

## 👨‍💻 Implementado por
**GitHub Copilot**  
Data: 20/10/2025  
Branch: `feature/ajuste-ordenacao-e-busca`
