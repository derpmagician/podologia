#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usuarios y roles (solo Administrador — regla R3).

Cada usuario con rol Podologo o Recepcionista se vincula a la fila de personal
que le corresponde, para que el sistema sepa de quién son las citas.
"""

from __future__ import annotations

import re

from api.enrutador import Peticion, ruta
from datos import consultar, escalar, escalar_insert, ejecutar, uno
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN, TODOS
from nucleo.seguridad import cifrar_clave
from nucleo.utilidades import entero, hace_falta


@ruta("GET", "/api/usuarios", ADMIN)
def api_usuarios(p: Peticion):
    return consultar(
        """SELECT u.Id_Usuario, u.Usuario, u.Rol, u.Nombres, u.Activo, u.Fe_Alta, u.Ultimo_Acceso,
                  u.Id_Podologo, u.Id_Recep,
                  ISNULL(p.Nom_Podologo + ' ' + ISNULL(p.Ape_Pat_Podo,''), '') AS Empleado_Podologo,
                  ISNULL(r.Noms_Recep + ' ' + ISNULL(r.Apellidos_Recep,''), '')     AS Empleado_Recep
           FROM USUARIO u
           LEFT JOIN PODOLOGO p      ON p.Id_Podologo = u.Id_Podologo
           LEFT JOIN RECEPCIONISTA r ON r.Id_Recep    = u.Id_Recep
           ORDER BY u.Rol, u.Usuario"""
    )


@ruta("POST", "/api/usuarios", ADMIN)
def api_guardar_usuario(p: Peticion):
    id_usuario = entero(p.cuerpo.get("Id_Usuario"), 0)
    usuario = p.campo("Usuario", 50).lower()
    rol = p.campo("Rol", 20)
    nombres = p.campo("Nombres", 120)
    id_pod = entero(p.cuerpo.get("Id_Podologo"), 0) or None
    id_rec = entero(p.cuerpo.get("Id_Recep"), 0) or None
    activo = 1 if p.cuerpo.get("Activo", True) in (True, 1, "1", "true", "on") else 0

    hace_falta(usuario, "Indique el nombre de usuario.")
    hace_falta(re.fullmatch(r"[a-z0-9._-]{3,50}", usuario), "El usuario debe tener 3 a 50 caracteres (letras, números, punto, guion o guion bajo).")
    hace_falta(rol in TODOS, "Seleccione un rol válido.")
    hace_falta(nombres, "Indique el nombre completo de la persona.")

    if rol == "Podologo":
        hace_falta(id_pod, "Seleccione a qué podólogo corresponde este usuario.")
        hace_falta(uno("SELECT Id_Podologo FROM PODOLOGO WHERE Id_Podologo = ?", (id_pod,)),
                   "El podólogo seleccionado no existe.", 404)
        id_rec = None
    elif rol == "Recepcionista":
        hace_falta(id_rec, "Seleccione a qué recepcionista corresponde este usuario.")
        hace_falta(uno("SELECT Id_Recep FROM RECEPCIONISTA WHERE Id_Recep = ?", (id_rec,)),
                   "El recepcionista seleccionado no existe.", 404)
        id_pod = None
    else:
        id_pod = id_rec = None

    repetido = uno(
        "SELECT Id_Usuario FROM USUARIO WHERE Usuario = ? AND Id_Usuario <> ?", (usuario, id_usuario)
    )
    hace_falta(not repetido, "Ese nombre de usuario ya existe.")

    if id_usuario:
        ejecutar(
            """UPDATE USUARIO SET Usuario=?, Rol=?, Nombres=?, Id_Podologo=?, Id_Recep=?, Activo=?
               WHERE Id_Usuario=?""",
            (usuario, rol, nombres, id_pod, id_rec, activo, id_usuario),
        )
        auditar(p.sesion, "UPDATE", "USUARIO", id_usuario,
                "Actualizó el usuario '%s' (rol %s)" % (usuario, rol), p.equipo)
    else:
        clave = str(p.cuerpo.get("Clave") or "")
        hace_falta(len(clave) >= 6, "La contraseña debe tener al menos 6 caracteres.")
        id_usuario = escalar_insert(
            """INSERT INTO USUARIO (Usuario, Clave_Hash, Rol, Id_Podologo, Id_Recep, Nombres, Activo)
               VALUES (?,?,?,?,?,?,?)""",
            (usuario, cifrar_clave(clave), rol, id_pod, id_rec, nombres, activo),
        )
        auditar(p.sesion, "INSERT", "USUARIO", id_usuario,
                "Creó el usuario '%s' con rol %s" % (usuario, rol), p.equipo)

    return uno(
        "SELECT Id_Usuario, Usuario, Rol, Nombres, Activo, Fe_Alta, Ultimo_Acceso FROM USUARIO WHERE Id_Usuario = ?",
        (id_usuario,),
    )


@ruta("POST", "/api/usuarios/(?P<id>\\d+)/clave", ADMIN)
def api_reset_clave(p: Peticion):
    id_usuario = p.identificador()
    clave = str(p.cuerpo.get("Clave") or "")
    hace_falta(len(clave) >= 6, "La nueva contraseña debe tener al menos 6 caracteres.")
    hace_falta(uno("SELECT Id_Usuario FROM USUARIO WHERE Id_Usuario = ?", (id_usuario,)),
               "El usuario no existe.", 404)
    ejecutar("UPDATE USUARIO SET Clave_Hash = ? WHERE Id_Usuario = ?", (cifrar_clave(clave), id_usuario))
    auditar(p.sesion, "UPDATE", "USUARIO", id_usuario, "Cambió la contraseña de un usuario", p.equipo)
    return {"ok": True}


@ruta("DELETE", "/api/usuarios/(?P<id>\\d+)", ADMIN)
def api_borrar_usuario(p: Peticion):
    id_usuario = p.identificador()
    hace_falta(id_usuario != p.id_usuario, "No puede eliminar su propio usuario.")
    administradores = escalar("SELECT COUNT(*) FROM USUARIO WHERE Rol='Administrador' AND Activo=1", (), 0)
    objetivo = uno("SELECT * FROM USUARIO WHERE Id_Usuario = ?", (id_usuario,))
    hace_falta(objetivo, "El usuario no existe.", 404)
    if objetivo["Rol"] == "Administrador" and administradores <= 1:
        fallo("Debe quedar al menos un administrador activo.")
    ejecutar("UPDATE USUARIO SET Activo = 0 WHERE Id_Usuario = ?", (id_usuario,))
    auditar(p.sesion, "DELETE", "USUARIO", id_usuario,
            "Desactivó el usuario '%s'" % objetivo["Usuario"], p.equipo)
    return {"ok": True}
