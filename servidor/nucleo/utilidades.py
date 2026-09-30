#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades de validación y formato.

Convierten lo que llega por HTTP (texto suelto) a los tipos del dominio,
lanzando ErrorApi cuando el dato no es válido.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from nucleo.errores import fallo


def txt(valor, limite: int = 200) -> str:
    return ("" if valor is None else str(valor)).strip()[:limite]


def entero(valor, defecto: int = 0) -> int:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return defecto


def monto(valor) -> Decimal:
    try:
        return Decimal(str(valor if valor not in (None, "") else 0)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        fallo("El monto indicado no es válido.")


def a_fecha(valor, defecto=None):
    texto = txt(valor, 10)
    if not texto:
        return defecto
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        fallo("La fecha debe tener el formato AAAA-MM-DD.")


def a_hora(valor):
    texto = txt(valor, 8)
    if not texto:
        fallo("Indique la hora de la cita.")
    for formato in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    fallo("La hora debe tener el formato HH:MM.")


def hace_falta(condicion, mensaje: str, codigo: int = 400):
    if not condicion:
        fallo(mensaje, codigo)


def nombre_cliente(fila) -> str:
    if not fila:
        return "—"
    partes = [fila.get("Noms_Cliente"), fila.get("Ape_Pat_Cliente"), fila.get("Ape_Mat_Cliente")]
    return " ".join(p for p in partes if p).strip() or "—"


def nombre_podologo(fila) -> str:
    if not fila:
        return "—"
    partes = [fila.get("Nom_Podologo"), fila.get("Ape_Pat_Podo"), fila.get("Ape_Mat_Podo")]
    return " ".join(p for p in partes if p).strip() or "—"
