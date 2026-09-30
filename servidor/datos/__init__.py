# -*- coding: utf-8 -*-
"""Capa de datos: conexión a SQL Server, helpers de consulta y transacciones."""

from datos.conexion import (  # noqa: F401
    BASE_DATOS,
    DRIVER,
    SERVIDOR,
    Tx,
    cadena_conexion,
    columnas,
    conectar,
    consultar,
    ejecutar,
    escalar,
    escalar_insert,
    lote_insert,
    uno,
)

__all__ = [
    "BASE_DATOS",
    "DRIVER",
    "SERVIDOR",
    "Tx",
    "cadena_conexion",
    "columnas",
    "conectar",
    "consultar",
    "ejecutar",
    "escalar",
    "escalar_insert",
    "lote_insert",
    "uno",
]
