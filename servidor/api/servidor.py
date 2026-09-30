#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor HTTP de la clínica.

Sirve tres cosas: la API (/api/...), el index.html de la raíz y los archivos
estáticos de servidor/web/. No conoce las reglas del negocio: solo despacha.
"""

from __future__ import annotations

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pyodbc

import config
from api.enrutador import Descarga, Peticion, buscar
from nucleo.auditoria import auditar
from nucleo.errores import ErrorApi, fallo
from nucleo.seguridad import buscar_sesion
from nucleo.serializacion import serializar

TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "ClinicaPodologica/1.0"

    def log_message(self, formato, *args):
        print("[%s] %s" % (self.log_date_time_string(), formato % args))

    # -- utilidades de respuesta -------------------------------------------
    def _responder(self, codigo=200, cuerpo=b"", tipo="application/json; charset=utf-8", cabeceras=None):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for nombre, valor in (cabeceras or []):
            self.send_header(nombre, valor)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _json(self, objeto, codigo=200, cabeceras=None):
        crudo = json.dumps(objeto, ensure_ascii=False, default=serializar).encode("utf-8")
        self._responder(codigo, crudo, "application/json; charset=utf-8", cabeceras)

    def _cuerpo_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if not largo:
            return {}
        crudo = self.rfile.read(largo)
        try:
            return json.loads(crudo.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            fallo("El cuerpo de la petición no es un JSON válido.")

    def _cuerpo_binario(self) -> bytes:
        """Para las subidas de archivos: se recibe el contenido tal cual."""
        largo = int(self.headers.get("Content-Length") or 0)
        if not largo:
            return b""
        if largo > config.TAMANO_MAXIMO_SUBIDA:
            fallo("El archivo supera el tamaño máximo permitido (%d MB)."
                  % (config.TAMANO_MAXIMO_SUBIDA // (1024 * 1024)))
        return self.rfile.read(largo)

    def _descargar(self, archivo: Descarga):
        self._responder(200, archivo.contenido, archivo.tipo,
                        [("Content-Disposition", 'attachment; filename="%s"' % archivo.nombre)])

    def _token_sesion(self):
        galletas = self.headers.get("Cookie") or ""
        for parte in galletas.split(";"):
            nombre, _, valor = parte.strip().partition("=")
            if nombre == "sesion":
                return valor
        return None

    def _equipo(self):
        return self.client_address[0] if self.client_address else ""

    # -- archivos estáticos -------------------------------------------------
    def _servir_archivo(self, archivo: Path, raiz: Path) -> bool:
        """Sirve un archivo solo si está dentro de la carpeta permitida."""
        destino = archivo.resolve()
        try:
            destino.relative_to(raiz.resolve())
        except ValueError:
            return False
        if not destino.is_file():
            return False
        tipo = TIPOS.get(destino.suffix.lower(), "application/octet-stream")
        self._responder(200, destino.read_bytes(), tipo)
        return True

    def _servir_estatico(self, direccion: str) -> bool:
        """Todo lo que cuelga de /estatico/ vive en servidor/web/estatico/."""
        relativo = direccion[len("/estatico/"):]
        return self._servir_archivo(config.WEB_ESTATICO / relativo, config.WEB_ESTATICO)

    # -- despacho -----------------------------------------------------------
    def _atender(self, metodo: str):
        try:
            partes_url = urlparse(self.path)
            ruta_pedida = partes_url.path

            if ruta_pedida.startswith("/api/"):
                self._atender_api(metodo, ruta_pedida, partes_url.query)
                return

            if metodo != "GET":
                self._json({"error": "Método no permitido"}, 405)
                return
            if ruta_pedida in ("/", "/index.html"):
                if not self._servir_archivo(config.HTML_RAIZ, config.RAIZ):
                    self._json({"error": "Falta el archivo index.html"}, 500)
                return
            if ruta_pedida == "/login.html":
                if not self._servir_archivo(config.HTML_LOGIN, config.WEB):
                    self._json({"error": "Falta el archivo login.html"}, 500)
                return
            if ruta_pedida == "/favicon.ico":
                self._responder(204, b"", "image/x-icon")
                return
            if ruta_pedida.startswith("/estatico/") and self._servir_estatico(ruta_pedida):
                return
            self._json({"error": "No encontrado"}, 404)

        except ErrorApi as error:
            self._json({"error": error.mensaje}, error.codigo)
        except pyodbc.Error as error:
            self._json({"error": _mensaje_sql(error)}, 400)
        except Exception as error:
            print("[error]", traceback.format_exc())
            self._json({"error": "Error interno: %s" % error}, 500)

    def _atender_api(self, metodo: str, ruta_pedida: str, query: str):
        encontrada = buscar(metodo, ruta_pedida)
        if not encontrada:
            self._json({"error": "Ruta no encontrada"}, 404)
            return

        funcion, roles, grupos = encontrada
        sesion = buscar_sesion(self._token_sesion())

        if roles is not None:
            if not sesion:
                self._json({"error": "Su sesión expiró. Vuelva a iniciar sesión."}, 401)
                return
            if sesion["rol"] not in roles:
                auditar(sesion, "LOGIN_FALLIDO", "API", ruta_pedida,
                        "Acceso denegado a %s con rol %s" % (ruta_pedida, sesion["rol"]), self._equipo())
                self._json({"error": "Su rol (%s) no tiene permiso para esta operación." % sesion["rol"]}, 403)
                return

        parametros = {clave: valor[0] if valor else "" for clave, valor in parse_qs(query).items()}
        peticion = Peticion(metodo, grupos, parametros, {}, sesion, self._equipo())
        try:
            if metodo in ("POST", "PUT", "PATCH"):
                tipo = (self.headers.get("Content-Type") or "").lower()
                if "json" in tipo:
                    peticion.cuerpo = self._cuerpo_json() or {}
                else:
                    peticion.binario = self._cuerpo_binario()
            resultado = funcion(peticion)
            if isinstance(resultado, Descarga):
                self._descargar(resultado)
            else:
                self._json(resultado if resultado is not None else {"ok": True},
                           200, peticion.cabeceras)
        except ErrorApi as error:
            self._json({"error": error.mensaje}, error.codigo, peticion.cabeceras)

    def do_GET(self):
        self._atender("GET")

    def do_POST(self):
        self._atender("POST")

    def do_PUT(self):
        self._atender("PUT")

    def do_DELETE(self):
        self._atender("DELETE")

    def do_OPTIONS(self):
        self._responder(204, b"", "text/plain")


def _mensaje_sql(error) -> str:
    """Traduce el error de SQL Server a algo que el usuario pueda entender."""
    detalle = str(error)
    print("[sql]", detalle.replace("\n", " ")[:400])
    mayusculas = detalle.upper()
    if "UNIQUE" in mayusculas or "DUPLICATE" in mayusculas:
        return "Ya existe un registro con esos mismos datos."
    if "FOREIGN KEY" in mayusculas:
        return "La operación hace referencia a un registro que ya no existe."
    if "CHECK" in mayusculas or "TRIGGER" in mayusculas:
        return "Los datos no cumplen una regla del sistema (revise la regla R1 a R5)."
    return "No se pudo completar la operación en la base de datos."


def correr(puerto: int) -> None:
    ThreadingHTTPServer(("127.0.0.1", puerto), Handler).serve_forever()
