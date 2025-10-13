# 📅 Integração Google Calendar - Agendamento de Implantação

## 📋 Visão Geral

Quando o botão **"Agendar Implantação"** é clicado, o sistema agora cria automaticamente **2 eventos** no Google Calendar da agenda de implantação da Animati.

### 🎯 Objetivo

Automatizar o registro das datas de **Homologação** e **Virada** no calendário compartilhado da equipe, garantindo visibilidade e organização do cronograma de implantações.

---

## 🗓️ Eventos Criados

### 1️⃣ Evento de Homologação

**Formato do Título:**
```
Homologação {NOME_CLIENTE} (Remoto/Presencial)
```

**Características:**
- 📅 **Data início:** Data calculada de homologação (segunda-feira)
- 📅 **Data fim:** Sexta-feira da mesma semana
- ⏰ **Tipo:** Evento de dia inteiro
- 🎨 **Cor:** Amarelo (colorId: 5)
- 📝 **Descrição:** "Período de homologação do projeto {NOME_CLIENTE}"

**Exemplo:**
```
Título: Homologação Hospital XYZ (Remoto/Presencial)
Período: 20/10/2025 (Segunda) a 24/10/2025 (Sexta)
```

### 2️⃣ Evento de Virada

**Formato do Título:**
```
Virada {NOME_CLIENTE} (Remoto/Presencial)
```

**Características:**
- 📅 **Data início:** Data calculada de virada (segunda-feira da semana seguinte)
- 📅 **Data fim:** Sexta-feira da mesma semana
- ⏰ **Tipo:** Evento de dia inteiro
- 🎨 **Cor:** Vermelho (colorId: 11)
- 📝 **Descrição:** "Período de virada do projeto {NOME_CLIENTE}"

**Exemplo:**
```
Título: Virada Hospital XYZ (Remoto/Presencial)
Período: 27/10/2025 (Segunda) a 31/10/2025 (Sexta)
```

---

## 🔧 Configuração

### Google Calendar ID

**Arquivo:** `config.py`

```python
# Google Calendar - Agenda de Implantação
GOOGLE_CALENDAR_ID = "animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com"
```

### Permissões Google API

Os eventos são criados usando as credenciais Google já configuradas no sistema. É necessário ter o scope de Calendar:

```python
SCOPES_GOOGLE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/calendar',  # ⬅️ Necessário para Calendar
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
```

---

## 📂 Arquivos Relacionados

### 1. `google_calendar.py` (Novo)

Módulo principal para integração com Google Calendar.

**Funções Principais:**

#### `criar_evento_homologacao(credentials, nome_cliente, data_homologacao, modalidade)`
Cria o evento de Homologação.

**Parâmetros:**
- `credentials`: Credenciais Google autenticadas
- `nome_cliente`: Nome do cliente (extraído do nome do projeto)
- `data_homologacao`: Data no formato 'YYYY-MM-DD'
- `modalidade`: "Remoto", "Presencial" ou "Remoto/Presencial" (padrão)

**Retorna:**
```python
(sucesso: bool, event_id: str|None, mensagem_erro: str|None)
```

#### `criar_evento_virada(credentials, nome_cliente, data_virada, modalidade)`
Cria o evento de Virada.

**Parâmetros:** Mesmos da função de homologação.

**Retorna:** Mesma estrutura.

#### `criar_eventos_implantacao(credentials, nome_cliente, data_homologacao, data_virada, modalidade)`
Função de conveniência que cria ambos os eventos de uma vez.

**Retorna:**
```python
{
    'sucesso': bool,  # True se AMBOS criados com sucesso
    'homologacao': {
        'criado': bool,
        'event_id': str | None,
        'erro': str | None
    },
    'virada': {
        'criado': bool,
        'event_id': str | None,
        'erro': str | None
    },
    'mensagem': str  # Mensagem resumo
}
```

#### Funções Auxiliares

- `_calcular_sexta_feira_da_semana(data_inicio)`: Calcula a sexta-feira da semana
- `validar_data_formato(data_str)`: Valida formato YYYY-MM-DD
- `obter_resumo_eventos(data_homologacao, data_virada)`: Gera resumo formatado

### 2. `routes/api.py` (Modificado)

Integração no endpoint `/iniciar_implantacao`.

**Nova Etapa 4:**
```python
# ==== 4. QUARTO: CRIAR EVENTOS NO GOOGLE CALENDAR ====
from google_calendar import criar_eventos_implantacao

resultado_calendar = criar_eventos_implantacao(
    credentials=creds,
    nome_cliente=nome_cliente,
    data_homologacao=datas_calculadas['data_homologacao_prevista'],
    data_virada=datas_calculadas['data_virada_prevista'],
    modalidade="Remoto/Presencial"
)
```

