#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roles, permisos y módulos de la interfaz (regla R3).

Cada módulo declara qué roles pueden verlo. El servidor valida contra esta
lista en cada ruta; el cliente la usa solo para pintar las pestañas.
"""

from __future__ import annotations

TODOS = ("Administrador", "Recepcionista", "Podologo")
ADMIN = ("Administrador",)
ADMIN_RECEP = ("Administrador", "Recepcionista")
ADMIN_POD = ("Administrador", "Podologo")

# Módulos de la interfaz y qué roles pueden verlos (regla R3).
MODULOS = [
    {"id": "resumen", "titulo": "Resumen", "roles": TODOS},
    {"id": "citas", "titulo": "Citas", "roles": TODOS},
    {"id": "atencion", "titulo": "Atención", "roles": ADMIN_POD},
    {"id": "caja", "titulo": "Caja y boletas", "roles": ADMIN_RECEP},
    {"id": "clientes", "titulo": "Clientes", "roles": ADMIN_RECEP},
    {"id": "seguimiento", "titulo": "Seguimiento", "roles": ADMIN_RECEP},
    {"id": "servicios", "titulo": "Servicios", "roles": ADMIN},
    {"id": "medicamentos", "titulo": "Medicamentos", "roles": ADMIN},
    {"id": "personal", "titulo": "Personal", "roles": ADMIN},
    {"id": "usuarios", "titulo": "Usuarios y roles", "roles": ADMIN},
    {"id": "auditoria", "titulo": "Auditoría", "roles": ADMIN},
    {"id": "respaldo", "titulo": "Copia de seguridad", "roles": ADMIN},
]


def datos_usuario(sesion: dict) -> dict:
    """Lo que el cliente necesita saber de la sesión abierta."""
    return {
        "id": sesion["id"],
        "usuario": sesion["usuario"],
        "rol": sesion["rol"],
        "nombres": sesion["nombres"],
        "id_podologo": sesion["id_podologo"],
        "id_recep": sesion["id_recep"],
        "modulos": [m["id"] for m in MODULOS if sesion["rol"] in m["roles"]],
    }
