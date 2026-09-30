#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sesión y login.

Las credenciales se validan contra la tabla USUARIO (PBKDF2-SHA256) y la
sesión viaja en una cookie HttpOnly. Cada intento queda en la auditoría.
"""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from config import DURACION_SESION
from datos import ejecutar, uno
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import datos_usuario
from nucleo.seguridad import abrir_sesion, cerrar_sesion, clave_correcta
from nucleo.utilidades import hace_falta


@ruta("POST", "/api/login")
def api_login(p: Peticion):
    usuario = p.campo("usuario", 50).lower()
    clave = str(p.cuerpo.get("clave") or "")
    hace_falta(usuario and clave, "Ingrese su usuario y contraseña.")

    fila = uno("SELECT * FROM USUARIO WHERE Usuario = ?", (usuario,))
    if not fila or not fila["Activo"] or not clave_correcta(clave, fila["Clave_Hash"]):
        auditar(None, "LOGIN_FALLIDO", "USUARIO", usuario,
                "Intento fallido con el usuario '%s'" % usuario, p.equipo)
        fallo("Usuario o contraseña incorrectos.", 401)

    sesion = abrir_sesion(fila)
    ejecutar("UPDATE USUARIO SET Ultimo_Acceso = GETDATE() WHERE Id_Usuario = ?", (fila["Id_Usuario"],))
    auditar(sesion, "LOGIN", "USUARIO", fila["Id_Usuario"], "Ingreso correcto al sistema", p.equipo)

    p.cabeceras.append(
        ("Set-Cookie", "sesion=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (sesion["token"], DURACION_SESION))
    )
    return datos_usuario(sesion)


@ruta("POST", "/api/logout")
def api_logout(p: Peticion):
    auditar(p.sesion, "LOGOUT", "USUARIO", p.id_usuario, "Salió del sistema", p.equipo)
    cerrar_sesion(p.sesion["token"] if p.sesion else None)
    p.cabeceras.append(("Set-Cookie", "sesion=; Path=/; HttpOnly; Max-Age=0"))
    return {"ok": True}


@ruta("GET", "/api/sesion")
def api_sesion(p: Peticion):
    if not p.sesion:
        fallo("No hay una sesión activa.", 401)
    return datos_usuario(p.sesion)
