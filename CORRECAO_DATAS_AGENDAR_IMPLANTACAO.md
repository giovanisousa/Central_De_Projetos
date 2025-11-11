# ✅ CORREÇÃO: Datas em "Agendar Implantação"

## 📋 Problema Reportado

Quando você testou **"Agendar Implantação"** localmente, as seguintes datas **NÃO** foram atualizadas:

1. ❌ `data_de_inicio_da_implantacao` - não foi enviada para o Zoho
2. ❌ `data_termino_original` (Homologação Prevista) - não foi preenchida no Zoho
3. ❌ `data_de_virada_original` (Virada Prevista) - não foi preenchida no Zoho
4. ❌ Colunas na planilha Google Sheets não foram preenchidas

## ✅ Solução Implementada

### Mudanças em `implantacao_manager.py`

Adicionei uma **nova seção (3.5)** na função `agendar_implantacao()` que:

1. **Obtém detalhes do projeto** do Zoho para descobrir `produtos_contratados`
2. **Calcula as datas** seguindo as mesmas regras de "Iniciar Implantação":
   ```python
   data_de_inicio_da_implantacao = hoje (YYYY-MM-DD)
   
   # Dias até homologação baseado em produtos
   - netRIS ou "net ris": 95 dias corridos
   - AnimatiPACS: 35 dias corridos
   - Default: 95 dias
   
   data_termino_original = data_inicio + dias_homologacao
   # Ajustar para segunda-feira
   
   data_de_virada_original = data_homologacao + 7 dias
   # Ajustar para segunda-feira
   ```

3. **Atualiza os custom fields no Zoho** com as 3 datas calculadas
4. **Registra no resultado** que as datas foram atualizadas (`datas_atualizadas: true`)

### Mudanças em `routes/api.py`

Adicionei código no endpoint `api_agendar_implantacao()` que:

1. **Verifica se as datas foram atualizadas** (`resultado.get('datas_atualizadas')`)
2. **Obtém os custom fields atualizados** do Zoho
3. **Extrai o nome do cliente** do nome do projeto
4. **Atualiza 3 colunas na planilha Google Sheets**:
   - `Data Implantação` = data_de_inicio_da_implantacao (formato dd/mm/yyyy)
   - `Homolog. Prevista` = data_termino_original (formato dd/mm/yyyy)
   - `Virada Prevista` = data_de_virada_original (formato dd/mm/yyyy)
5. **Retorna informações** sobre quais colunas foram atualizadas

## 🧪 Como Testar

### 1. Preparar ambiente local

```powershell
# Fazer pull das mudanças
cd "c:\Users\Giovani Souza\Documents\Central_De_Projetos"
git pull origin correcao16

# Reiniciar o servidor Flask
# Ctrl+C para parar
# Depois executar novamente:
python app.py
```

### 2. Testar "Agendar Implantação"

1. Acesse o painel local
2. Mova um projeto para **"Aguardando Cronograma"** (se ainda não estiver)
3. Clique em **"Agendar Implantação"** no card do projeto
4. Escolha RIS ou PACS
5. Clique em **"Agendar"**

### 3. Verificar no Zoho Projects

Abra o projeto no Zoho e verifique se os seguintes **custom fields** foram preenchidos:

- ✅ **Data de Início da Implantação**: data de hoje (YYYY-MM-DD)
- ✅ **Data de Homologação Prevista** (`data_de_termino_original`): hoje + 95 dias (netRIS) ou + 35 dias (AnimatiPACS), ajustado para segunda-feira
- ✅ **Data de Virada Prevista** (`data_de_virada_original`): homologação + 7 dias, ajustado para segunda-feira

### 4. Verificar na Planilha Google Sheets

Abra a planilha principal e verifique se as seguintes **colunas** foram preenchidas para o cliente:

- ✅ **Data Implantação**: data de hoje (dd/mm/yyyy)
- ✅ **Homolog. Prevista**: data de homologação prevista (dd/mm/yyyy)
- ✅ **Virada Prevista**: data de virada prevista (dd/mm/yyyy)

### 5. Verificar logs

No terminal onde o Flask está rodando, você deve ver logs como:

