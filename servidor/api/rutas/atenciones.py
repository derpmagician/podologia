#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atención clínica: diagnóstico, tratamiento y consumos del podólogo.

El importe nunca se digita a mano: se calcula sumando los detalles de
servicios y medicamentos. Una atención ya facturada queda bloqueada (R4).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from api.enrutador import Peticion, ruta
from datos import Tx, consultar, escalar, ejecutar, uno
from dominio.atenciones import abierta, solo_su_podologo, totales
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN_POD, TODOS
from nucleo.utilidades import a_fecha, entero, hace_falta


@ruta("GET", "/api/atenciones", TODOS)
def api_atenciones(p: Peticion):
    sin_boleta = p.filtro("sin_boleta", 2) == "1"
    desde = p.filtro("desde", 10)
    hasta = p.filtro("hasta", 10)
    id_pod = entero(p.filtro("podologo", 10), 0)
    if p.rol == "Podologo":
        id_pod = p.sesion["id_podologo"]

    sql = """
        SELECT a.Id_Atencion, a.Id_Cita, a.Diag, a.Trat, a.Obs, a.Fe_Atencion,
               c.Fe_Cita, c.Hora_Cita, c.Estado AS Estado_Cita, c.Motivo,
               c.Id_Cliente, c.Id_Podologo,
               cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') + ' ' + ISNULL(cl.Ape_Mat_Cliente,'') AS Cliente,
               cl.Dni_Cliente, cl.Tel_Cliente,
               pd.Nom_Podologo + ' ' + ISNULL(pd.Ape_Pat_Podo,'') + ' ' + ISNULL(pd.Ape_Mat_Podo,'') AS Podologo,
               b.Id_Boleta, b.Importe, b.Estado_Pago,
               (SELECT ISNULL(SUM(d.Subt_Aten),0) FROM DETALLE_ATENCION d WHERE d.Id_Atencion = a.Id_Atencion) AS Total_Servicios,
               (SELECT ISNULL(SUM(d.Subt_Med),0)  FROM DETALLE_MEDICAMENTO d WHERE d.Id_Atencion = a.Id_Atencion) AS Total_Medicamentos
        FROM ATENCION a
        JOIN CITA c      ON c.Id_Cita = a.Id_Cita
        JOIN CLIENTE cl  ON cl.Id_Cliente = c.Id_Cliente
        JOIN PODOLOGO pd ON pd.Id_Podologo = c.Id_Podologo
        LEFT JOIN BOLETA b ON b.Id_Atencion = a.Id_Atencion
        WHERE 1 = 1"""
    args: list = []
    if sin_boleta:
        sql += " AND b.Id_Boleta IS NULL"
    if desde:
        sql += " AND a.Fe_Atencion >= ?"
        args.append(a_fecha(desde))
    if hasta:
        sql += " AND a.Fe_Atencion <= ?"
        args.append(a_fecha(hasta))
    if id_pod:
        sql += " AND c.Id_Podologo = ?"
        args.append(id_pod)
    sql += " ORDER BY a.Fe_Atencion DESC, a.Id_Atencion DESC"
    return consultar(sql, tuple(args))


@ruta("GET", "/api/atenciones/(?P<id>\\d+)", TODOS)
def api_atencion_detalle(p: Peticion):
    id_atencion = p.identificador()
    cabecera = uno(
        """SELECT a.*, c.Fe_Cita, c.Hora_Cita, c.Motivo, c.Id_Cliente, c.Id_Podologo,
                  cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') + ' ' + ISNULL(cl.Ape_Mat_Cliente,'') AS Cliente,
                  cl.Dni_Cliente, cl.Tel_Cliente, cl.Email_Cliente,
                  pd.Nom_Podologo + ' ' + ISNULL(pd.Ape_Pat_Podo,'') + ' ' + ISNULL(pd.Ape_Mat_Podo,'') AS Podologo,
                  b.Id_Boleta, b.Importe, b.Estado_Pago, b.Fe_Emision
           FROM ATENCION a
           JOIN CITA c      ON c.Id_Cita = a.Id_Cita
           JOIN CLIENTE cl  ON cl.Id_Cliente = c.Id_Cliente
           JOIN PODOLOGO pd ON pd.Id_Podologo = c.Id_Podologo
           LEFT JOIN BOLETA b ON b.Id_Atencion = a.Id_Atencion
           WHERE a.Id_Atencion = ?""",
        (id_atencion,),
    )
    if not cabecera:
        fallo("La atención no existe.", 404)
    if p.rol == "Podologo" and cabecera["Id_Podologo"] != p.sesion["id_podologo"]:
        fallo("Solo puede ver las atenciones de sus propias citas.", 403)

    servicios = consultar(
        """SELECT d.Id_Detalle_Aten, d.Id_Servicio, d.Cant_Aten, d.Subt_Aten,
                  s.Nom_serv, s.Precio_Servicio
           FROM DETALLE_ATENCION d JOIN SERVICIO s ON s.Id_Servicio = d.Id_Servicio
           WHERE d.Id_Atencion = ? ORDER BY d.Id_Detalle_Aten""", (id_atencion,)
    )
    medicamentos = consultar(
        """SELECT d.Id_Detalle_Med, d.Id_Medicamento, d.Cant_Med, d.Subt_Med,
                  m.Nom_Med, m.Precio_Med
           FROM DETALLE_MEDICAMENTO d JOIN MEDICAMENTO m ON m.Id_Medicamento = d.Id_Medicamento
           WHERE d.Id_Atencion = ? ORDER BY d.Id_Detalle_Med""", (id_atencion,)
    )
    pagos = []
    if cabecera["Id_Boleta"]:
        pagos = consultar(
            "SELECT * FROM PAGO WHERE Id_Boleta = ? ORDER BY Id_Pago", (cabecera["Id_Boleta"],)
        )
    suma_servicios = sum(float(s["Subt_Aten"]) for s in servicios)
    suma_medicamentos = sum(float(m["Subt_Med"]) for m in medicamentos)
    return {
        "cabecera": cabecera,
        "servicios": servicios,
        "medicamentos": medicamentos,
        "pagos": pagos,
        "totales": {
            "servicios": suma_servicios,
            "medicamentos": suma_medicamentos,
            "total": suma_servicios + suma_medicamentos,
        },
    }


