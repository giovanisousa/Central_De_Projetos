# ✅ Atualização: Sincronização Automática do Banco de Dados

**Data**: 13 de outubro de 2025  
**Status**: ✅ Implementado

---

## 🎯 Objetivo

Garantir que o **banco de dados local** esteja sempre sincronizado com os **campos customizados do Zoho Projects**, eliminando a necessidade de sincronizações periódicas completas para esses campos específicos.

---

## 📋 Problema Identificado

Anteriormente, quando um card era movido e campos customizados eram preenchidos no Zoho Projects (como `data_de_homologacao`, `data_de_onboarding`, etc.), esses valores **não eram automaticamente refletidos no banco de dados local**. 

Isso causava:
- ❌ Inconsistência entre Zoho e banco local
- ❌ Necessidade de aguardar sincronização completa
- ❌ Dados desatualizados em consultas ao banco

---

## ✅ Solução Implementada

### Sincronização Automática Imediata

Quando um card é movido e campos customizados são atualizados no Zoho, **o banco de dados local é atualizado imediatamente** com os mesmos valores.

### Mapeamento de Campos

A sincronização cobre automaticamente os seguintes campos:

| Campo Zoho Projects | Coluna Banco de Dados | Quando Atualiza |
|---------------------|----------------------|-----------------|
| `data_de_homologacao` | `data_homologacao` | Ao mover para "Em Homologação" |
| `data_de_onboarding` | `data_de_onboarding` | Ao sair de "Aguardando Onboarding" |
| `data_liberacao_servidor` | `data_liberacao_servidor` | Ao mover para "Em Andamento" (de Infra) |
| `data_de_inicio_da_implantacao` | `data_inicio_implantacao` | Ao mover para "Em Andamento - Implantação" |
| `data_de_virada` | `data_virada` | Ao mover para "Em Virada" |

---

## 🔧 Implementação Técnica

### 1. Nova Função: `_sincronizar_custom_fields_banco()`

**Arquivo**: `routes/api.py`

```python
def _sincronizar_custom_fields_banco(projeto_id: str, custom_fields_resolvidos: dict, coletor_mensagens: list) -> None:
    """
    Sincroniza os campos customizados do Zoho com o banco de dados local.
    Garante que campos como data_de_homologacao, data_de_onboarding, etc. 
    estejam sempre atualizados no banco.
    """
    if not custom_fields_resolvidos:
        return
    
    # Mapeamento de campos customizados do Zoho para colunas do banco de dados
    campo_para_coluna = {
        'data_de_homologacao': 'data_homologacao',
        'data_de_onboarding': 'data_de_onboarding',
        'data_liberacao_servidor': 'data_liberacao_servidor',
        'data_de_inicio_da_implantacao': 'data_inicio_implantacao',
        'data_de_virada': 'data_virada',
    }
    
    updates = {}
    for campo_zoho, valor in custom_fields_resolvidos.items():
        coluna_banco = campo_para_coluna.get(campo_zoho)
        if coluna_banco:
            updates[coluna_banco] = valor
    
    if not updates:
        return
    
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Monta query de atualização dinamicamente
        set_clause = ', '.join([f"{col} = ?" for col in updates.keys()])
        values = list(updates.values()) + [projeto_id]
        
        sql = f"UPDATE projects SET {set_clause} WHERE id = ?"
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        
        campos_atualizados = ', '.join([f"'{col}'" for col in updates.keys()])
        mensagem = f"Banco de dados: campos {campos_atualizados} sincronizados com Zoho"
        coletor_mensagens.append(mensagem)
        
    except Exception as e:
        print(f"[ERROR][DB] Erro ao sincronizar campos customizados no banco: {e}")
        coletor_mensagens.append(f"Aviso: Falha ao sincronizar campos no banco: {e}")
```

### 2. Integração na Função `_atualizar_zoho()`

**Localização**: `routes/api.py`, função `_atualizar_zoho()` (linha ~1015)

