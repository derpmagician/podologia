#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conexión a SQL Server — Clínica Podológica.

Aquí vive todo lo que habla con el gestor de base de datos: la cadena de
conexión, los helpers de consulta y la clase de transacción. Lo usan las
rutas, el dominio y el servicio de respaldos.

La configuración se puede cambiar con variables de entorno:
    POD_SERVIDOR, POD_BASE, POD_DRIVER, POD_USUARIO, POD_CLAVE
"""

from __future__ import annotations

import os

import pyodbc

SERVIDOR = os.environ.get("POD_SERVIDOR", "localhost")
BASE_DATOS = os.environ.get("POD_BASE", "SQLData_ClinicaPodologicaV2")
DRIVER = os.environ.get("POD_DRIVER", "ODBC Driver 17 for SQL Server")
USUARIO_SQL = os.environ.get("POD_USUARIO")
CLAVE_SQL = os.environ.get("POD_CLAVE")


def cadena_conexion(base: str | None = None) -> str:
    partes = [
        "DRIVER={%s}" % DRIVER,
        "SERVER=%s" % SERVIDOR,
        "DATABASE=%s" % (base or BASE_DATOS),
        "TrustServerCertificate=yes",
        "Connection Timeout=10",
    ]
    if USUARIO_SQL and CLAVE_SQL:
        partes.append("UID=%s" % USUARIO_SQL)
        partes.append("PWD=%s" % CLAVE_SQL)
    else:
        partes.append("Trusted_Connection=yes")
    return ";".join(partes) + ";"


def conectar(base: str | None = None, autocommit: bool = False):
    """Sin argumento se conecta a la base del sistema.

    Pasar base="master" sirve para averiguar si la base existe y para crearla
    la primera vez, cuando todavía no se puede conectar a ella.
    autocommit=True es necesario para crear la base: SQL Server no permite
    CREATE DATABASE dentro de una transacción.
    """
    return pyodbc.connect(cadena_conexion(base), autocommit=autocommit)


def consultar(sql: str, args: tuple = ()) -> list[dict]:
    cn = conectar()
    try:
        cur = cn.cursor()
        cur.execute(sql, args)
        if cur.description is None:
            return []
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, list(fila))) for fila in cur.fetchall()]
    finally:
        cn.close()


def uno(sql: str, args: tuple = ()) -> dict | None:
    filas = consultar(sql, args)
    return filas[0] if filas else None


def ejecutar(sql: str, args: tuple = ()) -> int:
    cn = conectar()
    try:
        cur = cn.cursor()
        cur.execute(sql, args)
        n = cur.rowcount
        cn.commit()
        return n
    except Exception:
        cn.rollback()
        raise
    finally:
        cn.close()


class Tx:
    """Transacción: agrupa varias sentencias y confirma o deshace todo junto."""

    def __init__(self):
        self.cn = conectar()
        self.cur = self.cn.cursor()

    def ejecutar(self, sql: str, args: tuple = ()) -> int:
        self.cur.execute(sql, args)
        return self.cur.rowcount

    def insertar(self, sql: str, args: tuple = ()) -> int:
        self.cur.execute(lote_insert(sql), args)
        return int(self.cur.fetchone()[0])

    def uno(self, sql: str, args: tuple = ()) -> dict | None:
        self.cur.execute(sql, args)
        fila = self.cur.fetchone()
        if fila is None:
            return None
        cols = [c[0] for c in self.cur.description]
        return dict(zip(cols, list(fila)))

    def confirmar(self) -> None:
        self.cn.commit()

    def cerrar(self) -> None:
        self.cn.close()


def escalar(sql: str, args: tuple = (), defecto=0):
    fila = uno(sql, args)
    if not fila:
        return defecto
    valor = list(fila.values())[0]
    return defecto if valor is None else valor


def lote_insert(sql: str) -> str:
    """Envuelve un INSERT para que devuelva su IDENTITY en un único lote."""
    return ("SET NOCOUNT ON; " + sql.strip().rstrip(";")
            + "; SELECT CAST(SCOPE_IDENTITY() AS INT);")


def escalar_insert(sql: str, args: tuple = ()) -> int:
    """INSERT que devuelve el valor IDENTITY recién generado.

    El INSERT y la lectura de SCOPE_IDENTITY() deben viajar en un mismo lote
    (batch); de lo contrario SQL Server ya no recuerda el ámbito del INSERT.
    """
    cn = conectar()
    try:
        cur = cn.cursor()
        cur.execute(lote_insert(sql), args)
        nuevo = int(cur.fetchone()[0])
        cn.commit()
        return nuevo
    except Exception:
        cn.rollback()
        raise
    finally:
        cn.close()


# Columnas de cada tabla, en el orden del modelo físico. Se usan para exportar
# e importar sin depender de lo que devuelva cada consulta.
def columnas(tabla: str) -> list[str]:
    filas = consultar(
        """SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION""",
        (tabla,),
    )
    return [f["COLUMN_NAME"] for f in filas]
