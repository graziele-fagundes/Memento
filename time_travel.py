"""
Módulo para simular viagem no tempo para testes
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import time

# Variável global para armazenar a data/hora de "viagem"
_time_travel_date: Optional[datetime] = None

def _get_local_timezone_offset() -> timedelta:
    """
    Detecta o offset do timezone local do sistema.
    
    Returns:
        timedelta: Offset do timezone local
    """
    # Detecta o offset do timezone local
    if time.daylight:
        offset_seconds = -time.altzone
    else:
        offset_seconds = -time.timezone
    
    return timedelta(seconds=offset_seconds)

def _local_to_utc(dt: datetime) -> datetime:
    """
    Converte um datetime naive (sem timezone) interpretado como hora local para UTC.
    
    Args:
        dt: datetime naive (sem timezone)
    
    Returns:
        datetime: datetime em UTC
    """
    # Detecta offset local
    offset = _get_local_timezone_offset()
    
    # Cria um datetime UTC subtraindo o offset
    # Se o offset é -3 (São Paulo), então local = UTC - 3, logo UTC = local + 3
    utc_dt = dt - offset
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    return utc_dt

def set_travel_date(date_str: str) -> datetime:
    """
    Define a data de viagem no tempo.
    
    Args:
        date_str: Data em formato "DD/MM/YYYY" ou "DD/MM/YYYY HH:MM"
                 Interpretada como hora local do usuário e convertida para UTC
    
    Returns:
        datetime: A data configurada em UTC
    
    Raises:
        ValueError: Se o formato da data for inválido
    """
    global _time_travel_date
    
    try:
        if len(date_str) == 10:  # "DD/MM/YYYY"
            local_dt = datetime.strptime(date_str, "%d/%m/%Y")
            _time_travel_date = _local_to_utc(local_dt)
        elif len(date_str) == 16:  # "DD/MM/YYYY HH:MM"
            local_dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            _time_travel_date = _local_to_utc(local_dt)
        else:
            raise ValueError("Formato inválido")
        
        # Mostra em hora local para o usuário entender melhor
        local_time = _time_travel_date - _get_local_timezone_offset()
        print(f"⏰ Data de viagem definida para: {local_time.strftime('%d/%m/%Y %H:%M')} (horário local)")
        print(f"   UTC: {_time_travel_date.strftime('%d/%m/%Y %H:%M')}")
        return _time_travel_date
    except ValueError as e:
        raise ValueError(f"Erro ao processar data: {e}")

def get_current_time() -> datetime:
    """
    Retorna a data/hora atual, considerando viagem no tempo se configurada.
    Sempre retorna em UTC com timezone aware.
    
    Returns:
        datetime: Data/hora em UTC
    """
    if _time_travel_date is not None:
        return _time_travel_date
    return datetime.now(timezone.utc)

def reset_travel_date():
    """Reseta a viagem no tempo para a data/hora real."""
    global _time_travel_date
    _time_travel_date = None
    print("⏰ Viagem no tempo desativada. Usando data/hora real.")

def is_traveling():
    """Verifica se está em viagem no tempo."""
    return _time_travel_date is not None

def utc_to_local(utc_dt: datetime) -> datetime:
    """
    Converte um datetime UTC para hora local.
    
    Args:
        utc_dt: datetime em UTC
    
    Returns:
        datetime: datetime em hora local (naive, sem tzinfo)
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    offset = _get_local_timezone_offset()
    local_dt = utc_dt + offset
    return local_dt.replace(tzinfo=None)

def prompt_for_travel_date() -> datetime:
    """
    Pergunta ao usuário qual data deseja usar para a revisão.
    
    Returns:
        datetime: Data escolhida em UTC
    """
    while True:
        try:
            date_input = input(
                "\n⏰ Que dia você quer usar para esta revisão?\n"
                "   Formato: DD/MM/YYYY ou DD/MM/YYYY HH:MM\n"
                "   (Digite 'agora' para usar a data real)\n"
                "   > "
            ).strip()
            
            if date_input.lower() == 'agora':
                reset_travel_date()
                return get_current_time()
            
            return set_travel_date(date_input)
        except ValueError as e:
            print(f"❌ {e}. Tente novamente.")
