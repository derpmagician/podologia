#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resumen, seguimiento de pacientes y auditoría."""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from datos import consultar, escalar
from nucleo.permisos import ADMIN, ADMIN_RECEP, TODOS
from nucleo.utilidades import a_fecha, entero


@ruta("GET", "/api/resumen", TODOS)
def api_resumen(p: Peticion):
    kpis = {
        "citas_hoy": escalar(
            "SELECT COUNT(*) FROM CITA WHERE Fe_Cita = CAST(GETDATE() AS DATE) AND Estado <> 'Cancelada'", (), 0),
        "atenciones_mes": escalar(
            """SELECT COUNT(*) FROM ATENCION
               WHERE MONTH(Fe_Atencion) = MONTH(GETDATE()) AND YEAR(Fe_Atencion) = YEAR(GETDATE())""", (), 0),
        "cobrado_mes": float(escalar(
            """SELECT ISNULL(SUM(Monto),0) FROM PAGO
               WHERE MONTH(Fe_Pago) = MONTH(GETDATE()) AND YEAR(Fe_Pago) = YEAR(GETDATE())""", (), 0)),
        "por_cobrar": float(escalar(
            """SELECT ISNULL(SUM(b.Importe - ISNULL(p.pagado, 0)), 0)
               FROM BOLETA b
               LEFT JOIN (SELECT Id_Boleta, SUM(Monto) AS pagado
                          FROM PAGO GROUP BY Id_Boleta) p ON p.Id_Boleta = b.Id_Boleta
               WHERE b.Estado_Pago = 'Pendiente'""", (), 0)),
        "boletas_pendientes": escalar(
            "SELECT COUNT(*) FROM BOLETA WHERE Estado_Pago = 'Pendiente'", (), 0),
        "clientes": escalar("SELECT COUNT(*) FROM CLIENTE", (), 0),
        "sin_facturar": escalar(
            """SELECT COUNT(*) FROM ATENCION a
               WHERE NOT EXISTS (SELECT 1 FROM BOLETA b WHERE b.Id_Atencion = a.Id_Atencion)""", (), 0),
        "stock_bajo": escalar("SELECT COUNT(*) FROM MEDICAMENTO WHERE Stock_Med < 5", (), 0),
        "por_vencer": escalar(
            """SELECT COUNT(*) FROM MEDICAMENTO
               WHERE Fe_Venc_Med IS NOT NULL AND DATEDIFF(DAY, GETDATE(), Fe_Venc_Med) <= 30""", (), 0),
    }
    agenda_hoy = consultar(
        """SELECT c.Id_Cita, c.Hora_Cita, c.Estado, c.Motivo,
                  cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') AS Cliente,
                  pd.Nom_Podologo + ' ' + ISNULL(pd.Ape_Pat_Podo,'') AS Podologo,
                  a.Id_Atencion
           FROM CITA c
           JOIN CLIENTE cl  ON cl.Id_Cliente = c.Id_Cliente
           JOIN PODOLOGO pd ON pd.Id_Podologo = c.Id_Podologo
           LEFT JOIN ATENCION a ON a.Id_Cita = c.Id_Cita
           WHERE c.Fe_Cita = CAST(GETDATE() AS DATE)
           ORDER BY c.Hora_Cita"""
    )
    ultimas = consultar(
        """SELECT TOP 8 a.Id_Atencion, a.Fe_Atencion, a.Diag,
                  cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') AS Cliente,
                  pd.Nom_Podologo + ' ' + ISNULL(pd.Ape_Pat_Podo,'') AS Podologo,
                  b.Id_Boleta, b.Estado_Pago, b.Importe,
                  ISNULL((SELECT SUM(d.Subt_Aten) FROM DETALLE_ATENCION d WHERE d.Id_Atencion=a.Id_Atencion),0)
                + ISNULL((SELECT SUM(d.Subt_Med)  FROM DETALLE_MEDICAMENTO d WHERE d.Id_Atencion=a.Id_Atencion),0) AS Total
           FROM ATENCION a
           JOIN CITA c ON c.Id_Cita = a.Id_Cita
           JOIN CLIENTE cl ON cl.Id_Cliente = c.Id_Cliente
           JOIN PODOLOGO pd ON pd.Id_Podologo = c.Id_Podologo
           LEFT JOIN BOLETA b ON b.Id_Atencion = a.Id_Atencion
           ORDER BY a.Fe_Atencion DESC, a.Id_Atencion DESC"""
    )
    top_servicios = consultar(
        """SELECT TOP 5 s.Nom_serv, SUM(d.Cant_Aten) AS Veces, SUM(d.Subt_Aten) AS Importe
           FROM DETALLE_ATENCION d JOIN SERVICIO s ON s.Id_Servicio = d.Id_Servicio
           GROUP BY s.Nom_serv ORDER BY SUM(d.Cant_Aten) DESC"""
    )
    return {"kpis": kpis, "agenda_hoy": agenda_hoy, "ultimas": ultimas, "top_servicios": top_servicios}