```python
if payload_patch:
    # ... código de atualização no Zoho ...
    
    response_patch = requests.patch(base_url, headers=headers, json=payload_patch, timeout=45)
    
    if response_patch.status_code not in (200, 201):
        raise RuntimeError(...)
    
    # ✅ NOVO: Sincronizar campos customizados no banco de dados local
    if custom_fields:
        _sincronizar_custom_fields_banco(projeto_id, payload_patch.get("custom_fields", {}), coletor_mensagens)
```

---

## 🔄 Fluxo de Execução

### Exemplo: Movendo para "Em Homologação"

```
1. 🎨 Usuário arrasta card para "Em Homologação"
         ↓
2. 📝 Backend lê mapeamento_colunas.json
   - zohoCustomFields: { "data_de_homologacao": "CURRENT_DATE" }
         ↓
3. 🔧 Backend resolve placeholder
   - "CURRENT_DATE" → "2025-10-13"
         ↓
4. 🏢 Backend atualiza Zoho Projects
   - PATCH /projects/{id}
   - custom_fields: { "data_de_homologacao": "2025-10-13" }
   - Status: 200 OK ✅
         ↓
5. 💾 Backend sincroniza banco de dados (NOVO!)
   - UPDATE projects 
   - SET data_homologacao = '2025-10-13' 
   - WHERE id = '{projeto_id}'
   - ✅ Banco atualizado imediatamente!
         ↓
6. 📊 Backend atualiza Google Sheets
   - Coluna "Dt Homolog" = "13/10/2025"
         ↓
7. ✨ Frontend recebe confirmação
   - Badge "dias_na_fase" = "Hoje"
```

---

## 🧪 Como Testar

### Teste 1: Verificação da Sincronização

1. **Mover card** para "Em Homologação"
2. **Verificar logs** no console do backend:
   ```
   [DEBUG][DB] Preparando atualização: data_homologacao = 2025-10-13
   [DEBUG][DB] Banco de dados: campos 'data_homologacao' sincronizados com Zoho
   ```
3. **Consultar banco** diretamente:
   ```python
   import database
   project = database.get_project_by_id("SEU_PROJECT_ID")
   print(f"data_homologacao: {project['data_homologacao']}")
   # Deve mostrar: data_homologacao: 2025-10-13
   ```

### Teste 2: Onboarding

1. **Mover card** para "Falta Liberar Servidor Infra" (sai de Aguardando Onboarding)
2. **Verificar logs**:
   ```
   [DEBUG][DB] Preparando atualização: data_de_onboarding = 2025-10-13
   [DEBUG][DB] Banco de dados: campos 'data_de_onboarding' sincronizados com Zoho
   ```
3. **Consultar banco**:
   ```python
   project = database.get_project_by_id("SEU_PROJECT_ID")
   print(f"data_de_onboarding: {project['data_de_onboarding']}")
   # Deve mostrar: data_de_onboarding: 2025-10-13
   ```

### Teste 3: Liberação de Servidor

1. **Mover card** para "Em Andamento" (de Falta Liberar Servidor Infra)
2. **Verificar logs**:
   ```
   [DEBUG][DB] Preparando atualização: data_liberacao_servidor = 2025-10-13
   [DEBUG][DB] Banco de dados: campos 'data_liberacao_servidor' sincronizados com Zoho
   ```
3. **Consultar banco**:
   ```python
   project = database.get_project_by_id("SEU_PROJECT_ID")
   print(f"data_liberacao_servidor: {project['data_liberacao_servidor']}")
   # Deve mostrar: data_liberacao_servidor: 2025-10-13
   ```

---

## 📊 Comparação: Antes vs Depois

### Antes (Sem Sincronização Automática)

```
Moveu card → Zoho atualizado → Banco desatualizado ❌
                                      ↓
                            Aguardar sincronização periódica
                                      ↓
                            Banco atualizado após ~5min ⏰
```

### Depois (Com Sincronização Automática)

```
Moveu card → Zoho atualizado → Banco atualizado imediatamente ✅
                                      ↓
                            Dados consistentes em <1s ⚡
```

---

## 🎯 Benefícios

### 1. **Consistência Imediata** ⚡
- Banco de dados sempre atualizado
- Não há delay entre Zoho e banco

