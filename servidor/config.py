#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración del sistema — rutas, puerto y constantes.

Aquí se resuelve dónde está cada cosa dentro del proyecto. Ningún otro módulo
debería construir rutas por su cuenta.

Variables de entorno opcionales:
    POD_PUERTO    (por defecto 8766)
"""

from __future__ import annotations

import os
from pathlib import Path

# servidor/  <-  aquí vive este archivo
BASE = Path(__file__).resolve().parent
# La raíz del proyecto es la carpeta que contiene servidor/ y index.html.
RAIZ = BASE.parent

# El único archivo que vive en la raíz del proyecto.
HTML_RAIZ = RAIZ / "index.html"

# Recursos servidos por HTTP.
WEB = BASE / "web"
WEB_ESTATICO = WEB / "estatico"
HTML_LOGIN = WEB / "login.html"

# Scripts de base de datos, en orden de ejecución.
SQL_DIR = BASE / "sql"
SQL_ESQUEMA = SQL_DIR / "00_esquema.sql"
SQL_INICIO = SQL_DIR / "01_usuarios_auditoria.sql"
SQL_DEMO = SQL_DIR / "02_datos_demo.sql"

PUERTO = int(os.environ.get("POD_PUERTO", "8766"))

DURACION_SESION = 8 * 3600
ITERACIONES_PBKDF2 = 120_000
TAMANO_MAXIMO_SUBIDA = 20 * 1024 * 1024   # 20 MB para los archivos de respaldo