@ruta("POST", "/api/atenciones", ADMIN_POD)
def api_guardar_atencion(p: Peticion):
    id_atencion = entero(p.cuerpo.get("Id_Atencion"), 0)
    id_cita = entero(p.cuerpo.get("Id_Cita"), 0)
    diag = p.campo("Diag", 2000)
    trat = p.campo("Trat", 2000)
    obs = p.campo("Obs", 2000)

    if id_atencion:
        actual = uno("SELECT * FROM ATENCION WHERE Id_Atencion = ?", (id_atencion,))
        hace_falta(actual, "La atención no existe.", 404)
        if escalar("SELECT COUNT(*) FROM BOLETA WHERE Id_Atencion = ?", (id_atencion,), 0):
            fallo("Regla R4: la atención ya tiene una boleta emitida; no se puede modificar.")
        ejecutar("UPDATE ATENCION SET Diag=?, Trat=?, Obs=? WHERE Id_Atencion=?",
                 (diag, trat, obs, id_atencion))
        auditar(p.sesion, "UPDATE", "ATENCION", id_atencion, "Actualizó la atención clínica", p.equipo)
        return uno("SELECT * FROM ATENCION WHERE Id_Atencion = ?", (id_atencion,))

    hace_falta(id_cita, "Seleccione la cita a atender.")
    cita = uno("SELECT * FROM CITA WHERE Id_Cita = ?", (id_cita,))
    hace_falta(cita, "La cita no existe.", 404)
    solo_su_podologo(cita, p, "Solo puede registrar atenciones de sus propias citas.")
    if cita["Estado"] == "Cancelada":
        fallo("La cita está cancelada.")
    hace_falta(not escalar("SELECT COUNT(*) FROM ATENCION WHERE Id_Cita = ?", (id_cita,), 0),
               "Esa cita ya tiene una atención registrada.")

    tx = Tx()
    try:
        id_atencion = tx.insertar(
            "INSERT INTO ATENCION (Id_Cita, Diag, Trat, Obs, Fe_Atencion) VALUES (?,?,?,?,?)",
            (id_cita, diag, trat, obs, date.today()),
        )
        tx.ejecutar("UPDATE CITA SET Estado = 'Atendida' WHERE Id_Cita = ?", (id_cita,))
        tx.confirmar()
    finally:
        tx.cerrar()
    auditar(p.sesion, "INSERT", "ATENCION", id_atencion, "Registró la atención de la cita %d" % id_cita, p.equipo)
    return uno("SELECT * FROM ATENCION WHERE Id_Atencion = ?", (id_atencion,))


@ruta("POST", "/api/atenciones/(?P<id>\\d+)/servicios", ADMIN_POD)
def api_agregar_servicio(p: Peticion):
    id_atencion = p.identificador()
    fila = abierta(id_atencion)
    solo_su_podologo(fila, p, "Solo puede agregar consumos a sus propias atenciones.")

    id_servicio = entero(p.cuerpo.get("Id_Servicio"), 0)
    cantidad = entero(p.cuerpo.get("Cant_Aten"), 1)
    hace_falta(id_servicio, "Seleccione el servicio.")
    hace_falta(cantidad > 0, "La cantidad debe ser mayor que cero.")
    servicio = uno("SELECT * FROM SERVICIO WHERE Id_Servicio = ?", (id_servicio,))
    hace_falta(servicio, "El servicio no existe.", 404)

    precio = Decimal(str(servicio["Precio_Servicio"]))
    tx = Tx()
    try:
        id_detalle = tx.insertar(
            """INSERT INTO DETALLE_ATENCION (Id_Atencion, Id_Servicio, Cant_Aten, Subt_Aten)
               VALUES (?,?,?,?)""",
            (id_atencion, id_servicio, cantidad, precio * cantidad),
        )
        totales_atencion = totales(tx, id_atencion)
        tx.confirmar()
    finally:
        tx.cerrar()
    auditar(p.sesion, "INSERT", "DETALLE_ATENCION", id_detalle,
            "Agregó %dx %s a la atención %d" % (cantidad, servicio["Nom_serv"], id_atencion), p.equipo)
    return {"ok": True, "Id_Detalle_Aten": id_detalle, "totales": totales_atencion}