### 3. `config.py` (Modificado)

- ✅ Adicionado `GOOGLE_CALENDAR_ID`
- ✅ Adicionado scope `'https://www.googleapis.com/auth/calendar'`

### 4. `test_google_calendar.py` (Novo)

Suite de testes com **18 casos de teste** cobrindo:
- ✅ Cálculo de sexta-feira (7 testes)
- ✅ Validação de datas (5 testes)
- ✅ Geração de resumo (3 testes)
- ✅ Cenários completos (3 testes)

---

## 🔄 Fluxo de Execução

### No endpoint `/iniciar_implantacao`:

```
1. Calcular datas de homologação e virada
   ↓
2. Atualizar Zoho Projects
   ↓
3. Atualizar Planilha Google
   ↓
4. Processar tarefas de implantação
   ↓
5. 🆕 CRIAR EVENTOS NO GOOGLE CALENDAR ⬅️ NOVO
   ├── Criar evento de Homologação
   │   └── Retorna (sucesso, event_id, erro)
   ├── Criar evento de Virada
   │   └── Retorna (sucesso, event_id, erro)
   └── Retornar resultado consolidado
   ↓
6. Sincronizar banco local
```

### Extração do Nome do Cliente

O sistema extrai automaticamente o nome do cliente a partir do nome do projeto no Zoho, removendo sufixos técnicos e códigos:

**Lógica de Limpeza:**
1. Remove sufixos " - NR", " - AP", " - NR/AP"
2. Remove códigos numéricos no final (padrão: `\s+\d+$`)

**Exemplos:**
```python
"Hospital ABC - NR 001"              → "Hospital ABC"
"Clínica XYZ - AP 002"               → "Clínica XYZ"
"Centro Médico - NR/AP 003"          → "Centro Médico"
"Santa Casa de Misericórdia - NR 123" → "Santa Casa de Misericórdia"
"Hospital Regional"                  → "Hospital Regional"
```

**Código de Extração:**
```python
import re

nome_projeto = "Hospital ABC - NR 001"
nome_cliente = nome_projeto

# Remover sufixos
for padrao in [' - NR/AP', ' - NR', ' - AP']:
    if padrao in nome_cliente:
        nome_cliente = nome_cliente.split(padrao)[0].strip()
        break

# Remover código numérico no final
nome_cliente = re.sub(r'\s+\d+$', '', nome_cliente).strip()
# Resultado: "Hospital ABC"
```

---

## 📊 Lógica de Cálculo de Datas

### Cálculo da Sexta-feira da Semana

A função `_calcular_sexta_feira_da_semana()` determina a sexta-feira baseada no dia da semana:

| Dia de Início | Sexta-feira Retornada | Dias Adicionados |
|---------------|----------------------|------------------|
| Segunda (0)   | Sexta mesma semana   | +4 dias          |
| Terça (1)     | Sexta mesma semana   | +3 dias          |
| Quarta (2)    | Sexta mesma semana   | +2 dias          |
| Quinta (3)    | Sexta mesma semana   | +1 dia           |
| Sexta (4)     | Mesma sexta          | 0 dias           |
| Sábado (5)    | Sexta ANTERIOR       | -1 dia           |
| Domingo (6)   | Sexta ANTERIOR       | -2 dias          |

**Exemplo Prático:**
```python
# Início: Segunda, 20/10/2025
data_inicio = datetime(2025, 10, 20)  # Segunda

# Homologação: 20/10 (seg) a 24/10 (sex)
sexta_homolog = _calcular_sexta_feira_da_semana(data_inicio)
# Resultado: 24/10/2025 (Sexta)

# Virada: Uma semana depois
data_virada = data_inicio + timedelta(days=7)  # 27/10 (Segunda)
sexta_virada = _calcular_sexta_feira_da_semana(data_virada)
# Resultado: 31/10/2025 (Sexta)
```

### Formato dos Eventos

Os eventos seguem o padrão de **eventos de dia inteiro** do Google Calendar:

```python
evento = {
    'summary': 'Homologação Hospital XYZ (Remoto/Presencial)',
    'start': {
        'date': '2025-10-20',  # Sem hora (evento de dia inteiro)
        'timeZone': 'America/Sao_Paulo',
    },
    'end': {
        'date': '2025-10-25',  # Sexta + 1 dia (exclusivo)
        'timeZone': 'America/Sao_Paulo',
    },
    'description': 'Período de homologação do projeto Hospital XYZ',
    'colorId': '5',  # Amarelo
}
```