```
📋 Produtos contratados: netRIS
📅 Dias até homologação: 95 (baseado em: netRIS)
📅 Datas calculadas:
  - Início Implantação: 2024-01-15
  - Homologação Prevista: 2024-04-22
  - Virada Prevista: 2024-04-29
✅ Datas de implantação atualizadas no Zoho
📊 Atualizando planilha Google Sheets com datas de implantação...
✅ Coluna 'Data Implantação' atualizada
✅ Coluna 'Homolog. Prevista' atualizada
✅ Coluna 'Virada Prevista' atualizada
✅ Planilha atualizada com 3 colunas
```

## 📊 Exemplo de Resposta da API

Quando bem-sucedido, a API retorna:

```json
{
  "sucesso": true,
  "usuarios_adicionados": [...],
  "tarefas_atribuidas": [...],
  "custom_fields_atualizados": true,
  "datas_atualizadas": true,
  "planilha_atualizada": true,
  "colunas_atualizadas": [
    "Data Implantação: 15/01/2024",
    "Homolog. Prevista: 22/04/2024",
    "Virada Prevista: 29/04/2024"
  ],
  "mensagem": "Implantação agendada! 2 usuários adicionados, 15 tarefas atribuídas, datas atualizadas"
}
```

## 🔍 Detalhes Técnicos

### Regras de Cálculo de Datas

1. **Data de Início**: Data atual (hoje)
2. **Homologação Prevista**: 
   - Detecta produtos_contratados no Zoho
   - netRIS: adiciona 95 dias corridos
   - AnimatiPACS: adiciona 35 dias corridos
   - Ajusta para a próxima segunda-feira se não cair em segunda
3. **Virada Prevista**:
   - Homologação + 7 dias
   - Ajusta para a próxima segunda-feira se não cair em segunda

### Formato das Datas

- **Zoho custom fields**: `YYYY-MM-DD` (2024-01-15)
- **Google Sheets**: `dd/mm/yyyy` (15/01/2024)

### Compatibilidade

Esta implementação segue **exatamente a mesma lógica** usada em "Iniciar Implantação" (linhas 1990-2296 em `routes/api.py`), garantindo consistência.

## 🎯 Resultado Esperado

Após esta correção:

✅ **Zoho Projects** mostrará as 3 datas preenchidas automaticamente
✅ **Planilha Google Sheets** mostrará as 3 colunas preenchidas
✅ **Logs detalhados** permitirão debugar qualquer problema
✅ **Mensagens de erro** não quebram a operação principal se a planilha falhar

## 📝 Commit

```
feat: Adicionar cálculo e atualização de datas em Agendar Implantação

- Calcular data_de_inicio_da_implantacao (data atual)
- Calcular data_termino_original (homologação) baseado em produtos_contratados:
  * netRIS: 95 dias corridos
  * AnimatiPACS: 35 dias corridos
  * Ajustar para segunda-feira
- Calcular data_de_virada_original (virada) = homologação + 7 dias, ajustado para segunda
- Atualizar custom fields no Zoho Projects
- Atualizar colunas na planilha Google Sheets:
  * Data Implantação
  * Homolog. Prevista
  * Virada Prevista
- Seguir mesma lógica de Iniciar Implantação
- Resolve problema reportado: datas não eram preenchidas
```

Commit: **6a3ed0b**
Branch: **correcao16**

## ⚠️ Observações

1. **Produtos Contratados**: O cálculo de dias depende do campo `produtos_contratados` estar preenchido corretamente no Zoho. Se não encontrar, usa default de 95 dias (netRIS).

2. **Planilha Google Sheets**: Se a atualização da planilha falhar, a operação **não é abortada**. Um aviso é retornado no resultado, mas as datas são atualizadas no Zoho normalmente.

3. **Nomes das Colunas**: Os nomes exatos das colunas na planilha são:
   - `Data Implantação` (não "Data de Implantação")
   - `Homolog. Prevista` (abreviado)
   - `Virada Prevista`

4. **Segundas-feiras**: Todas as datas previstas são ajustadas para cair em segundas-feiras, seguindo o padrão do negócio (início de semana).
