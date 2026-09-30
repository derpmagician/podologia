#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Caja: boletas y pagos — reglas R2, R4 y R5.

El importe de la boleta siempre se calcula sumando los detalles de la
atención (nunca se digita a mano). Las validaciones viven en
dominio/facturacion.py.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from api.enrutador import Peticion, ruta
from datos import Tx, consultar, ejecutar, uno
from dominio.atenciones import totales
from dominio.facturacion import (
    TIPOS_PAGO,
    atencion_facturable,
    estado_segun_saldo,
    saldo_pendiente,
    verificar_boleta_abierta,
    verificar_boleta_anulable,
)
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN, ADMIN_RECEP
from nucleo.utilidades import a_fecha, entero, hace_falta, monto


@ruta("GET", "/api/boletas", ADMIN_RECEP)
def api_boletas(p: Peticion):
    estado = p.filtro("estado", 20)
    desde = p.filtro("desde", 10)
    hasta = p.filtro("hasta", 10)
    sql = """
        SELECT b.Id_Boleta, b.Id_Atencion, b.Fe_Emision, b.Importe, b.Estado_Pago,
               r.Noms_Recep + ' ' + ISNULL(r.Apellidos_Recep,'') AS Recepcionista,
               cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') + ' ' + ISNULL(cl.Ape_Mat_Cliente,'') AS Cliente,
               cl.Dni_Cliente,
               pd.Nom_Podologo + ' ' + ISNULL(pd.Ape_Pat_Podo,'') AS Podologo,
               a.Fe_Atencion,
               ISNULL((SELECT SUM(pg.Monto) FROM PAGO pg WHERE pg.Id_Boleta = b.Id_Boleta), 0) AS Pagado,
               (SELECT COUNT(*) FROM PAGO pg WHERE pg.Id_Boleta = b.Id_Boleta) AS N_Pagos
        FROM BOLETA b
        JOIN ATENCION a  ON a.Id_Atencion = b.Id_Atencion
        JOIN CITA c      ON c.Id_Cita = a.Id_Cita
        JOIN CLIENTE cl  ON cl.Id_Cliente = c.Id_Cliente
        JOIN PODOLOGO pd ON pd.Id_Podologo = c.Id_Podologo
        LEFT JOIN RECEPCIONISTA r ON r.Id_Recep = b.Id_Recep
        WHERE 1 = 1"""
    args: list = []
    if estado:
        sql += " AND b.Estado_Pago = ?"
        args.append(estado)
    if desde:
        sql += " AND b.Fe_Emision >= ?"
        args.append(a_fecha(desde))
    if hasta:
        sql += " AND b.Fe_Emision <= ?"
        args.append(a_fecha(hasta))
    sql += " ORDER BY b.Id_Boleta DESC"
    return consultar(sql, tuple(args))


@ruta("POST", "/api/boletas", ADMIN_RECEP)
def api_emitir_boleta(p: Peticion):
    id_atencion = entero(p.cuerpo.get("Id_Atencion"), 0)
    hace_falta(id_atencion, "Seleccione la atención a facturar.")

    # Regla R5 — no hay boleta sin cliente/atención válidos.
    atencion_facturable(id_atencion)

    tx = Tx()
    try:
        totales_atencion = totales(tx, id_atencion)
        hace_falta(totales_atencion["total"] > 0,
                   "La atención no tiene servicios ni medicamentos registrados. El podólogo debe cargarlos antes de facturar.")
        id_boleta = tx.insertar(
            """INSERT INTO BOLETA (Id_Atencion, Id_Recep, Fe_Emision, Importe, Estado_Pago)
               VALUES (?,?,?,?, 'Pendiente')""",
            (id_atencion, p.sesion["id_recep"], date.today(), Decimal(str(totales_atencion["total"]))),
        )
        tx.confirmar()
    finally:
        tx.cerrar()
    auditar(p.sesion, "INSERT", "BOLETA", id_boleta,
            "Emitió la boleta de la atención %d por S/ %.2f" % (id_atencion, totales_atencion["total"]), p.equipo)
    return uno("SELECT * FROM BOLETA WHERE Id_Boleta = ?", (id_boleta,))


@ruta("POST", "/api/boletas/(?P<id>\\d+)/pagos", ADMIN_RECEP)
def api_registrar_pago(p: Peticion):
    id_boleta = p.identificador()
    tipo = p.campo("Tipo_Pago", 30)
    monto_pago = monto(p.cuerpo.get("Monto"))
    hace_falta(tipo in TIPOS_PAGO, "Seleccione el tipo de pago.")
    hace_falta(monto_pago > 0, "El monto debe ser mayor que cero.")

    tx = Tx()
    try:
        # Regla R4 — una boleta pagada y cerrada no se modifica.
        boleta = verificar_boleta_abierta(tx, id_boleta)

        # Regla R2 — la suma de pagos no puede superar el importe.
        saldo = saldo_pendiente(tx, boleta)
        hace_falta(monto_pago <= saldo,
                   "Regla R2: el pago (S/ %.2f) supera el saldo pendiente (S/ %.2f)." % (monto_pago, saldo))

        id_pago = tx.insertar(
            "INSERT INTO PAGO (Id_Boleta, Tipo_Pago, Monto, Fe_Pago) VALUES (?,?,?,?)",
            (id_boleta, tipo, monto_pago, a_fecha(p.campo("Fe_Pago", 10), date.today())),
        )
        nuevo_saldo = saldo - monto_pago
        estado = estado_segun_saldo(nuevo_saldo)
        tx.ejecutar("UPDATE BOLETA SET Estado_Pago = ? WHERE Id_Boleta = ?", (estado, id_boleta))
        tx.confirmar()
    finally:
        tx.cerrar()

    auditar(p.sesion, "COBRO", "BOLETA", id_boleta,
            "Registró pago %s de S/ %.2f (saldo S/ %.2f)" % (tipo, monto_pago, nuevo_saldo), p.equipo)
    return {
        "ok": True,
        "Id_Pago": id_pago,
        "saldo": float(nuevo_saldo),
        "estado": estado,
    }


@ruta("DELETE", "/api/boletas/(?P<id>\\d+)", ADMIN)
def api_borrar_boleta(p: Peticion):
    id_boleta = p.identificador()
    # Regla R4 — verificada también por el trigger TR_BOLETA_NoEliminarPagada.
    verificar_boleta_anulable(id_boleta)
    ejecutar("DELETE FROM BOLETA WHERE Id_Boleta = ?", (id_boleta,))
    auditar(p.sesion, "DELETE", "BOLETA", id_boleta, "Anuló la boleta (sin pagos)", p.equipo)
    return {"ok": True}
