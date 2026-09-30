#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medicamentos: catálogo y control de stock.

El stock se descuenta al agregar un medicamento a una atención y se devuelve
al quitarlo (ver api/rutas/atenciones.py).
"""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from datos import consultar, escalar, escalar_insert, ejecutar, uno
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN, TODOS
from nucleo.utilidades import a_fecha, entero, hace_falta, monto


@ruta("GET", "/api/medicamentos", TODOS)
def api_medicamentos(p: Peticion):
    return consultar(
        """SELECT m.*,
                  DATEDIFF(DAY, GETDATE(), m.Fe_Venc_Med) AS Dias_Vencer,
                  (SELECT ISNULL(SUM(d.Cant_Med),0) FROM DETALLE_MEDICAMENTO d
                    WHERE d.Id_Medicamento = m.Id_Medicamento) AS Usos
           FROM MEDICAMENTO m ORDER BY m.Nom_Med"""
    )


@ruta("POST", "/api/medicamentos", ADMIN)
def api_guardar_medicamento(p: Peticion):
    nombre = p.campo("Nom_Med", 100)
    hace_falta(nombre, "Indique el nombre del medicamento.")
    stock = entero(p.cuerpo.get("Stock_Med"), 0)
    hace_falta(stock >= 0, "El stock no puede ser negativo.")
    datos = (nombre, stock, monto(p.cuerpo.get("Precio_Med")), a_fecha(p.campo("Fe_Venc_Med", 10), None))
    id_med = entero(p.cuerpo.get("Id_Medicamento"), 0)
    if id_med:
        ejecutar(
            """UPDATE MEDICAMENTO SET Nom_Med=?, Stock_Med=?, Precio_Med=?, Fe_Venc_Med=?
               WHERE Id_Medicamento=?""",
            datos + (id_med,),
        )
        auditar(p.sesion, "UPDATE", "MEDICAMENTO", id_med, "Actualizó %s (stock %d)" % (nombre, stock), p.equipo)
    else:
        id_med = escalar_insert(
            """INSERT INTO MEDICAMENTO (Nom_Med, Stock_Med, Precio_Med, Fe_Venc_Med)
               VALUES (?,?,?,?)""", datos
        )
        auditar(p.sesion, "INSERT", "MEDICAMENTO", id_med, "Registró %s (stock %d)" % (nombre, stock), p.equipo)
    return uno("SELECT * FROM MEDICAMENTO WHERE Id_Medicamento = ?", (id_med,))


@ruta("POST", "/api/medicamentos/(?P<id>\\d+)/stock", ADMIN)
def api_movimiento_stock(p: Peticion):
    id_med = p.identificador()
    cantidad = entero(p.cuerpo.get("Cantidad"), 0)
    hace_falta(cantidad != 0, "Indique la cantidad a ingresar o retirar.")
    fila = uno("SELECT * FROM MEDICAMENTO WHERE Id_Medicamento = ?", (id_med,))
    hace_falta(fila, "El medicamento no existe.", 404)
    nuevo = int(fila["Stock_Med"]) + cantidad
    hace_falta(nuevo >= 0, "El stock quedaría en negativo (%d)." % nuevo)
    ejecutar("UPDATE MEDICAMENTO SET Stock_Med = ? WHERE Id_Medicamento = ?", (nuevo, id_med))
    auditar(p.sesion, "UPDATE", "MEDICAMENTO", id_med,
            "Movimiento de stock %+d en %s (queda %d)" % (cantidad, fila["Nom_Med"], nuevo), p.equipo)
    return uno("SELECT * FROM MEDICAMENTO WHERE Id_Medicamento = ?", (id_med,))


@ruta("DELETE", "/api/medicamentos/(?P<id>\\d+)", ADMIN)
def api_borrar_medicamento(p: Peticion):
    id_med = p.identificador()
    if escalar("SELECT COUNT(*) FROM DETALLE_MEDICAMENTO WHERE Id_Medicamento = ?", (id_med,), 0):
        fallo("No se puede eliminar: el medicamento ya fue usado en atenciones.")
    ejecutar("DELETE FROM MEDICAMENTO WHERE Id_Medicamento = ?", (id_med,))
    auditar(p.sesion, "DELETE", "MEDICAMENTO", id_med, "Eliminó un medicamento", p.equipo)
    return {"ok": True}
