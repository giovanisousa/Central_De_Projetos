# -*- coding: utf-8 -*-
"""
Módulo para integração com Google Calendar.
Gerencia criação de eventos de Homologação e Virada na agenda de implantação.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CALENDAR_ID


def _calcular_sexta_feira_da_semana(data_inicio: datetime) -> datetime:
    """
    Calcula a sexta-feira da mesma semana de uma data.
    
    Args:
        data_inicio: Data de início (datetime object)
    
    Returns:
        datetime da sexta-feira da mesma semana
    
    Examples:
        >>> # Se data_inicio é segunda (0), sexta é +4 dias
        >>> # Se data_inicio é quinta (3), sexta é +1 dia
        >>> # Se data_inicio é sexta (4), retorna a própria data
    """
    # weekday(): 0=segunda, 1=terça, 2=quarta, 3=quinta, 4=sexta, 5=sábado, 6=domingo
    dia_da_semana = data_inicio.weekday()
    
    # Calcular quantos dias faltam até sexta-feira (4)
    dias_ate_sexta = (4 - dia_da_semana) % 7
    
    # Se já é sexta ou depois, pega a sexta da mesma semana (0 dias)
    if dia_da_semana == 4:  # Sexta
        return data_inicio
    elif dia_da_semana > 4:  # Sábado ou Domingo
        # Retornar a sexta anterior (mesma semana de trabalho)
        dias_ate_sexta = 4 - dia_da_semana
    
    data_sexta = data_inicio + timedelta(days=dias_ate_sexta)
    return data_sexta


def criar_evento_homologacao(
    credentials,
    nome_cliente: str,
    data_homologacao: str,
    modalidade: str = "Remoto/Presencial"
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Cria evento de Homologação no Google Calendar.
    
    O evento será criado com:
    - Título: "Homologação {NOME_CLIENTE} (Remoto/Presencial)"
    - Data início: data_homologacao (segunda-feira)
    - Data fim: sexta-feira da mesma semana
    - Evento de dia inteiro
    
    Args:
        credentials: Credenciais Google autenticadas
        nome_cliente: Nome do cliente para o título do evento
        data_homologacao: Data de início da homologação no formato 'YYYY-MM-DD'
        modalidade: "Remoto", "Presencial" ou "Remoto/Presencial" (padrão)
    
    Returns:
        Tupla (sucesso, event_id, mensagem_erro)
        - sucesso: True se evento foi criado com sucesso
        - event_id: ID do evento criado (None se falhou)
        - mensagem_erro: Mensagem de erro (None se sucesso)
    
    Examples:
        >>> criar_evento_homologacao(creds, "Hospital XYZ", "2025-10-20", "Remoto")
        (True, "abc123def456", None)
    """
    try:
        # Parse da data
        data_inicio = datetime.strptime(data_homologacao, '%Y-%m-%d')
        
        # Calcular sexta-feira da mesma semana
        data_fim = _calcular_sexta_feira_da_semana(data_inicio)
        
        # Ajustar para o dia seguinte (Google Calendar usa data fim exclusiva para eventos de dia inteiro)
        data_fim_exclusiva = data_fim + timedelta(days=1)
        
        # Montar título do evento
        summary = f"Homologação {nome_cliente} ({modalidade})"
        
        # Criar evento
        evento = {
            'summary': summary,
            'start': {
                'date': data_inicio.strftime('%Y-%m-%d'),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'date': data_fim_exclusiva.strftime('%Y-%m-%d'),
                'timeZone': 'America/Sao_Paulo',
            },
            'description': f'Período de homologação do projeto {nome_cliente}',
            'colorId': '3',  # Magenta (cor para homologação)
        }
        
        print(f"[DEBUG][GOOGLE_CALENDAR] Criando evento de Homologação:")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📋 Título: {summary}")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📅 Início: {data_inicio.strftime('%d/%m/%Y (%A)')}")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📅 Fim: {data_fim.strftime('%d/%m/%Y (%A)')}")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📧 Calendar ID: {GOOGLE_CALENDAR_ID}")
        
        # Criar serviço do Google Calendar
        service = build('calendar', 'v3', credentials=credentials)
        
        # Inserir evento no calendário
        evento_criado = service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID,
            body=evento
        ).execute()
        
        event_id = evento_criado.get('id')
        event_link = evento_criado.get('htmlLink')
        
        print(f"[INFO][GOOGLE_CALENDAR] ✅ Evento de Homologação criado com sucesso!")
        print(f"[INFO][GOOGLE_CALENDAR]    🔗 ID: {event_id}")
        print(f"[INFO][GOOGLE_CALENDAR]    🔗 Link: {event_link}")
        
        return True, event_id, None
        
    except HttpError as e:
        erro_msg = f"Erro HTTP ao criar evento de homologação: {e}"
        print(f"[ERROR][GOOGLE_CALENDAR] {erro_msg}")
        return False, None, erro_msg
        
    except ValueError as e:
        erro_msg = f"Data inválida '{data_homologacao}': {e}"
        print(f"[ERROR][GOOGLE_CALENDAR] {erro_msg}")
        return False, None, erro_msg
        
    except Exception as e:
        erro_msg = f"Erro inesperado ao criar evento de homologação: {e}"
        print(f"[ERROR][GOOGLE_CALENDAR] {erro_msg}")
        return False, None, erro_msg


