#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reglas de facturación — R2, R4 y R5.

R2: la suma de los pagos de una boleta no puede superar su importe. La boleta
    pasa a "Pagada" solo cuando los pagos igualan el importe.
R4: una boleta pagada y cerrada no se modifica ni se elimina. Lo refuerza el
    trigger TR_BOLETA_NoEliminarPagada en SQL Server.
R5: no se emite boleta si no existe una atención con su cliente registrado.
"""

from __future__ import annotations

from decimal import Decimal

from datos import escalar, uno
from nucleo.errores import fallo
from nucleo.utilidades import hace_falta

TIPOS_PAGO = ("Efectivo", "Tarjeta", "Yape", "Transferencia")


def atencion_facturable(id_atencion: int) -> dict:
    """Regla R5 — la atención debe existir y tener su cliente registrado."""
    atencion = uno(
        """SELECT a.Id_Atencion, c.Id_Cliente, cl.Noms_Cliente
           FROM ATENCION a
           JOIN CITA c ON c.Id_Cita = a.Id_Cita
           JOIN CLIENTE cl ON cl.Id_Cliente = c.Id_Cliente
           WHERE a.Id_Atencion = ?""",
        (id_atencion,),
    )
    hace_falta(atencion, "Regla R5: la atención o el cliente no existen.", 404)
    hace_falta(not escalar("SELECT COUNT(*) FROM BOLETA WHERE Id_Atencion = ?", (id_atencion,), 0),
               "Esa atención ya tiene una boleta emitida.")
    return atencion


def verificar_boleta_abierta(tx, id_boleta: int) -> dict:
    """Regla R4 — una boleta pagada y cerrada no admite más movimientos."""
    boleta = tx.uno("SELECT * FROM BOLETA WITH (UPDLOCK) WHERE Id_Boleta = ?", (id_boleta,))
    hace_falta(boleta, "La boleta no existe.", 404)
    hace_falta(boleta["Estado_Pago"] != "Pagada", "Regla R4: esta boleta ya está pagada y cerrada.")
    return boleta


def saldo_pendiente(tx, boleta: dict) -> Decimal:
    """Regla R2 — cuánto falta por cobrar de una boleta ya bloqueada."""
    pagado = Decimal(str(tx.uno(
        "SELECT ISNULL(SUM(Monto),0) t FROM PAGO WHERE Id_Boleta = ?", (boleta["Id_Boleta"],)
    )["t"]))
    return Decimal(str(boleta["Importe"])) - pagado


def estado_segun_saldo(saldo: Decimal) -> str:
    return "Pagada" if saldo == 0 else "Pendiente"


def verificar_boleta_anulable(id_boleta: int) -> dict:
    """Regla R4 — no se elimina una boleta pagada ni una que tenga pagos."""
    boleta = uno("SELECT * FROM BOLETA WHERE Id_Boleta = ?", (id_boleta,))
    hace_falta(boleta, "La boleta no existe.", 404)
    hace_falta(boleta["Estado_Pago"] != "Pagada",
               "Regla R4: una boleta pagada no se puede eliminar.")
    hace_falta(not escalar("SELECT COUNT(*) FROM PAGO WHERE Id_Boleta = ?", (id_boleta,), 0),
               "La boleta tiene pagos registrados: no se puede eliminar.")
    return boleta
