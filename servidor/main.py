#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLÍNICA PODOLÓGICA — Sistema web con login, roles y auditoría.

Motor de base de datos : SQL Server  (base SQLData_ClinicaPodologicaV2)
Backend                : Python estándar + pyodbc (sin frameworks web)

Uso (desde la raíz del proyecto):
    python servidor/main.py                     -> http://127.0.0.1:8766
    python servidor/main.py --demo              -> carga datos de ejemplo y sale
    python servidor/main.py --reiniciar         -> vacía la base y sale
    python servidor/main.py --puerto 9000       -> cambia el puerto

Variables de entorno opcionales:
    POD_SERVIDOR  (por defecto localhost)
    POD_BASE      (por defecto SQLData_ClinicaPodologicaV2)
    POD_DRIVER    (por defecto "ODBC Driver 17 for SQL Server")
    POD_PUERTO    (por defecto 8766)
    POD_USUARIO / POD_CLAVE   -> si usa login de SQL Server en vez de Windows

Roles del sistema (política de seguridad del proyecto):
    Administrador  : control total, reportes y auditoría (regla R3).
    Recepcionista  : clientes, citas, boletas y pagos (counter).
    Podologo       : registro de atenciones, servicios y medicamentos.
"""

from __future__ import annotations

import sys

try:
    import pyodbc  # noqa: F401
except ImportError:  # pragma: no cover
    print("Falta el conector pyodbc. Instálelo con:  python -m pip install pyodbc")
    raise SystemExit(1)

try:
    import openpyxl  # noqa: F401
except ImportError:  # pragma: no cover
    print("Falta el conector openpyxl. Instálelo con:  python -m pip install openpyxl")
    raise SystemExit(1)

import config
import arranque
from api import rutas  # noqa: F401  (importarlo registra todas las rutas de la API)
from api.servidor import correr


def main():
    argumentos = sys.argv[1:]
    if "--demo" in argumentos:
        arranque.cargar_demo()
        return
    if "--reiniciar" in argumentos:
        arranque.preparar_base()
        arranque.reiniciar()
        return

    puerto = config.PUERTO
    if "--puerto" in argumentos:
        puerto = int(argumentos[argumentos.index("--puerto") + 1])

    print("=" * 68)
    print("CLÍNICA PODOLÓGICA — sistema web")
    print("=" * 68)
    arranque.preparar_base()
    print("Servidor SQL : %s" % arranque.describir_conexion())
    print("Dirección    : http://127.0.0.1:%d" % puerto)
    print("Para detener : Ctrl + C")
    print("=" * 68)
    correr(puerto)


if __name__ == "__main__":
    main()
