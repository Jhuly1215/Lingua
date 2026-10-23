"""
Utilidades auxiliares para LINGUA.
"""
import re
from datetime import date
from typing import Optional


def sanitize_string(text: Optional[str]) -> Optional[str]:
    """Limpia espacios en blanco al inicio y final y normaliza cadenas."""
    if text is None:
        return None
    cleaned = text.strip()
    return cleaned if cleaned else None


def calculate_age(birth_date: date, reference_date: Optional[date] = None) -> int:
    """Calcula la edad en años completos a partir de la fecha de nacimiento."""
    if reference_date is None:
        reference_date = date.today()
    return (
        reference_date.year
        - birth_date.year
        - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))
    )
