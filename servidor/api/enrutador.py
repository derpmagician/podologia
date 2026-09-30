#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enrutador: registro de rutas y objetos de petición / respuesta.

Cada módulo de api/rutas/ decora sus funciones con @ruta y queda registrado
aquí. El servidor HTTP solo busca la coincidencia y ejecuta.
"""

from __future__ import annotations

import re

from nucleo.utilidades import entero, txt

RUTAS: list[tuple] = []


def ruta(metodo: str, patron: str, roles=None):
    """roles=None -> público; roles=tupla -> exige sesión con ese rol."""
    def decorador(fn):
        RUTAS.append((metodo, re.compile("^" + patron + "$"), fn, roles))
        return fn
    return decorador


def buscar(metodo: str, ruta_pedida: str):
    """Primera ruta registrada que coincida con el método y la dirección."""
    for metodo_ruta, patron, funcion, roles in RUTAS:
        if metodo_ruta != metodo:
            continue
        coincidencia = patron.match(ruta_pedida)
        if coincidencia:
            return funcion, roles, coincidencia.groupdict()
    return None


class Descarga:
    """Respuesta que no es JSON: un archivo para descargar."""

    def __init__(self, contenido: bytes, nombre: str, tipo: str):
        self.contenido = contenido
        self.nombre = nombre
        self.tipo = tipo


class Peticion:
    def __init__(self, metodo, partes, query, cuerpo, sesion, equipo):
        self.metodo = metodo
        self.partes = partes
        self.query = query
        self.cuerpo = cuerpo or {}
        self.binario: bytes | None = None
        self.sesion = sesion
        self.equipo = equipo
        self.cabeceras: list[tuple[str, str]] = []

    @property
    def id_usuario(self):
        return self.sesion["id"] if self.sesion else None

    @property
    def rol(self):
        return self.sesion["rol"] if self.sesion else None

    def campo(self, nombre, limite: int = 200) -> str:
        return txt(self.cuerpo.get(nombre), limite)

    def filtro(self, nombre, limite: int = 60) -> str:
        valor = self.query.get(nombre)
        return txt(valor[0] if isinstance(valor, list) else valor, limite)

    def identificador(self, nombre="id") -> int:
        return entero(self.partes.get(nombre), 0)
