#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preparación de la base de datos.

Ejecuta los scripts de servidor/sql/ y crea el administrador inicial la
primera vez. También borra los datos cuando se pide --reiniciar.
"""

from __future__ import annotations

import re

import config
from datos import BASE_DATOS, SERVIDOR, conectar, escalar, escalar_insert, ejecutar
from nucleo.seguridad import cifrar_clave


def ejecutar_script_sql(texto: str, base: str = None, autocommit: bool = False) -> None:
    """Ejecuta un script .sql separado por lotes GO.

    autocommit=True hace falta para 00_esquema.sql: SQL Server no permite
    CREATE DATABASE dentro de una transacción.
    """
    lotes = re.split(r"(?im)^\s*GO\s*;?\s*$", texto)
    cn = conectar(base, autocommit=autocommit)
    try:
        for lote in lotes:
            if lote.strip():
                cn.cursor().execute(lote)
        if not autocommit:
            cn.commit()
    finally:
        cn.close()


def existe_base() -> bool:
    """Pregunta a master si la base del sistema ya está creada.

    No se puede consultar la base misma para saber si existe, así que la
    pregunta se hace desde master.
    """
    cn = conectar("master")
    try:
        cur = cn.cursor()
        cur.execute("SELECT COUNT(*) FROM sys.databases WHERE name = ?", (BASE_DATOS,))
        return cur.fetchone()[0] > 0
    finally:
        cn.close()


def crear_base() -> None:
    """Crea la base con 00_esquema.sql. La conexión va a master porque la base
    todavía no existe (no se podría conectar a ella)."""
    if not config.SQL_ESQUEMA.exists():
        print("AVISO: no se encontró %s" % config.SQL_ESQUEMA)
        print("       Cree la base con ese script antes de continuar.")
        return
    print("La base '%s' no existe: creándola..." % BASE_DATOS)
    ejecutar_script_sql(config.SQL_ESQUEMA.read_text(encoding="utf-8"),
                        base="master", autocommit=True)
    print("  Base creada con las 11 tablas del modelo físico.")


def preparar_base() -> None:
    if not existe_base():
        crear_base()

    if not config.SQL_INICIO.exists():
        print("AVISO: no se encontró %s" % config.SQL_INICIO)
        print("       Las tablas USUARIO y AUDITORIA deben existir para poder ingresar.")
    else:
        ejecutar_script_sql(config.SQL_INICIO.read_text(encoding="utf-8"))

    # Usuario administrador inicial (solo la primera vez).
    if escalar("SELECT COUNT(*) FROM USUARIO", (), 0) == 0:
        escalar_insert(
            """INSERT INTO USUARIO (Usuario, Clave_Hash, Rol, Nombres)
               VALUES (?,?,'Administrador',?)""",
            ("admin", cifrar_clave("admin123"), "Administrador del sistema"),
        )
        print("  Usuario inicial creado ->  usuario: admin    contraseña: admin123")
        print("  Cámbiela en el módulo 'Usuarios y roles' apenas ingrese.")


def cargar_demo() -> None:
    """Carga el ejemplo completo ejecutando el script sql/02_datos_demo.sql.

    El script es idempotente: si los registros ya existen, no los duplica.
    Se puede ejecutar también por separado con sqlcmd o SQL Server Management
    Studio, sin necesidad de Python.
    """
    preparar_base()
    if not config.SQL_DEMO.exists():
        print("AVISO: no se encontró %s" % config.SQL_DEMO)
        print("       Mantenga la carpeta servidor/sql para cargar el ejemplo.")
        return

    ejecutar_script_sql(config.SQL_DEMO.read_text(encoding="utf-8"))
    print("Datos de ejemplo cargados.")
    print("  admin      / admin123        (Administrador)")
    print("  recepcion  / recepcion123    (Recepcionista)")
    print("  podologo   / podologo123     (Podologo)")


def reiniciar() -> None:
    """Borra todos los registros. La base queda vacía (útil antes de presentar).

    Se desactiva momentáneamente el trigger de la regla R4 para poder limpiar
    las boletas pagadas; se vuelve a activar al terminar.
    """
    respuesta = input("Esto borrará TODOS los registros de la base. Escriba SI para continuar: ")
    if respuesta.strip().upper() != "SI":
        print("Cancelado. No se borró nada.")
        return

    ejecutar("ALTER TABLE BOLETA DISABLE TRIGGER TR_BOLETA_NoEliminarPagada")
    try:
        for tabla in ("PAGO", "BOLETA", "DETALLE_MEDICAMENTO", "DETALLE_ATENCION", "ATENCION",
                      "CITA", "AUDITORIA", "USUARIO", "MEDICAMENTO", "SERVICIO",
                      "RECEPCIONISTA", "PODOLOGO", "CLIENTE"):
            ejecutar("DELETE FROM %s" % tabla)
    finally:
        ejecutar("ALTER TABLE BOLETA ENABLE TRIGGER TR_BOLETA_NoEliminarPagada")

    print("Base de datos vacía. Ejecute 'python servidor/main.py --demo' para cargar el ejemplo.")


def describir_conexion() -> str:
    return "%s / %s" % (SERVIDOR, BASE_DATOS)
