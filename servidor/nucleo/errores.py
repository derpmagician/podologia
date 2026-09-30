#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Errores de la aplicación.

ErrorApi es la única excepción que llega al cliente con su mensaje: el resto
de excepciones se traducen a un mensaje genérico para no filtrar detalles.
"""

from __future__ import annotations


class ErrorApi(Exception):
    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def fallo(mensaje: str, codigo: int = 400):
    raise ErrorApi(mensaje, codigo)