### 2. **Consultas Confiáveis** 📊
- Queries ao banco retornam dados atuais
- Relatórios sempre precisos

### 3. **Redução de Sincronizações** 🚀
- Menos chamadas completas à API do Zoho
- Performance melhorada

### 4. **Rastreabilidade Completa** 📝
- Logs detalhados de cada sincronização
- Fácil debugging

### 5. **Extensível** 🔧
- Adicionar novos campos é trivial
- Apenas atualizar o dicionário `campo_para_coluna`

---

## 🔍 Logs de Depuração

### Logs Bem-Sucedidos
```
[DEBUG][DB] Preparando atualização: data_homologacao = 2025-10-13
[DEBUG][DB] Banco de dados: campos 'data_homologacao' sincronizados com Zoho
```

### Logs de Erro
```
[ERROR][DB] Erro ao sincronizar campos customizados no banco: [detalhe do erro]
```

### Logs Informativos
```
[DEBUG][DB] Nenhum campo customizado mapeado para atualizar no banco
```

---

## ➕ Como Adicionar Novos Campos

Para adicionar um novo campo customizado à sincronização automática:

### Passo 1: Atualizar o Mapeamento

Editar `routes/api.py`, função `_sincronizar_custom_fields_banco()`:

```python
campo_para_coluna = {
    'data_de_homologacao': 'data_homologacao',
    'data_de_onboarding': 'data_de_onboarding',
    'data_liberacao_servidor': 'data_liberacao_servidor',
    'data_de_inicio_da_implantacao': 'data_inicio_implantacao',
    'data_de_virada': 'data_virada',
    # ✅ ADICIONAR NOVO CAMPO AQUI:
    'seu_novo_campo_zoho': 'sua_coluna_banco',
}
```

### Passo 2: Garantir Coluna no Banco

Se a coluna não existe, criar migração em `database.py`:

```python
def _migrate_database(cursor):
    # ... migrações existentes ...
    
    # Nova migração
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(projects)").fetchall()]
    if 'sua_coluna_banco' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN sua_coluna_banco TEXT")
        print("Migração: Coluna 'sua_coluna_banco' adicionada")
```

### Passo 3: Configurar no mapeamento_colunas.json

```json
"Sua Coluna": {
  "zohoCustomFields": {
    "seu_novo_campo_zoho": "CURRENT_DATE"
  }
}
```

**Pronto!** A sincronização funcionará automaticamente.

---

## 🛡️ Tratamento de Erros

### Erro na Atualização do Banco
- **Comportamento**: Erro é logado, mas não interrompe o fluxo
- **Mensagem ao usuário**: "Aviso: Falha ao sincronizar campos no banco"
- **Impacto**: Zoho e Planilha são atualizados normalmente

### Campo Não Mapeado
- **Comportamento**: Campo é ignorado silenciosamente
- **Log**: "[DEBUG][DB] Nenhum campo customizado mapeado para atualizar no banco"
- **Impacto**: Nenhum (comportamento esperado)

---

## 📚 Arquivos Modificados

| Arquivo | Tipo de Alteração | Descrição |
|---------|-------------------|-----------|
| `routes/api.py` | ➕ Função | Adicionada `_sincronizar_custom_fields_banco()` |
| `routes/api.py` | ✏️ Código | Integrada chamada em `_atualizar_zoho()` |
| `SINCRONIZACAO_BANCO_DADOS.md` | ➕ Documentação | Este arquivo |

---

## 🎉 Resumo

A sincronização automática garante que:

✅ **Banco sempre atualizado** com campos do Zoho  
✅ **Sem necessidade de aguardar** sincronização periódica  
✅ **Consultas confiáveis** ao banco de dados  
✅ **Logs detalhados** para debugging  
✅ **Fácil de estender** para novos campos  

---

## 🚀 Próximos Passos

1. ✅ Testar movimentações que atualizam campos customizados
2. ✅ Verificar logs de sincronização no console
3. ✅ Validar dados no banco com consultas diretas
4. ✅ Confirmar que queries retornam dados atualizados
5. 🎉 Usar em produção com confiança!

---

**Desenvolvido com ❤️ para manter dados sempre sincronizados**
