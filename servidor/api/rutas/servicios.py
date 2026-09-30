#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo de servicios y sus precios (solo Administrador)."""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from datos import consultar, escalar, escalar_insert, ejecutar, uno
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN, TODOS
from nucleo.utilidades import entero, hace_falta, monto


@ruta("GET", "/api/servicios", TODOS)
def api_servicios(p: Peticion):
    return consultar(
        """SELECT s.*, (SELECT COUNT(*) FROM DETALLE_ATENCION d WHERE d.Id_Servicio = s.Id_Servicio) AS Usos
           FROM SERVICIO s ORDER BY s.Nom_serv"""
    )


@ruta("POST", "/api/servicios", ADMIN)
def api_guardar_servicio(p: Peticion):
    nombre = p.campo("Nom_serv", 100)
    hace_falta(nombre, "Indique el nombre del servicio.")
    datos = (nombre, p.campo("Descripcion", 200), monto(p.cuerpo.get("Precio_Servicio")))
    id_serv = entero(p.cuerpo.get("Id_Servicio"), 0)
    if id_serv:
        ejecutar(
            "UPDATE SERVICIO SET Nom_serv=?, Descripcion=?, Precio_Servicio=? WHERE Id_Servicio=?",
            datos + (id_serv,),
        )
        auditar(p.sesion, "UPDATE", "SERVICIO", id_serv, "Actualizó el servicio %s" % nombre, p.equipo)
    else:
        id_serv = escalar_insert(
            "INSERT INTO SERVICIO (Nom_serv, Descripcion, Precio_Servicio) VALUES (?,?,?)", datos
        )
        auditar(p.sesion, "INSERT", "SERVICIO", id_serv, "Registró el servicio %s" % nombre, p.equipo)
    return uno("SELECT * FROM SERVICIO WHERE Id_Servicio = ?", (id_serv,))


@ruta("DELETE", "/api/servicios/(?P<id>\\d+)", ADMIN)
def api_borrar_servicio(p: Peticion):
    id_serv = p.identificador()
    if escalar("SELECT COUNT(*) FROM DETALLE_ATENCION WHERE Id_Servicio = ?", (id_serv,), 0):
        fallo("No se puede eliminar: el servicio ya fue usado en atenciones.")
    ejecutar("DELETE FROM SERVICIO WHERE Id_Servicio = ?", (id_serv,))
    auditar(p.sesion, "DELETE", "SERVICIO", id_serv, "Eliminó un servicio", p.equipo)
    return {"ok": True}
