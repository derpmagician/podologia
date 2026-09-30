#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reglas de las atenciones clínicas.

Una atención ya facturada queda bloqueada para el podólogo (regla R4): no se
puede modificar su ficha ni cambiar sus consumos.
"""

from __future__ import annotations

from datos import uno
from nucleo.errores import fallo
from nucleo.utilidades import hace_falta


def totales(tx, id_atencion: int) -> dict:
    """Suma de servicios y medicamentos de una atención, dentro de una transacción."""
    servicios = tx.uno(
        "SELECT ISNULL(SUM(Subt_Aten),0) t FROM DETALLE_ATENCION WHERE Id_Atencion = ?", (id_atencion,)
    )["t"]
    medicamentos = tx.uno(
        "SELECT ISNULL(SUM(Subt_Med),0) t FROM DETALLE_MEDICAMENTO WHERE Id_Atencion = ?", (id_atencion,)
    )["t"]
    return {"servicios": float(servicios), "medicamentos": float(medicamentos),
            "total": float(servicios) + float(medicamentos)}


def abierta(id_atencion: int) -> dict:
    """Devuelve la atención solo si todavía se le puede mover dinero."""
    fila = uno(
        """SELECT a.*, c.Id_Podologo,
                  (SELECT COUNT(*) FROM BOLETA b WHERE b.Id_Atencion = a.Id_Atencion) AS Boletas
           FROM ATENCION a JOIN CITA c ON c.Id_Cita = a.Id_Cita
           WHERE a.Id_Atencion = ?""",
        (id_atencion,),
    )
    hace_falta(fila, "La atención no existe.", 404)
    if fila["Boletas"]:
        fallo("Regla R4: la atención ya fue facturada; no se pueden cambiar sus consumos.")
    return fila


def solo_su_podologo(fila: dict, peticion, mensaje: str) -> None:
    """Un podólogo únicamente opera sobre sus propias citas."""
    if peticion.rol == "Podologo" and fila["Id_Podologo"] != peticion.sesion["id_podologo"]:
        fallo(mensaje, 403)
