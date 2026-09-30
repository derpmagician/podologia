#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clientes: registro, edición y baja (regla R3: Administrador y Recepcionista)."""

from __future__ import annotations

from datetime import date

from api.enrutador import Peticion, ruta
from datos import consultar, escalar, escalar_insert, ejecutar, uno
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN, ADMIN_RECEP, TODOS
from nucleo.utilidades import a_fecha, entero, hace_falta


@ruta("GET", "/api/clientes", TODOS)
def api_clientes(p: Peticion):
    busqueda = p.filtro("q", 60)
    sql = """SELECT c.*, (SELECT COUNT(*) FROM CITA ci WHERE ci.Id_Cliente = c.Id_Cliente) AS Citas,
                    (SELECT MAX(a.Fe_Atencion) FROM CITA ci
                       JOIN ATENCION a ON a.Id_Cita = ci.Id_Cita
                      WHERE ci.Id_Cliente = c.Id_Cliente) AS Ultima_Atencion
             FROM CLIENTE c"""
    args: list = []
    if busqueda:
        sql += """ WHERE c.Noms_Cliente LIKE ? OR c.Ape_Pat_Cliente LIKE ?
                     OR c.Ape_Mat_Cliente LIKE ? OR c.Dni_Cliente LIKE ?"""
        args = ["%" + busqueda + "%"] * 4
    sql += " ORDER BY c.Ape_Pat_Cliente, c.Ape_Mat_Cliente, c.Noms_Cliente"
    return consultar(sql, tuple(args))


@ruta("POST", "/api/clientes", ADMIN_RECEP)
def api_guardar_cliente(p: Peticion):
    nombre = p.campo("Noms_Cliente", 100)
    hace_falta(nombre, "Indique los nombres del cliente.")
    dni = p.campo("Dni_Cliente", 8)
    if dni and not dni.isdigit():
        fallo("El DNI debe tener solo números.")
    if dni and len(dni) != 8:
        fallo("El DNI debe tener 8 dígitos.")

    datos = (
        nombre,
        p.campo("Ape_Pat_Cliente", 50),
        p.campo("Ape_Mat_Cliente", 50),
        dni or None,
        p.campo("Tel_Cliente", 15),
        p.campo("Email_Cliente", 100),
        a_fecha(p.campo("Fecha_Registro", 10), date.today()),
    )
    id_cliente = entero(p.cuerpo.get("Id_Cliente"), 0)

    if id_cliente:
        ejecutar(
            """UPDATE CLIENTE SET Noms_Cliente=?, Ape_Pat_Cliente=?, Ape_Mat_Cliente=?,
               Dni_Cliente=?, Tel_Cliente=?, Email_Cliente=?, Fecha_Registro=? WHERE Id_Cliente=?""",
            datos + (id_cliente,),
        )
        auditar(p.sesion, "UPDATE", "CLIENTE", id_cliente, "Actualizó al cliente %s" % nombre, p.equipo)
    else:
        try:
            id_cliente = escalar_insert(
                """INSERT INTO CLIENTE (Noms_Cliente, Ape_Pat_Cliente, Ape_Mat_Cliente,
                   Dni_Cliente, Tel_Cliente, Email_Cliente, Fecha_Registro)
                   VALUES (?,?,?,?,?,?,?)""",
                datos,
            )
        except Exception as error:
            if "UQ" in str(error) or "duplicate" in str(error).lower() or "UNIQUE" in str(error).upper():
                fallo("Ya existe un cliente registrado con ese DNI.")
            raise
        auditar(p.sesion, "INSERT", "CLIENTE", id_cliente, "Registró al cliente %s" % nombre, p.equipo)

    return uno("SELECT * FROM CLIENTE WHERE Id_Cliente = ?", (id_cliente,))


@ruta("DELETE", "/api/clientes/(?P<id>\\d+)", ADMIN)
def api_borrar_cliente(p: Peticion):
    id_cliente = p.identificador()
    citas = escalar("SELECT COUNT(*) FROM CITA WHERE Id_Cliente = ?", (id_cliente,), 0)
    if citas:
        fallo("No se puede eliminar: el cliente tiene %d cita(s) registrada(s)." % citas)
    atenciones = escalar(
        """SELECT COUNT(*) FROM ATENCION a JOIN CITA c ON c.Id_Cita = a.Id_Cita
           WHERE c.Id_Cliente = ?""", (id_cliente,), 0)
    if atenciones:
        fallo("No se puede eliminar: el cliente tiene historial clínico (%d atención/es)." % atenciones)
    ejecutar("DELETE FROM CLIENTE WHERE Id_Cliente = ?", (id_cliente,))
    auditar(p.sesion, "DELETE", "CLIENTE", id_cliente, "Eliminó un cliente", p.equipo)
    return {"ok": True}