@ruta("DELETE", "/api/atenciones/(?P<id>\\d+)/servicios/(?P<idd>\\d+)", ADMIN_POD)
def api_quitar_servicio(p: Peticion):
    id_atencion = p.identificador()
    fila = abierta(id_atencion)
    solo_su_podologo(fila, p, "Solo puede quitar consumos de sus propias atenciones.")
    ejecutar("DELETE FROM DETALLE_ATENCION WHERE Id_Detalle_Aten = ? AND Id_Atencion = ?",
             (entero(p.partes.get("idd"), 0), id_atencion))
    auditar(p.sesion, "DELETE", "DETALLE_ATENCION", p.partes.get("idd"),
            "Quitó un servicio de la atención %d" % id_atencion, p.equipo)
    return {"ok": True}


@ruta("POST", "/api/atenciones/(?P<id>\\d+)/medicamentos", ADMIN_POD)
def api_agregar_medicamento(p: Peticion):
    id_atencion = p.identificador()
    fila = abierta(id_atencion)
    solo_su_podologo(fila, p, "Solo puede agregar consumos a sus propias atenciones.")

    id_medicamento = entero(p.cuerpo.get("Id_Medicamento"), 0)
    cantidad = entero(p.cuerpo.get("Cant_Med"), 1)
    hace_falta(id_medicamento, "Seleccione el medicamento.")
    hace_falta(cantidad > 0, "La cantidad debe ser mayor que cero.")

    tx = Tx()
    try:
        med = tx.uno(
            "SELECT * FROM MEDICAMENTO WITH (UPDLOCK) WHERE Id_Medicamento = ?", (id_medicamento,)
        )
        hace_falta(med, "El medicamento no existe.", 404)
        hace_falta(int(med["Stock_Med"]) >= cantidad,
                   "Stock insuficiente de %s: quedan %d unidad(es)." % (med["Nom_Med"], med["Stock_Med"]))

        precio = Decimal(str(med["Precio_Med"]))
        id_detalle = tx.insertar(
            """INSERT INTO DETALLE_MEDICAMENTO (Id_Atencion, Id_Medicamento, Cant_Med, Subt_Med)
               VALUES (?,?,?,?)""",
            (id_atencion, id_medicamento, cantidad, precio * cantidad),
        )
        tx.ejecutar("UPDATE MEDICAMENTO SET Stock_Med = Stock_Med - ? WHERE Id_Medicamento = ?",
                    (cantidad, id_medicamento))
        totales_atencion = totales(tx, id_atencion)
        tx.confirmar()
    finally:
        tx.cerrar()
    auditar(p.sesion, "UPDATE", "MEDICAMENTO", id_medicamento,
            "Descontó %d de %s por la atención %d" % (cantidad, med["Nom_Med"], id_atencion), p.equipo)
    return {"ok": True, "Id_Detalle_Med": id_detalle, "totales": totales_atencion}


@ruta("DELETE", "/api/atenciones/(?P<id>\\d+)/medicamentos/(?P<idd>\\d+)", ADMIN_POD)
def api_quitar_medicamento(p: Peticion):
    id_atencion = p.identificador()
    fila = abierta(id_atencion)
    solo_su_podologo(fila, p, "Solo puede quitar consumos de sus propias atenciones.")

    id_detalle = entero(p.partes.get("idd"), 0)
    detalle = uno("SELECT * FROM DETALLE_MEDICAMENTO WHERE Id_Detalle_Med = ? AND Id_Atencion = ?",
                  (id_detalle, id_atencion))
    hace_falta(detalle, "El detalle no existe.", 404)

    tx = Tx()
    try:
        tx.ejecutar("UPDATE MEDICAMENTO SET Stock_Med = Stock_Med + ? WHERE Id_Medicamento = ?",
                    (detalle["Cant_Med"], detalle["Id_Medicamento"]))
        tx.ejecutar("DELETE FROM DETALLE_MEDICAMENTO WHERE Id_Detalle_Med = ?", (id_detalle,))
        totales_atencion = totales(tx, id_atencion)
        tx.confirmar()
    finally:
        tx.cerrar()
    auditar(p.sesion, "DELETE", "DETALLE_MEDICAMENTO", id_detalle,
            "Devolvió stock y quitó un medicamento de la atención %d" % id_atencion, p.equipo)
    return {"ok": True, "totales": totales_atencion}
