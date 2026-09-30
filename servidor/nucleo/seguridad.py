#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seguridad: contraseñas y sesiones.

Las contraseñas nunca se guardan en texto plano: PBKDF2-SHA256 con sal
aleatoria por usuario. Las sesiones viven en memoria y expiran solas.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time

from config import DURACION_SESION, ITERACIONES_PBKDF2


def cifrar_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, ITERACIONES_PBKDF2)
    return "pbkdf2$%d$%s$%s" % (ITERACIONES_PBKDF2, sal.hex(), derivada.hex())


def clave_correcta(clave: str, guardado: str) -> bool:
    try:
        algoritmo, iteraciones, sal_hex, hash_hex = (guardado or "").split("$")
        if algoritmo != "pbkdf2":
            return False
        derivada = hashlib.pbkdf2_hmac(
            "sha256", clave.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones)
        )
        return hmac.compare_digest(derivada.hex(), hash_hex)
    except Exception:
        return False


SESIONES: dict[str, dict] = {}
CANDADO = threading.Lock()


def abrir_sesion(fila: dict) -> dict:
    sesion = {
        "token": secrets.token_urlsafe(32),
        "id": fila["Id_Usuario"],
        "usuario": fila["Usuario"],
        "rol": fila["Rol"],
        "nombres": fila["Nombres"],
        "id_podologo": fila["Id_Podologo"],
        "id_recep": fila["Id_Recep"],
        "expira": time.time() + DURACION_SESION,
    }
    with CANDADO:
        SESIONES[sesion["token"]] = sesion
    return sesion


def buscar_sesion(token: str | None) -> dict | None:
    if not token:
        return None
    with CANDADO:
        sesion = SESIONES.get(token)
        if not sesion:
            return None
        if sesion["expira"] < time.time():
            SESIONES.pop(token, None)
            return None
    return sesion


def cerrar_sesion(token: str | None) -> None:
    if token:
        with CANDADO:
            SESIONES.pop(token, None)