@ruta("GET", "/api/seguimiento", ADMIN_RECEP)
def api_seguimiento(p: Peticion):
    """Pacientes que no vuelven hace N días (por defecto 30)."""
    dias = entero(p.filtro("dias", 4), 30) or 30
    return consultar(
        """SELECT c.Id_Cliente,
                  c.Noms_Cliente + ' ' + ISNULL(c.Ape_Pat_Cliente,'') + ' ' + ISNULL(c.Ape_Mat_Cliente,'') AS Cliente,
                  c.Dni_Cliente, c.Tel_Cliente, c.Email_Cliente,
                  (SELECT MAX(a.Fe_Atencion) FROM CITA ci
                     JOIN ATENCION a ON a.Id_Cita = ci.Id_Cita
                    WHERE ci.Id_Cliente = c.Id_Cliente) AS Ultima_Atencion,
                  (SELECT TOP 1 a.Trat FROM CITA ci
                     JOIN ATENCION a ON a.Id_Cita = ci.Id_Cita
                    WHERE ci.Id_Cliente = c.Id_Cliente
                    ORDER BY a.Fe_Atencion DESC, a.Id_Atencion DESC) AS Ultimo_Tratamiento,
                  DATEDIFF(DAY,
                      (SELECT MAX(a.Fe_Atencion) FROM CITA ci
                         JOIN ATENCION a ON a.Id_Cita = ci.Id_Cita
                        WHERE ci.Id_Cliente = c.Id_Cliente), GETDATE()) AS Dias_Sin_Volver,
                  (SELECT COUNT(*) FROM CITA ci
                    WHERE ci.Id_Cliente = c.Id_Cliente AND ci.Fe_Cita >= CAST(GETDATE() AS DATE)
                      AND ci.Estado = 'Programada') AS Citas_Futuras
           FROM CLIENTE c
           WHERE NOT EXISTS (
                 SELECT 1 FROM CITA ci
                 JOIN ATENCION a ON a.Id_Cita = ci.Id_Cita
                 WHERE ci.Id_Cliente = c.Id_Cliente
                   AND DATEDIFF(DAY, a.Fe_Atencion, GETDATE()) < ?)
           ORDER BY Dias_Sin_Volver DESC""",
        (dias,),
    )


@ruta("GET", "/api/auditoria", ADMIN)
def api_auditoria(p: Peticion):
    accion = p.filtro("accion", 25)
    usuario = p.filtro("usuario", 50)
    desde = p.filtro("desde", 10)
    hasta = p.filtro("hasta", 10)
    sql = "SELECT TOP 300 * FROM AUDITORIA WHERE 1 = 1"
    args: list = []
    if accion:
        sql += " AND Accion = ?"
        args.append(accion)
    if usuario:
        sql += " AND Usuario LIKE ?"
        args.append("%" + usuario + "%")
    if desde:
        sql += " AND Fe_Evento >= ?"
        args.append(a_fecha(desde))
    if hasta:
        sql += " AND Fe_Evento < DATEADD(DAY, 1, ?)"
        args.append(a_fecha(hasta))
    sql += " ORDER BY Id_Auditoria DESC"
    return consultar(sql, tuple(args))
