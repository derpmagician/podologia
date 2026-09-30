#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reglas de las citas — R1.

R1: un podólogo no puede tener dos citas activas a la misma fecha y hora.
    Se refuerza en dos niveles: aquí antes de grabar, y con el índice único
    filtrado UX_CITA_Podologo_Fecha_Hora en SQL Server (por si dos peticiones
    simultáneas pasan la validación a la vez).
"""

from __future__ import annotations

from datos import uno
from nucleo.errores import fallo

ESTADOS = ("Programada", "Atendida", "Cancelada", "No asistio")


def verificar_estado(estado: str) -> None:
    if estado not in ESTADOS:
        fallo("El estado de la cita no es válido.")


def verificar_disponibilidad(id_podologo: int, fe_cita, hora_cita, id_cita: int = 0) -> None:
    """Regla R1 — el podólogo no puede tener dos citas a la misma fecha y hora."""
    choque = uno(
        """SELECT c.Id_Cita, cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') AS Cliente
           FROM CITA c JOIN CLIENTE cl ON cl.Id_Cliente = c.Id_Cliente
           WHERE c.Id_Podologo = ? AND c.Fe_Cita = ? AND c.Hora_Cita = ?
             AND c.Estado <> 'Cancelada' AND c.Id_Cita <> ?""",
        (id_podologo, fe_cita, hora_cita, id_cita),
    )
    if choque:
        fallo("Regla R1: el podólogo ya tiene una cita a las %s con %s."
              % (hora_cita.strftime("%H:%M"), choque["Cliente"]))
