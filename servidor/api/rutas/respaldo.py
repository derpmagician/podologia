#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copia de seguridad: exportar e importar en JSON y Excel (solo Administrador)."""

from __future__ import annotations

import json
import traceback
from datetime import date

from api.enrutador import Descarga, Peticion, ruta
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN
from nucleo.serializacion import serializar
import respaldos


@ruta("GET", "/api/respaldo", ADMIN)
def api_respaldo(p: Peticion):
    return {"tablas": respaldos.contar_tablas()}


@ruta("GET", "/api/respaldo/json", ADMIN)
def api_respaldo_json(p: Peticion):
    paquete = respaldos.exportar_json()
    total = sum(len(f) for f in paquete["tablas"].values())
    auditar(p.sesion, "EXPORTAR", "RESPALDO", None,
            "Descargó el respaldo JSON (%d registros)" % total, p.equipo)
    crudo = json.dumps(paquete, ensure_ascii=False, indent=2, default=serializar).encode("utf-8")
    return Descarga(crudo, "podologia-respaldo-%s.json" % date.today(), "application/json; charset=utf-8")


@ruta("GET", "/api/respaldo/excel", ADMIN)
def api_respaldo_excel(p: Peticion):
    contenido = respaldos.exportar_excel()
    auditar(p.sesion, "EXPORTAR", "RESPALDO", None,
            "Descargó el respaldo Excel (%d KB)" % (len(contenido) // 1024), p.equipo)
    return Descarga(contenido, "podologia-respaldo-%s.xlsx" % date.today(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@ruta("POST", "/api/respaldo/json", ADMIN)
def api_importar_json(p: Peticion):
    try:
        resumen = respaldos.importar_json(p.cuerpo)
    except ValueError as error:
        fallo(str(error))
    except Exception as error:
        print("[importar json]", traceback.format_exc().splitlines()[-1])
        fallo("No se pudo importar el JSON: %s" % error)
    auditar(p.sesion, "IMPORTAR", "RESPALDO", None,
            "Importó un respaldo JSON (%d nuevos, %d actualizados)"
            % (resumen["total_insertados"], resumen["total_actualizados"]), p.equipo)
    return resumen


@ruta("POST", "/api/respaldo/excel", ADMIN)
def api_importar_excel(p: Peticion):
    if not p.binario:
        fallo("No se recibió el archivo Excel.")
    try:
        resumen = respaldos.importar_excel(p.binario)
    except ValueError as error:
        fallo(str(error))
    except Exception as error:
        print("[importar excel]", traceback.format_exc().splitlines()[-1])
        fallo("No se pudo importar el Excel: %s" % error)
    auditar(p.sesion, "IMPORTAR", "RESPALDO", None,
            "Importó un respaldo Excel (%d nuevos, %d actualizados)"
            % (resumen["total_insertados"], resumen["total_actualizados"]), p.equipo)
    return resumen
