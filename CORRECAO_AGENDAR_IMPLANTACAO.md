# 🔧 Correção: Agendar Implantação - Datas Previstas e Google Calendar

## 🐛 Problema Identificado

Ao clicar em "Agendar Implantação", os seguintes problemas foram detectados:

1. ❌ **Campos no Zoho não preenchidos**:
   - `data_de_homologacao_prevista` ficava vazio
   - `data_de_virada_prevista` ficava vazio

2. ❌ **Eventos no Google Calendar não criados**:
   - Evento de Homologação não era criado
   - Evento de Virada não era criado

## ✅ Solução Implementada

### 1️⃣ Cálculo Automático de Datas Previstas

**Arquivo modificado**: `routes/api.py` - Endpoint `/api/iniciar_implantacao`

**Lógica implementada**:

```python
# Data de início da implantação (fornecida pelo usuário)
data_inicio_implantacao = "2025-10-20"  # exemplo

# Homologação Prevista: 42 dias corridos após início (~30 dias úteis)
# Ajustada para segunda-feira da semana
data_homologacao_prevista = inicio + 42 dias → próxima segunda-feira

# Virada Prevista: 1 semana após homologação
# Ajustada para segunda-feira da semana
data_virada_prevista = homologacao + 7 dias → próxima segunda-feira
```

**Exemplo**:
- **Início Implantação**: 20/10/2025 (segunda)
- **Homologação Prevista**: 01/12/2025 (segunda) - 42 dias depois
- **Virada Prevista**: 08/12/2025 (segunda) - 1 semana depois

### 2️⃣ Atualização dos Campos Customizados no Zoho

**Campos enviados ao Zoho Projects**:

```json
{
  "custom_fields": {
    "data_de_inicio_da_implantacao": "2025-10-20",
    "data_de_homologacao_prevista": "2025-12-01",
    "data_de_virada_prevista": "2025-12-08"
  }
}
```

**Implementação**:
- ✅ Método principal: via `_atualizar_zoho()` com configuração modificada
- ✅ Método fallback: PATCH direto na API v3 se falhar

### 3️⃣ Integração com Google Calendar

**Módulo utilizado**: `google_calendar.py` (já existente, mas não estava sendo chamado)

**Funções importadas**:
- `criar_evento_homologacao()` - Cria evento de Homologação
- `criar_evento_virada()` - Cria evento de Virada

**Características dos eventos criados**:

#### Evento de Homologação:
```
Título: "Homologação {NOME_CLIENTE} (Remoto/Presencial)"
Data Início: data_homologacao_prevista (segunda-feira)
Data Fim: sexta-feira da mesma semana
Tipo: Evento de dia inteiro
Cor: Magenta (colorId: 3)
Calendário: GOOGLE_CALENDAR_ID configurado
```

#### Evento de Virada:
```
Título: "Virada {NOME_CLIENTE} (Remoto/Presencial)"
Data Início: data_virada_prevista (segunda-feira)
Data Fim: sexta-feira da mesma semana
Tipo: Evento de dia inteiro
Cor: Magenta (colorId: 3)
Calendário: GOOGLE_CALENDAR_ID configurado
```

**Exemplo de eventos criados**:
- **Homologação Hospital XYZ (Remoto)**: 01/12/2025 (seg) até 05/12/2025 (sex)
- **Virada Hospital XYZ (Remoto)**: 08/12/2025 (seg) até 12/12/2025 (sex)

### 4️⃣ Parâmetro de Modalidade

**Novo parâmetro aceito** no endpoint `/api/iniciar_implantacao`:

```json
{
  "project_id": "2376502000005544019",
  "data_inicio_implantacao": "2025-10-20",
  "implantador_ris": "Pablo Pyerri Ferreira da Costa",
  "implantador_pacs": "Camilo Osaida",
  "modalidade": "Remoto"  // Novo parâmetro (opcional)
}
```

**Valores possíveis**:
- `"Remoto"` - Implantação remota
- `"Presencial"` - Implantação presencial
- `"Remoto/Presencial"` - **Padrão** se não informado

**Uso**: Define a modalidade que aparece nos títulos dos eventos do Google Calendar

---

## 📝 Alterações no Código

### Arquivo: `routes/api.py`

#### Seção 1: Cálculo de Datas (linhas ~1650)