⚠️ **Importante:** O Google Calendar usa **data fim exclusiva** para eventos de dia inteiro. Se o evento deve terminar na sexta (24/10), a data fim deve ser sábado (25/10).

---

## ✅ Tratamento de Erros

### Erro Parcial (Um evento criado, outro falhou)

```python
# Homologação criada ✅, Virada falhou ❌
{
    'sucesso': False,
    'homologacao': {'criado': True, 'event_id': 'abc123', 'erro': None},
    'virada': {'criado': False, 'event_id': None, 'erro': 'API Error...'},
    'mensagem': '⚠️ Virada criada, mas Homologação falhou: API Error...'
}
```

**Comportamento:** O sistema continua a execução e registra o aviso nos detalhes.

### Erro Total (Ambos falharam)

```python
{
    'sucesso': False,
    'homologacao': {'criado': False, 'event_id': None, 'erro': 'No permission'},
    'virada': {'criado': False, 'event_id': None, 'erro': 'No permission'},
    'mensagem': '❌ Falha ao criar ambos os eventos...'
}
```

**Comportamento:** O sistema continua (não bloqueia o agendamento) e registra o erro nos detalhes.

### Mensagens ao Usuário

As mensagens são adicionadas ao array `detalhes_msg` retornado ao frontend:

**Sucesso Total:**
```
✅ Eventos criados no Google Calendar:
   • Homologação: abc123def456
   • Virada: xyz789ghi012
```

**Sucesso Parcial:**
```
✅ Evento de Homologação criado: abc123def456
⚠️ Falha ao criar evento de Virada: Erro HTTP 403
```

**Falha Total:**
```
⚠️ Aviso: Falha ao criar eventos no Google Calendar: No permission
```

---

## 🧪 Testes

### Executar Testes

```bash
python test_google_calendar.py
```

### Cobertura de Testes

**18 testes automatizados:**

1. **Cálculo de Sexta-feira (7 testes):**
   - ✅ Segunda → Sexta (+4 dias)
   - ✅ Terça → Sexta (+3 dias)
   - ✅ Quarta → Sexta (+2 dias)
   - ✅ Quinta → Sexta (+1 dia)
   - ✅ Sexta → Mesma sexta (0 dias)
   - ✅ Sábado → Sexta anterior (-1 dia)
   - ✅ Domingo → Sexta anterior (-2 dias)

2. **Validação de Datas (5 testes):**
   - ✅ Datas válidas (YYYY-MM-DD)
   - ✅ Formatos incorretos (DD/MM/YYYY, etc.)
   - ✅ Valores inválidos (mês 13, 30 fev)
   - ✅ String vazia ou None
   - ✅ Strings aleatórias

3. **Resumo de Eventos (3 testes):**
   - ✅ Semana normal
   - ✅ Formatação de períodos
   - ✅ Datas inválidas

4. **Cenários Completos (3 testes):**
   - ✅ Implantação padrão (segunda-feira)
   - ✅ Início no meio da semana
   - ✅ Edge case: início em sexta

**Resultado Esperado:**
```
======================================================================
RESUMO DOS TESTES
======================================================================
✅ Testes executados: 18
✅ Sucessos: 18
❌ Falhas: 0
❌ Erros: 0

🎉 TODOS OS TESTES PASSARAM! 🎉
```

---

## 🔍 Logs e Debug

### Logs Detalhados

O módulo gera logs detalhados em todas as etapas:

```
[DEBUG][GOOGLE_CALENDAR] Criando evento de Homologação:
[DEBUG][GOOGLE_CALENDAR]   📋 Título: Homologação Hospital XYZ (Remoto/Presencial)
[DEBUG][GOOGLE_CALENDAR]   📅 Início: 20/10/2025 (Monday)
[DEBUG][GOOGLE_CALENDAR]   📅 Fim: 24/10/2025 (Friday)
[DEBUG][GOOGLE_CALENDAR]   📧 Calendar ID: animati.com.br_g82f2343cocg9tgr5soplsl210@group.calendar.google.com

[INFO][GOOGLE_CALENDAR] ✅ Evento de Homologação criado com sucesso!
[INFO][GOOGLE_CALENDAR]    🔗 ID: abc123def456
[INFO][GOOGLE_CALENDAR]    🔗 Link: https://calendar.google.com/...
```

### Logs no Endpoint

