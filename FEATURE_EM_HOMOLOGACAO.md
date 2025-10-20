# ✅ Feature: Ações Automáticas ao Mover para "Em Homologação"

**Data**: 13 de outubro de 2025  
**Status**: ✅ Implementado

---

## 🎯 Objetivo

Implementar ações automáticas quando um card é movido para a coluna **"Em Homologação"** no Kanban, garantindo:

1. ✅ Remoção da tag "Em Implantação" no Zoho Projects
2. ✅ Adição da tag "Em Homologação" no Zoho Projects
3. ✅ Preenchimento do campo customizado `data_de_homologacao` com a data atual no Zoho
4. ✅ Atualização do Status Principal para "Em Homologação" na Planilha Principal
5. ✅ Preenchimento do campo "Dt Homolog" com a data atual (formato dd/mm/yyyy) na Planilha Principal

---

## 🔧 Implementação

### 1. Configuração no `mapeamento_colunas.json`

```json
"Em Homologação": {
  "sheetStatus": "Em Homologação",
  "zohoStatusId": "2376502000000020092",
  "zohoTagsToAdd": ["2376502000000983053"],
  "zohoTagsToRemove": ["2376502000000188201"],
  "zohoCustomFields": {
    "data_de_homologacao": "CURRENT_DATE"
  },
  "triggers": [
    {
      "type": "taskComment",
      "taskName": "02.01.01 - Validação do DEIP",
      "mentions": ["Giovani Sousa"],
      "template": "Olá {mentions}, favor validar o DEIP e registrar feedback."
    },
    {
      "type": "workflow",
      "name": "preencher_dpi_homologacao"
    }
  ],
  "onTransition": {
    "from_Em_Andamento_-_Implantação": {
      "sheetColumns": {
        "Dt Homolog": "CURRENT_DATE_DDMMYYYY"
      }
    }
  }
}
```

#### Alterações realizadas:
- **`zohoTagsToRemove`**: Adicionado ID da tag "Em Implantação" (`2376502000000188201`)
- **`zohoCustomFields`**: Adicionado campo `data_de_homologacao` com valor `CURRENT_DATE`
- **`onTransition`**: Configurado para atualizar coluna "Dt Homolog" ao transicionar de "Em Andamento - Implantação"

---

### 2. Atualização da Função `_atualizar_planilha()` em `routes/api.py`

Foi adicionado suporte genérico para processar o campo `onTransition` do mapeamento de colunas:

```python
# Processar atualizações de colunas específicas através de onTransition
if coluna_origem:
    on_transition = info_dest.get("onTransition", {})
    # Normalizar nome da coluna de origem removendo espaços especiais
    coluna_origem_key = f"from_{coluna_origem.replace(' ', '_').replace('-', '_')}"
    transition_config = on_transition.get(coluna_origem_key, {})
    sheet_columns = transition_config.get("sheetColumns", {})
    
    if sheet_columns:
        print(f"[DEBUG][SHEET] Processando onTransition para transição '{coluna_origem}' -> '{coluna_destino}'")
        for nome_coluna, valor_config in sheet_columns.items():
            try:
                # Resolver valores especiais
                if isinstance(valor_config, str) and valor_config.upper() == "CURRENT_DATE_DDMMYYYY":
                    valor_real = datetime.now().strftime('%d/%m/%Y')
                elif isinstance(valor_config, str) and valor_config.upper() == "CURRENT_DATE":
                    valor_real = datetime.now().strftime('%Y-%m-%d')
                else:
                    valor_real = valor_config
                
                print(f"[DEBUG][SHEET] Atualizando coluna '{nome_coluna}' para '{valor_real}'")
                utils.update_col_value_by_cliente_tolerant(sheets_service, chave_busca, nome_coluna, valor_real)
                coletor_mensagens.append(f'Planilha principal: Coluna "{nome_coluna}" atualizada para "{valor_real}".')
                print(f"[DEBUG][SHEET] Coluna '{nome_coluna}' atualizada com sucesso")
            except Exception as e:
                print(f"[DEBUG][SHEET] Erro ao atualizar coluna '{nome_coluna}': {e}")
                coletor_mensagens.append(f'Aviso: Falha ao atualizar coluna "{nome_coluna}": {e}')
```

---

## 🔄 Fluxo de Execução

### Quando o card é movido de "Em Andamento - Implantação" para "Em Homologação":

1. **Frontend**: Usuário arrasta o card no Kanban
2. **Requisição POST** para `/api/mover_projeto` com:
   ```json
   {
     "projeto_id": "2376502000005544019",
     "coluna_origem": "Em Andamento - Implantação",
     "coluna_destino": "Em Homologação",
     "cliente_sheet": "Nome do Cliente"
   }
   ```

3. **Backend - Banco de Dados**:
   - Atualiza `data_mudanca_status` = data atual
   - Atualiza `status_atual` = "Em Homologação"

4. **Backend - Zoho Projects API**:
   - **Status**: Mantém "Em Andamento" (ID: `2376502000000020092`)
   - **Tags**: 
     - Remove tag "Em Implantação" (ID: `2376502000000188201`)
     - Adiciona tag "Em Homologação" (ID: `2376502000000983053`)
   - **Campo Customizado**: 
     - Define `data_de_homologacao` = data atual (formato: `YYYY-MM-DD`)
   - **Triggers**:
     - Adiciona comentário na tarefa "02.01.01 - Validação do DEIP"
     - Executa workflow `preencher_dpi_homologacao`

5. **Backend - Google Sheets API**:
   - Atualiza coluna **"Status Principal"** = "Em Homologação"
   - Atualiza coluna **"Dt Homolog"** = data atual (formato: `DD/MM/YYYY`)

