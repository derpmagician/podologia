#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registro de auditoría.

Se llama desde todas las operaciones que cambian datos. La auditoría es
secundaria: si falla, la operación principal continúa.
"""

from __future__ import annotations

from datos import ejecutar


def auditar(sesion: dict | None, accion: str, tabla: str = None, id_registro=None,
            detalle: str = None, equipo: str = None) -> None:
    """Registra el evento en AUDITORIA. Nunca debe romper la petición."""
    try:
        ejecutar(
            """INSERT INTO AUDITORIA
               (Id_Usuario, Usuario, Rol, Accion, Tabla, Id_Registro, Detalle, Equipo)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                (sesion or {}).get("id"),
                (sesion or {}).get("usuario"),
                (sesion or {}).get("rol"),
                accion,
                tabla,
                None if id_registro is None else str(id_registro)[:40],
                (detalle or "")[:400],
                (equipo or "")[:60],
            ),
        )
    except Exception as error:  # la auditoría es secundaria
        print("[aviso] no se pudo auditar:", error)