```
[INFO][INICIAR_IMPLANTACAO] ===== ETAPA 4: CRIANDO EVENTOS NO GOOGLE CALENDAR =====
[DEBUG][INICIAR_IMPLANTACAO] Criando eventos para cliente: Hospital XYZ
[DEBUG][INICIAR_IMPLANTACAO] Data Homologação: 2025-10-20
[DEBUG][INICIAR_IMPLANTACAO] Data Virada: 2025-10-27
[SUCCESS][INICIAR_IMPLANTACAO] Eventos criados com sucesso no Google Calendar
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Implantação Completa

**Entrada:**
```python
nome_cliente = "Hospital Santa Maria"
data_inicio = "2025-10-20"  # Segunda-feira
```

**Cálculo Automático:**
```python
# Sistema calcula:
data_homologacao = "2025-10-20"  # Segunda (mesma data início)
data_virada = "2025-10-27"       # Segunda (1 semana depois)
```

**Eventos Criados:**

1. **Homologação:**
   - Título: `Homologação Hospital Santa Maria (Remoto/Presencial)`
   - Período: 20/10/2025 a 24/10/2025 (Seg a Sex)
   - Cor: Amarelo

2. **Virada:**
   - Título: `Virada Hospital Santa Maria (Remoto/Presencial)`
   - Período: 27/10/2025 a 31/10/2025 (Seg a Sex)
   - Cor: Vermelho

### Exemplo 2: Início no Meio da Semana

**Entrada:**
```python
nome_cliente = "Clínica São Paulo"
data_inicio = "2025-10-22"  # Quarta-feira
```

**Eventos Criados:**

1. **Homologação:**
   - Período: 22/10/2025 a 24/10/2025 (Qua a Sex)
   - ⚠️ Apenas 3 dias (quarta, quinta, sexta)

2. **Virada:**
   - Período: 29/10/2025 a 31/10/2025 (Qua a Sex)

---

## 🚀 Melhorias Futuras

### Possíveis Expansões

1. **Modalidade Dinâmica:**
   - Permitir que usuário escolha "Remoto", "Presencial" ou "Híbrido"
   - Adicionar campo no modal de agendamento

2. **Participantes:**
   - Adicionar implantadores automaticamente como participantes
   - Email: `implantador@animati.com.br`

3. **Lembretes:**
   - Adicionar notificações 1 dia antes
   - Email/pop-up no Google Calendar

4. **Descrição Expandida:**
   - Incluir informações do projeto
   - Link para o Zoho Projects
   - Produtos contratados (RIS/PACS)

5. **Cores Customizadas:**
   - Baseada no tipo de produto
   - RIS: Azul, PACS: Verde, Híbrido: Roxo

---

## ⚙️ Dependências

### Bibliotecas Python

```python
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
```

**Já instaladas via `requirements.txt`:**
- ✅ `google-api-python-client==2.136.0`
- ✅ `google-auth-httplib2==0.2.0`
- ✅ `google-auth-oauthlib==1.2.0`

### Permissões Necessárias

- ✅ Google Calendar API habilitada
- ✅ Scope `https://www.googleapis.com/auth/calendar`
- ✅ Acesso ao calendar ID específico
- ✅ Credenciais OAuth 2.0 configuradas

---

## 🎯 Benefícios

### Para a Equipe

1. **Visibilidade:** Todos veem homologações e viradas no mesmo calendário
2. **Organização:** Não precisa criar eventos manualmente
3. **Consistência:** Títulos e formatos padronizados
4. **Automação:** Reduz trabalho manual e erros

### Para o Sistema

1. **Integração:** Conecta Zoho Projects ↔ Google Calendar
2. **Rastreabilidade:** Event IDs permitem atualizações futuras
3. **Confiabilidade:** Testes garantem cálculos corretos
4. **Robustez:** Tratamento de erros não bloqueia o fluxo principal

---

## 📞 Suporte

### Problemas Comuns

**1. Erro: "Insufficient Permission"**
- ✅ Verificar se scope de Calendar está em `SCOPES_GOOGLE`
- ✅ Re-autenticar no sistema (logout → login)

**2. Eventos não aparecem no calendário**
- ✅ Confirmar `GOOGLE_CALENDAR_ID` correto
- ✅ Verificar se usuário tem acesso ao calendário compartilhado

**3. Datas calculadas erradas**
- ✅ Executar `python test_google_calendar.py`
- ✅ Verificar timezone (deve ser `America/Sao_Paulo`)

---

**Última atualização:** 13/10/2025  
**Versão:** 1.0.0  
**Autor:** Sistema de Automação Animati