def criar_evento_virada(
    credentials,
    nome_cliente: str,
    data_virada: str,
    modalidade: str = "Remoto/Presencial"
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Cria evento de Virada no Google Calendar.
    
    O evento será criado com:
    - Título: "Virada {NOME_CLIENTE} (Remoto/Presencial)"
    - Data início: data_virada (segunda-feira)
    - Data fim: sexta-feira da mesma semana
    - Evento de dia inteiro
    
    Args:
        credentials: Credenciais Google autenticadas
        nome_cliente: Nome do cliente para o título do evento
        data_virada: Data de início da virada no formato 'YYYY-MM-DD'
        modalidade: "Remoto", "Presencial" ou "Remoto/Presencial" (padrão)
    
    Returns:
        Tupla (sucesso, event_id, mensagem_erro)
        - sucesso: True se evento foi criado com sucesso
        - event_id: ID do evento criado (None se falhou)
        - mensagem_erro: Mensagem de erro (None se sucesso)
    
    Examples:
        >>> criar_evento_virada(creds, "Hospital XYZ", "2025-10-27", "Presencial")
        (True, "xyz789ghi012", None)
    """
    try:
        # Parse da data
        data_inicio = datetime.strptime(data_virada, '%Y-%m-%d')
        
        # Calcular sexta-feira da mesma semana
        data_fim = _calcular_sexta_feira_da_semana(data_inicio)
        
        # Ajustar para o dia seguinte (Google Calendar usa data fim exclusiva para eventos de dia inteiro)
        data_fim_exclusiva = data_fim + timedelta(days=1)
        
        # Montar título do evento
        summary = f"Virada {nome_cliente} ({modalidade})"
        
        # Criar evento
        evento = {
            'summary': summary,
            'start': {
                'date': data_inicio.strftime('%Y-%m-%d'),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'date': data_fim_exclusiva.strftime('%Y-%m-%d'),
                'timeZone': 'America/Sao_Paulo',
            },
            'description': f'Período de virada do projeto {nome_cliente}',
            'colorId': '3',  # Magenta (cor para virada)
        }
        
        print(f"[DEBUG][GOOGLE_CALENDAR] Criando evento de Virada:")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📋 Título: {summary}")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📅 Início: {data_inicio.strftime('%d/%m/%Y (%A)')}")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📅 Fim: {data_fim.strftime('%d/%m/%Y (%A)')}")
        print(f"[DEBUG][GOOGLE_CALENDAR]   📧 Calendar ID: {GOOGLE_CALENDAR_ID}")
        
        # Criar serviço do Google Calendar
        service = build('calendar', 'v3', credentials=credentials)
        
        # Inserir evento no calendário
        evento_criado = service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID,
            body=evento
        ).execute()
        
        event_id = evento_criado.get('id')
        event_link = evento_criado.get('htmlLink')
        
        print(f"[INFO][GOOGLE_CALENDAR] ✅ Evento de Virada criado com sucesso!")
        print(f"[INFO][GOOGLE_CALENDAR]    🔗 ID: {event_id}")
        print(f"[INFO][GOOGLE_CALENDAR]    🔗 Link: {event_link}")
        
        return True, event_id, None
        
    except HttpError as e:
        erro_msg = f"Erro HTTP ao criar evento de virada: {e}"
        print(f"[ERROR][GOOGLE_CALENDAR] {erro_msg}")
        return False, None, erro_msg
        
    except ValueError as e:
        erro_msg = f"Data inválida '{data_virada}': {e}"
        print(f"[ERROR][GOOGLE_CALENDAR] {erro_msg}")
        return False, None, erro_msg
        
    except Exception as e:
        erro_msg = f"Erro inesperado ao criar evento de virada: {e}"
        print(f"[ERROR][GOOGLE_CALENDAR] {erro_msg}")
        return False, None, erro_msg


def criar_eventos_implantacao(
    credentials,
    nome_cliente: str,
    data_homologacao: str,
    data_virada: str,
    modalidade: str = "Remoto/Presencial"
) -> Dict[str, any]:
    """
    Cria ambos os eventos (Homologação e Virada) no Google Calendar.
    
    Função de conveniência que cria os dois eventos de uma vez.
    
    Args:
        credentials: Credenciais Google autenticadas
        nome_cliente: Nome do cliente para os títulos dos eventos
        data_homologacao: Data de início da homologação no formato 'YYYY-MM-DD'
        data_virada: Data de início da virada no formato 'YYYY-MM-DD'
        modalidade: "Remoto", "Presencial" ou "Remoto/Presencial" (padrão)
    
    Returns:
        Dict com resultado de ambas as operações:
        {
            'sucesso': bool,  # True se AMBOS foram criados com sucesso
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
    
    Examples:
        >>> criar_eventos_implantacao(creds, "Hospital XYZ", "2025-10-20", "2025-10-27")
        {
            'sucesso': True,
            'homologacao': {'criado': True, 'event_id': 'abc123', 'erro': None},
            'virada': {'criado': True, 'event_id': 'xyz789', 'erro': None},
            'mensagem': '✅ Eventos criados: Homologação (abc123), Virada (xyz789)'
        }
    """
    print(f"[INFO][GOOGLE_CALENDAR] ===== CRIANDO EVENTOS DE IMPLANTAÇÃO =====")
    print(f"[INFO][GOOGLE_CALENDAR] Cliente: {nome_cliente}")
    print(f"[INFO][GOOGLE_CALENDAR] Modalidade: {modalidade}")
    
    resultado = {
        'sucesso': False,
        'homologacao': {'criado': False, 'event_id': None, 'erro': None},
        'virada': {'criado': False, 'event_id': None, 'erro': None},
        'mensagem': ''
    }
    
    # Criar evento de Homologação
    print(f"[INFO][GOOGLE_CALENDAR] 1/2 - Criando evento de Homologação...")
    sucesso_homolog, event_id_homolog, erro_homolog = criar_evento_homologacao(
        credentials, nome_cliente, data_homologacao, modalidade
    )
    
    resultado['homologacao'] = {
        'criado': sucesso_homolog,
        'event_id': event_id_homolog,
        'erro': erro_homolog
    }
    
    # Criar evento de Virada
    print(f"[INFO][GOOGLE_CALENDAR] 2/2 - Criando evento de Virada...")
    sucesso_virada, event_id_virada, erro_virada = criar_evento_virada(
        credentials, nome_cliente, data_virada, modalidade
    )
    
    resultado['virada'] = {
        'criado': sucesso_virada,
        'event_id': event_id_virada,
        'erro': erro_virada
    }
    
    # Avaliar resultado geral
    if sucesso_homolog and sucesso_virada:
        resultado['sucesso'] = True
        resultado['mensagem'] = (
            f"✅ Eventos criados com sucesso!\n"
            f"   📅 Homologação: {event_id_homolog}\n"
            f"   📅 Virada: {event_id_virada}"
        )
        print(f"[INFO][GOOGLE_CALENDAR] {resultado['mensagem']}")
        
    elif sucesso_homolog and not sucesso_virada:
        resultado['mensagem'] = (
            f"⚠️ Homologação criada ({event_id_homolog}), mas Virada falhou: {erro_virada}"
        )
        print(f"[WARN][GOOGLE_CALENDAR] {resultado['mensagem']}")
        
    elif not sucesso_homolog and sucesso_virada:
        resultado['mensagem'] = (
            f"⚠️ Virada criada ({event_id_virada}), mas Homologação falhou: {erro_homolog}"
        )
        print(f"[WARN][GOOGLE_CALENDAR] {resultado['mensagem']}")
        
    else:
        resultado['mensagem'] = (
            f"❌ Falha ao criar ambos os eventos.\n"
            f"   Homologação: {erro_homolog}\n"
            f"   Virada: {erro_virada}"
        )
        print(f"[ERROR][GOOGLE_CALENDAR] {resultado['mensagem']}")
    
    print(f"[INFO][GOOGLE_CALENDAR] ===== PROCESSO FINALIZADO =====")
    return resultado


# === FUNÇÕES AUXILIARES PARA VALIDAÇÃO ===

def validar_data_formato(data_str: str) -> bool:
    """
    Valida se uma string está no formato YYYY-MM-DD.
    
    Args:
        data_str: String com a data
    
    Returns:
        True se formato válido, False caso contrário
    """
    try:
        datetime.strptime(data_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def obter_resumo_eventos(data_homologacao: str, data_virada: str) -> Dict[str, str]:
    """
    Retorna um resumo formatado dos períodos dos eventos.
    
    Args:
        data_homologacao: Data de início da homologação 'YYYY-MM-DD'
        data_virada: Data de início da virada 'YYYY-MM-DD'
    
    Returns:
        Dict com informações formatadas dos períodos
    """
    try:
        dt_homolog = datetime.strptime(data_homologacao, '%Y-%m-%d')
        dt_virada = datetime.strptime(data_virada, '%Y-%m-%d')
        
        sexta_homolog = _calcular_sexta_feira_da_semana(dt_homolog)
        sexta_virada = _calcular_sexta_feira_da_semana(dt_virada)
        
        return {
            'homologacao_inicio': dt_homolog.strftime('%d/%m/%Y (%A)'),
            'homologacao_fim': sexta_homolog.strftime('%d/%m/%Y (%A)'),
            'homologacao_periodo': f"{dt_homolog.strftime('%d/%m')} a {sexta_homolog.strftime('%d/%m/%Y')}",
            'virada_inicio': dt_virada.strftime('%d/%m/%Y (%A)'),
            'virada_fim': sexta_virada.strftime('%d/%m/%Y (%A)'),
            'virada_periodo': f"{dt_virada.strftime('%d/%m')} a {sexta_virada.strftime('%d/%m/%Y')}"
        }
    except Exception as e:
        print(f"[ERROR][GOOGLE_CALENDAR] Erro ao gerar resumo: {e}")
        return {}
