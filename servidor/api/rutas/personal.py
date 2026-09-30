#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Personal de la clínica: podólogos y recepcionistas (solo Administrador)."""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from datos import consultar, escalar, escalar_insert, ejecutar, uno
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN, TODOS
from nucleo.utilidades import entero, hace_falta


@ruta("GET", "/api/podologos", TODOS)
def api_podologos(p: Peticion):
    return consultar(
        """SELECT p.*, (SELECT COUNT(*) FROM CITA c WHERE c.Id_Podologo = p.Id_Podologo) AS Citas
           FROM PODOLOGO p ORDER BY p.Nom_Podologo"""
    )


@ruta("POST", "/api/podologos", ADMIN)
def api_guardar_podologo(p: Peticion):
    nombre = p.campo("Nom_Podologo", 100)
    hace_falta(nombre, "Indique el nombre del podólogo.")
    datos = (
        nombre,
        p.campo("Ape_Pat_Podo", 50),
        p.campo("Ape_Mat_Podo", 50),
        p.campo("Esp_Podo", 100),
        p.campo("Tel_Podo", 15),
        p.campo("Email_Podo", 100),
    )
    id_pod = entero(p.cuerpo.get("Id_Podologo"), 0)
    if id_pod:
        ejecutar(
            """UPDATE PODOLOGO SET Nom_Podologo=?, Ape_Pat_Podo=?, Ape_Mat_Podo=?,
               Esp_Podo=?, Tel_Podo=?, Email_Podo=? WHERE Id_Podologo=?""",
            datos + (id_pod,),
        )
        auditar(p.sesion, "UPDATE", "PODOLOGO", id_pod, "Actualizó al podólogo %s" % nombre, p.equipo)
    else:
        id_pod = escalar_insert(
            """INSERT INTO PODOLOGO (Nom_Podologo, Ape_Pat_Podo, Ape_Mat_Podo,
               Esp_Podo, Tel_Podo, Email_Podo) VALUES (?,?,?,?,?,?)""", datos
        )
        auditar(p.sesion, "INSERT", "PODOLOGO", id_pod, "Registró al podólogo %s" % nombre, p.equipo)
    return uno("SELECT * FROM PODOLOGO WHERE Id_Podologo = ?", (id_pod,))


@ruta("DELETE", "/api/podologos/(?P<id>\\d+)", ADMIN)
def api_borrar_podologo(p: Peticion):
    id_pod = p.identificador()
    if escalar("SELECT COUNT(*) FROM CITA WHERE Id_Podologo = ?", (id_pod,), 0):
        fallo("No se puede eliminar: el podólogo tiene citas registradas.")
    if escalar("SELECT COUNT(*) FROM USUARIO WHERE Id_Podologo = ?", (id_pod,), 0):
        fallo("No se puede eliminar: el podólogo tiene un usuario del sistema vinculado.")
    ejecutar("DELETE FROM PODOLOGO WHERE Id_Podologo = ?", (id_pod,))
    auditar(p.sesion, "DELETE", "PODOLOGO", id_pod, "Eliminó un podólogo", p.equipo)
    return {"ok": True}


@ruta("GET", "/api/recepcionistas", ADMIN)
def api_recepcionistas(p: Peticion):
    return consultar(
        """SELECT r.*, (SELECT COUNT(*) FROM CITA c WHERE c.Id_Recep = r.Id_Recep) AS Citas
           FROM RECEPCIONISTA r ORDER BY r.Apellidos_Recep"""
    )


@ruta("POST", "/api/recepcionistas", ADMIN)
def api_guardar_recepcionista(p: Peticion):
    nombres = p.campo("Noms_Recep", 100)
    hace_falta(nombres, "Indique los nombres del recepcionista.")
    datos = (nombres, p.campo("Apellidos_Recep", 100), p.campo("Tel_Recep", 15))
    id_rec = entero(p.cuerpo.get("Id_Recep"), 0)
    if id_rec:
        ejecutar(
            "UPDATE RECEPCIONISTA SET Noms_Recep=?, Apellidos_Recep=?, Tel_Recep=? WHERE Id_Recep=?",
            datos + (id_rec,),
        )
        auditar(p.sesion, "UPDATE", "RECEPCIONISTA", id_rec, "Actualizó a %s" % nombres, p.equipo)
    else:
        id_rec = escalar_insert(
            "INSERT INTO RECEPCIONISTA (Noms_Recep, Apellidos_Recep, Tel_Recep) VALUES (?,?,?)", datos
        )
        auditar(p.sesion, "INSERT", "RECEPCIONISTA", id_rec, "Registró a %s" % nombres, p.equipo)
    return uno("SELECT * FROM RECEPCIONISTA WHERE Id_Recep = ?", (id_rec,))


@ruta("DELETE", "/api/recepcionistas/(?P<id>\\d+)", ADMIN)
def api_borrar_recepcionista(p: Peticion):
    id_rec = p.identificador()
    if escalar("SELECT COUNT(*) FROM CITA WHERE Id_Recep = ?", (id_rec,), 0):
        fallo("No se puede eliminar: el recepcionista tiene citas registradas.")
    if escalar("SELECT COUNT(*) FROM USUARIO WHERE Id_Recep = ?", (id_rec,), 0):
        fallo("No se puede eliminar: el recepcionista tiene un usuario del sistema vinculado.")
    ejecutar("DELETE FROM RECEPCIONISTA WHERE Id_Recep = ?", (id_rec,))
    auditar(p.sesion, "DELETE", "RECEPCIONISTA", id_rec, "Eliminó un recepcionista", p.equipo)
    return {"ok": True}
