#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversión de tipos de Python a JSON.

Las consultas devuelven date, datetime, time y Decimal, que json.dumps no
sabe convertir por sí solo.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal


def serializar(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, bytes):
        return valor.decode("utf-8", "replace")
    return str(valor)
