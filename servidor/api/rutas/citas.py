#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Citas — regla R1: un podólogo no puede tener dos citas activas a la misma
fecha y hora. La validación vive en dominio/citas.py.
"""

from __future__ import annotations

from api.enrutador import Peticion, ruta
from datos import consultar, escalar, escalar_insert, ejecutar, uno
from dominio.citas import verificar_disponibilidad, verificar_estado
from nucleo.auditoria import auditar
from nucleo.errores import fallo
from nucleo.permisos import ADMIN_RECEP, TODOS
from nucleo.utilidades import a_fecha, a_hora, entero, hace_falta


@ruta("GET", "/api/citas", TODOS)
def api_citas(p: Peticion):
    desde = p.filtro("desde", 10)
    hasta = p.filtro("hasta", 10)
    estado = p.filtro("estado", 20)
    id_pod = entero(p.filtro("podologo", 10), 0)
    id_cli = entero(p.filtro("cliente", 10), 0)
    solo_hoy = p.filtro("hoy", 2) == "1"

    # Un podólogo solo ve su propia agenda.
    if p.rol == "Podologo":
        id_pod = p.sesion["id_podologo"]

    sql = """
        SELECT c.Id_Cita, c.Fe_Cita, c.Hora_Cita, c.Estado, c.Motivo,
               c.Id_Cliente, c.Id_Podologo, c.Id_Recep,
               cl.Noms_Cliente + ' ' + ISNULL(cl.Ape_Pat_Cliente,'') + ' ' + ISNULL(cl.Ape_Mat_Cliente,'') AS Cliente,
               cl.Dni_Cliente, cl.Tel_Cliente,
               pd.Nom_Podologo + ' ' + ISNULL(pd.Ape_Pat_Podo,'') + ' ' + ISNULL(pd.Ape_Mat_Podo,'') AS Podologo,
               rc.Noms_Recep + ' ' + ISNULL(rc.Apellidos_Recep,'') AS Recepcionista,
               a.Id_Atencion,
               (SELECT COUNT(*) FROM BOLETA b WHERE b.Id_Atencion = a.Id_Atencion) AS Boletas
        FROM CITA c
        JOIN CLIENTE cl      ON cl.Id_Cliente   = c.Id_Cliente
        JOIN PODOLOGO pd     ON pd.Id_Podologo  = c.Id_Podologo
        LEFT JOIN RECEPCIONISTA rc ON rc.Id_Recep = c.Id_Recep
        LEFT JOIN ATENCION a ON a.Id_Cita = c.Id_Cita
        WHERE 1 = 1"""
    args: list = []
    if solo_hoy:
        sql += " AND c.Fe_Cita = CAST(GETDATE() AS DATE)"
    if desde:
        sql += " AND c.Fe_Cita >= ?"
        args.append(a_fecha(desde))
    if hasta:
        sql += " AND c.Fe_Cita <= ?"
        args.append(a_fecha(hasta))
    if estado:
        sql += " AND c.Estado = ?"
        args.append(estado)
    if id_pod:
        sql += " AND c.Id_Podologo = ?"
        args.append(id_pod)
    if id_cli:
        sql += " AND c.Id_Cliente = ?"
        args.append(id_cli)
    sql += " ORDER BY c.Fe_Cita DESC, c.Hora_Cita"
    return consultar(sql, tuple(args))


@ruta("POST", "/api/citas", ADMIN_RECEP)
def api_guardar_cita(p: Peticion):
    id_cita = entero(p.cuerpo.get("Id_Cita"), 0)
    id_cliente = entero(p.cuerpo.get("Id_Cliente"), 0)
    id_pod = entero(p.cuerpo.get("Id_Podologo"), 0)
    fe_cita = a_fecha(p.campo("Fe_Cita", 10))
    hora_cita = a_hora(p.campo("Hora_Cita", 8))
    estado = p.campo("Estado", 30) or "Programada"
    motivo = p.campo("Motivo", 200)

    hace_falta(id_cliente, "Seleccione el cliente.")
    hace_falta(id_pod, "Seleccione el podólogo.")
    hace_falta(fe_cita, "Indique la fecha de la cita.")
    verificar_estado(estado)
    hace_falta(uno("SELECT Id_Cliente FROM CLIENTE WHERE Id_Cliente = ?", (id_cliente,)),
               "El cliente indicado no existe.", 404)
    hace_falta(uno("SELECT Id_Podologo FROM PODOLOGO WHERE Id_Podologo = ?", (id_pod,)),
               "El podólogo indicado no existe.", 404)

    if estado != "Cancelada":
        verificar_disponibilidad(id_pod, fe_cita, hora_cita, id_cita)

    datos = (id_cliente, id_pod, p.sesion["id_recep"] if p.rol == "Recepcionista" else None,
             fe_cita, hora_cita, estado, motivo)
    try:
        if id_cita:
            ejecutar(
                """UPDATE CITA SET Id_Cliente=?, Id_Podologo=?, Id_Recep=?, Fe_Cita=?, Hora_Cita=?,
                   Estado=?, Motivo=? WHERE Id_Cita=?""", datos + (id_cita,)
            )
            auditar(p.sesion, "UPDATE", "CITA", id_cita,
                    "Actualizó la cita del %s %s (%s)" % (fe_cita, hora_cita.strftime("%H:%M"), estado), p.equipo)
        else:
            id_cita = escalar_insert(
                """INSERT INTO CITA (Id_Cliente, Id_Podologo, Id_Recep, Fe_Cita, Hora_Cita, Estado, Motivo)
                   VALUES (?,?,?,?,?,?,?)""", datos
            )
            auditar(p.sesion, "INSERT", "CITA", id_cita,
                    "Agendó cita para el %s a las %s" % (fe_cita, hora_cita.strftime("%H:%M")), p.equipo)
    except Exception as error:
        # El índice único UX_CITA_Podologo_Fecha_Hora atrapa las carreras.
        if "UX_CITA" in str(error) or "duplicate" in str(error).lower():
            fallo("Regla R1: el podólogo ya tiene una cita en ese horario.")
        raise
    return uno("SELECT * FROM CITA WHERE Id_Cita = ?", (id_cita,))


@ruta("POST", "/api/citas/(?P<id>\\d+)/estado", TODOS)
def api_estado_cita(p: Peticion):
    id_cita = p.identificador()
    estado = p.campo("Estado", 30)
    verificar_estado(estado)
    cita = uno("SELECT * FROM CITA WHERE Id_Cita = ?", (id_cita,))
    hace_falta(cita, "La cita no existe.", 404)
    if p.rol == "Podologo" and cita["Id_Podologo"] != p.sesion["id_podologo"]:
        fallo("Solo puede cambiar el estado de sus propias citas.", 403)
    tiene_atencion = escalar("SELECT COUNT(*) FROM ATENCION WHERE Id_Cita = ?", (id_cita,), 0)
    if tiene_atencion and estado == "Cancelada":
        fallo("La cita ya tiene una atención registrada: no se puede cancelar.")
    ejecutar("UPDATE CITA SET Estado = ? WHERE Id_Cita = ?", (estado, id_cita))
    auditar(p.sesion, "UPDATE", "CITA", id_cita, "Cambió el estado de la cita a %s" % estado, p.equipo)
    return uno("SELECT * FROM CITA WHERE Id_Cita = ?", (id_cita,))


@ruta("DELETE", "/api/citas/(?P<id>\\d+)", ADMIN_RECEP)
def api_borrar_cita(p: Peticion):
    id_cita = p.identificador()
    if escalar("SELECT COUNT(*) FROM ATENCION WHERE Id_Cita = ?", (id_cita,), 0):
        fallo("La cita ya tiene una atención registrada: no se puede eliminar.")
    ejecutar("DELETE FROM CITA WHERE Id_Cita = ?", (id_cita,))
    auditar(p.sesion, "DELETE", "CITA", id_cita, "Eliminó una cita", p.equipo)
    return {"ok": True}