6. **Resposta ao Frontend**:
   ```json
   {
     "sucesso": true,
     "mensagem": "Projeto movido com sucesso.",
     "dados_atualizados": {
       "dias_na_fase": "Hoje",
       "data_mudanca_status": "2025-10-13",
       "status_atual": "Em Homologação"
     }
   }
   ```

---

## 📋 IDs e Constantes Utilizadas

| Recurso | Tipo | ID/Valor | Local |
|---------|------|----------|-------|
| Tag "Em Implantação" | Zoho Tag | `2376502000000188201` | `config.py` → `TAG_IMPLANTACAO` |
| Tag "Em Homologação" | Zoho Tag | `2376502000000983053` | `config.py` → `TAG_EM_HOMOLOGACAO_ID` |
| Status "Em Andamento" | Zoho Status | `2376502000000020092` | `config.py` → `STATUS_EM_ANDAMENTO_ID` |
| Campo Customizado | Zoho Custom Field | `data_de_homologacao` | Campo criado no Zoho Projects |

---

## 🧪 Como Testar

### Teste 1: Movimentação Completa
1. Certifique-se de que o projeto está na coluna **"Em Andamento - Implantação"**
2. Verifique que possui a tag **"Em Implantação"** no Zoho
3. Arraste o card para **"Em Homologação"**
4. **Verificações**:
   - ✅ Tag "Em Implantação" foi **removida** no Zoho
   - ✅ Tag "Em Homologação" foi **adicionada** no Zoho
   - ✅ Campo `data_de_homologacao` preenchido com data atual no Zoho
   - ✅ Coluna "Status Principal" = "Em Homologação" na planilha
   - ✅ Coluna "Dt Homolog" preenchida com data atual (DD/MM/YYYY) na planilha
   - ✅ Badge "dias_na_fase" mostra **"Hoje"** no card

### Teste 2: Logs de Depuração
Verifique o console do backend para os logs:
```
[DEBUG][SHEET] Processando onTransition para transição 'Em Andamento - Implantação' -> 'Em Homologação'
[DEBUG][SHEET] Atualizando coluna 'Dt Homolog' para '13/10/2025'
[DEBUG][SHEET] Coluna 'Dt Homolog' atualizada com sucesso
```

### Teste 3: Verificação no Zoho
1. Acesse o projeto no Zoho Projects
2. Verifique a seção de **Tags**: deve conter apenas "Em Homologação"
3. Verifique o campo customizado **"Data de Homologação"**: deve estar preenchido

### Teste 4: Verificação na Planilha
1. Abra a Planilha Principal do Google Sheets
2. Localize a linha do projeto pelo nome do cliente
3. Verifique:
   - Coluna **"Status Principal"** = "Em Homologação"
   - Coluna **"Dt Homolog"** = data atual no formato `DD/MM/YYYY`

---

## 🔍 Resolução de Placeholders

O sistema suporta os seguintes placeholders para valores de data:

| Placeholder | Formato Resultante | Uso |
|-------------|-------------------|-----|
| `CURRENT_DATE` | `YYYY-MM-DD` | Campos customizados do Zoho |
| `CURRENT_DATE_DDMMYYYY` | `DD/MM/YYYY` | Colunas da planilha Google Sheets |

---

## ♻️ Reutilização para Outras Colunas

Este sistema é **totalmente reutilizável** para outras transições! Basta configurar no `mapeamento_colunas.json`:

### Exemplo: Configurar para "Em Virada"
```json
"Em Virada": {
  "sheetStatus": "Em Virada",
  "zohoStatusId": "2376502000000020092",
  "zohoTagsToAdd": ["2376502000001228741"],
  "zohoTagsToRemove": ["2376502000000983053"],
  "zohoCustomFields": {
    "data_de_virada": "CURRENT_DATE"
  },
  "onTransition": {
    "from_Em_Homologação": {
      "sheetColumns": {
        "Dt Virada": "CURRENT_DATE_DDMMYYYY"
      }
    }
  }
}
```

---

## 📚 Arquivos Modificados

| Arquivo | Tipo de Alteração | Descrição |
|---------|-------------------|-----------|
| `mapeamento_colunas.json` | ➕ Configuração | Adicionados campos para "Em Homologação" |
| `routes/api.py` | ✏️ Código | Implementado suporte a `onTransition` |
| `FEATURE_EM_HOMOLOGACAO.md` | ➕ Documentação | Este arquivo |

---

## 🎉 Benefícios

1. **Automação Completa**: Todas as ações executadas automaticamente
2. **Consistência de Dados**: Zoho e Planilha sempre sincronizados
3. **Rastreabilidade**: Data exata de entrada em homologação registrada
4. **Reutilizável**: Modelo pode ser aplicado a outras colunas facilmente
5. **Manutenível**: Configuração centralizada em JSON

---

## 🚀 Próximos Passos

1. ✅ Testar a movimentação em ambiente de produção
2. ✅ Validar logs de depuração no console
3. ✅ Confirmar atualização correta no Zoho Projects
4. ✅ Confirmar atualização correta na Planilha Principal
5. 📝 Considerar adicionar alertas/notificações para a equipe quando projeto entrar em homologação

---

## 📞 Suporte

Em caso de problemas ou dúvidas:
1. Verificar logs no console do backend (`[DEBUG][SHEET]` e `[MOVE]`)
2. Confirmar que os IDs das tags/status estão corretos no `config.py`
3. Validar que a coluna "Dt Homolog" existe na Planilha Principal

---

**Desenvolvido com ❤️ para otimizar o fluxo de trabalho da equipe de implantação**
