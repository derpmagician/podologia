# -*- coding: utf-8 -*-
"""
Rutas de la API.

Importar este paquete registra todas las rutas en el enrutador. Cada módulo
se ocupa de un módulo funcional del sistema.
"""

from api.rutas import (  # noqa: F401
    atenciones,
    boletas,
    catalogos,
    citas,
    clientes,
    medicamentos,
    personal,
    reportes,
    respaldo,
    servicios,
    sesion,
    usuarios,
)