```python
# ==== CALCULAR DATAS PREVISTAS ====
from datetime import datetime, timedelta

# Calcular data de homologação prevista (30 dias úteis ≈ 42 dias corridos)
data_inicio_dt = datetime.strptime(data_inicio_implantacao, '%Y-%m-%d')
data_homologacao_prevista_dt = data_inicio_dt + timedelta(days=42)

# Ajustar para segunda-feira
while data_homologacao_prevista_dt.weekday() != 0:
    data_homologacao_prevista_dt += timedelta(days=1)

data_homologacao_prevista = data_homologacao_prevista_dt.strftime('%Y-%m-%d')

# Calcular data de virada prevista (1 semana após homologação)
data_virada_prevista_dt = data_homologacao_prevista_dt + timedelta(days=7)

# Ajustar para segunda-feira
while data_virada_prevista_dt.weekday() != 0:
    data_virada_prevista_dt += timedelta(days=1)

data_virada_prevista = data_virada_prevista_dt.strftime('%Y-%m-%d')
```

#### Seção 2: Atualização do Zoho (linhas ~1700)

```python
# Atualizar campos customizados na configuração
custom_fields_config = info_dest.get("zohoCustomFields", {}).copy()
custom_fields_config["data_de_inicio_da_implantacao"] = data_inicio_implantacao
custom_fields_config["data_de_homologacao_prevista"] = data_homologacao_prevista
custom_fields_config["data_de_virada_prevista"] = data_virada_prevista
info_dest_modificada = info_dest.copy()
info_dest_modificada["zohoCustomFields"] = custom_fields_config
```

#### Seção 3: Fallback (linhas ~1730)

```python
# Atualizar campos customizados (incluindo datas previstas)
payload_custom = {
    "custom_fields": {
        "data_de_inicio_da_implantacao": data_inicio_implantacao,
        "data_de_homologacao_prevista": data_homologacao_prevista,
        "data_de_virada_prevista": data_virada_prevista
    }
}
```

#### Seção 4: Google Calendar (linhas ~1850 - NOVO)

```python
# ==== 1.6. CRIAR EVENTOS NO GOOGLE CALENDAR ====
from google_calendar import criar_evento_homologacao, criar_evento_virada

# Obter nome do cliente
proj_name = str((detalhes_zoho or {}).get('name', '') or '')
nome_cliente = proj_name.split(' - NR')[0].split(' - AP')[0].split(' - NR/AP')[0].strip()

# Obter credenciais do Google
creds = utils.build_google_credentials_from_session()

# Criar evento de Homologação
sucesso_homolog, event_id_homolog, erro_homolog = criar_evento_homologacao(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_homologacao=data_homologacao_prevista,
    modalidade=modalidade
)

# Criar evento de Virada
sucesso_virada, event_id_virada, erro_virada = criar_evento_virada(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_virada=data_virada_prevista,
    modalidade=modalidade
)
```

---

## 🧪 Como Testar

### 1. Preparação
```powershell
cd "c:\Users\Giovani Souza\Documents\Central_De_Projetos"
python app.py
```

### 2. No Navegador

1. Acesse: http://localhost:5000
2. Vá para a coluna **"Em Andamento"**
3. Clique no ícone ▶️ (play) de um projeto
4. No modal "Agendar Implantação":
   - **Data de Início**: Ex: 20/10/2025
   - **Implantador RIS**: Ex: Pablo Pyerri Ferreira da Costa
   - **Implantador PACS**: Ex: Camilo Osaida
   - **Modalidade**: Remoto, Presencial ou Remoto/Presencial
5. Clique em **"Agendar Implantação"**

### 3. Verificações

#### ✅ No Zoho Projects:

1. Abra o projeto no Zoho
2. Vá em "Configurações" → "Campos Customizados" ou visualização do projeto
3. Verifique se os campos foram preenchidos:
   - **Data de Início da Implantação**: 20/10/2025
   - **Data de Homologação Prevista**: 01/12/2025 (calculada automaticamente)
   - **Data de Virada Prevista**: 08/12/2025 (calculada automaticamente)

#### ✅ No Google Calendar:

1. Acesse o Google Calendar configurado (conforme `GOOGLE_CALENDAR_ID` em `config.py`)
2. Navegue até **Dezembro de 2025**
3. Verifique se existem 2 eventos:
   - **Semana de 01/12 a 05/12**: "Homologação {Cliente} (Remoto)"
   - **Semana de 08/12 a 12/12**: "Virada {Cliente} (Remoto)"

#### ✅ Nos Logs do Terminal:

```
[DEBUG][INICIAR_IMPLANTACAO] Datas calculadas:
[DEBUG][INICIAR_IMPLANTACAO]   📅 Início Implantação: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO]   📅 Homologação Prevista: 2025-12-01
[DEBUG][INICIAR_IMPLANTACAO]   📅 Virada Prevista: 2025-12-08

[DEBUG][GOOGLE_CALENDAR] Criando evento de Homologação:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Homologação Hospital XYZ (Remoto)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 01/12/2025 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 05/12/2025 (Friday)

[INFO][GOOGLE_CALENDAR] ✅ Evento de Homologação criado com sucesso!

[DEBUG][GOOGLE_CALENDAR] Criando evento de Virada:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Virada Hospital XYZ (Remoto)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 08/12/2025 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 12/12/2025 (Friday)

[INFO][GOOGLE_CALENDAR] ✅ Evento de Virada criado com sucesso!
```

---

## 🔄 Tratamento de Erros

### Erros Tolerados (não falham a operação principal):

1. **Falha ao criar evento no Google Calendar**:
   - Log do erro
   - Aviso adicionado em `mensagens_zoho`
   - Operação continua normalmente

2. **Falha ao adicionar implantadores**:
   - Log do erro
   - Aviso adicionado em `mensagens_zoho`
   - Operação continua normalmente

3. **Falha ao atualizar campo customizado no Zoho**:
   - Tenta método principal
   - Se falhar, tenta fallback
   - Se ambos falharem, retorna erro

### Mensagens de Sucesso Esperadas:

```json
{
  "sucesso": true,
  "mensagem": "Implantação iniciada com sucesso! Zoho Projects e planilha atualizados.",
  "detalhes": [
    "Campo customizado atualizado (modo compatibilidade)",
    "Tag de implantação adicionada",
    "RIS (Pablo Pyerri Ferreira da Costa): Pablo Pyerri Ferreira da Costa adicionado! 158 tarefas atribuídas",
    "PACS (Camilo Osaida): Camilo Osaida adicionado! 31 tarefas atribuídas",
    "Evento de Homologação criado no Google Calendar para 01/12/2025",
    "Evento de Virada criado no Google Calendar para 08/12/2025",
    "Implant Responsável atualizado."
  ]
}
```

---

## 📊 Resumo das Melhorias

| Item | Antes | Depois |
|------|-------|--------|
| **Data Homologação Prevista** | ❌ Não preenchida | ✅ Calculada e preenchida automaticamente |
| **Data Virada Prevista** | ❌ Não preenchida | ✅ Calculada e preenchida automaticamente |
| **Evento Homologação no Calendar** | ❌ Não criado | ✅ Criado automaticamente |
| **Evento Virada no Calendar** | ❌ Não criado | ✅ Criado automaticamente |
| **Cálculo de Datas** | ❌ Inexistente | ✅ Baseado em 30 dias úteis + 1 semana |
| **Ajuste para Segunda-feira** | ❌ Não havia | ✅ Datas sempre caem em segunda-feira |
| **Modalidade nos Eventos** | ❌ Não configurável | ✅ Remoto/Presencial/Ambos |

---

## 🎯 Benefícios

1. ✅ **Automação completa**: Usuário só informa data de início, sistema calcula o resto
2. ✅ **Visibilidade no Zoho**: Todas as datas previstas ficam registradas no projeto
3. ✅ **Agenda sincronizada**: Equipe visualiza eventos de Homologação e Virada no Google Calendar
4. ✅ **Padronização**: Eventos sempre começam em segunda-feira (início da semana de trabalho)
5. ✅ **Flexibilidade**: Modalidade (Remoto/Presencial) pode ser configurada
6. ✅ **Tolerância a falhas**: Erros no Calendar não impedem o agendamento da implantação

---

## 📌 Observações Importantes

1. **Prazo de Implantação**: 
   - O sistema usa **42 dias corridos** como aproximação de **30 dias úteis**
   - Isso considera fins de semana e feriados médios
   - Pode ser ajustado conforme necessidade do negócio

2. **Ajuste para Segunda-feira**:
   - Garante que semanas de Homologação e Virada sempre comecem na segunda
   - Facilita planejamento da equipe

3. **Duração dos Eventos**:
   - Homologação: Segunda a sexta da semana calculada
   - Virada: Segunda a sexta, uma semana após homologação

4. **Configuração do Calendar**:
   - O ID do calendário deve estar configurado em `config.py`:
     ```python
     GOOGLE_CALENDAR_ID = 'seu-calendario@group.calendar.google.com'
     ```

5. **Permissões Google**:
   - O escopo `https://www.googleapis.com/auth/calendar` já está configurado
   - Usuário precisa ter autorizado acesso ao Google Calendar durante login

---

**Data da Correção**: 19/10/2025  
**Versão**: 2.1 - Correção completa de Agendar Implantação  
**Status**: ✅ Implementado e pronto para testes
