#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogos que alimentan los selectores de la interfaz."""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from datos import consultar
from nucleo.permisos import TODOS
from nucleo.utilidades import nombre_cliente, nombre_podologo


@ruta("GET", "/api/catalogos", TODOS)
def api_catalogos(p: Peticion):
    clientes = consultar(
        """SELECT Id_Cliente, Noms_Cliente, Ape_Pat_Cliente, Ape_Mat_Cliente, Dni_Cliente
           FROM CLIENTE ORDER BY Ape_Pat_Cliente, Ape_Mat_Cliente, Noms_Cliente"""
    )
    podologos = consultar(
        """SELECT Id_Podologo, Nom_Podologo, Ape_Pat_Podo, Ape_Mat_Podo, Esp_Podo
           FROM PODOLOGO ORDER BY Nom_Podologo"""
    )
    servicios = consultar(
        "SELECT Id_Servicio, Nom_serv, Precio_Servicio FROM SERVICIO ORDER BY Nom_serv"
    )
    medicamentos = consultar(
        """SELECT Id_Medicamento, Nom_Med, Precio_Med, Stock_Med, Fe_Venc_Med
           FROM MEDICAMENTO WHERE Stock_Med > 0 ORDER BY Nom_Med"""
    )
    for c in clientes:
        c["Nombre"] = nombre_cliente(c)
    for d in podologos:
        d["Nombre"] = nombre_podologo(d)
    return {
        "clientes": clientes,
        "podologos": podologos,
        "servicios": servicios,
        "medicamentos": medicamentos,
    }
