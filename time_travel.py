"""
Módulo para simular viagem no tempo para testes
"""
from datetime import datetime, timezone
from typing import Optional

# Variável global para armazenar a data/hora de "viagem"
_time_travel_date: Optional[datetime] = None

def set_travel_date(date_str: str) -> datetime:
    """
    Define a data de viagem no tempo.
    
    Args:
        date_str: Data em formato "DD/MM/YYYY" ou "DD/MM/YYYY HH:MM"
    
    Returns:
        datetime: A data configurada em UTC
    
    Raises:
        ValueError: Se o formato da data for inválido
    """
    global _time_travel_date
    
    try:
        if len(date_str) == 10:  # "DD/MM/YYYY"
            _time_travel_date = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=timezone.utc)
        elif len(date_str) == 16:  # "DD/MM/YYYY HH:MM"
            _time_travel_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
        else:
            raise ValueError("Formato inválido")
        
        print(f"⏰ Data de viagem definida para: {_time_travel_date.strftime('%d/%m/%Y %H:%M')}")
        return _time_travel_date
    except ValueError as e:
        raise ValueError(f"Erro ao processar data: {e}")

def get_current_time() -> datetime:
    """
    Retorna a data/hora atual, considerando viagem no tempo se configurada.
    
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
