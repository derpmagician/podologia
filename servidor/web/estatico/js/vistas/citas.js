/* ================================= CITAS ================================ */
/* Regla R1: un podólogo no puede tener dos citas a la misma fecha y hora.  */

import { DEL, GET, POST, intentar } from "../api.js";
import { catalogos, esAdmin, esPodo, esRecep } from "../estado.js";
import { $, avisar, badgeCita, esc, fechaBonita, hoy, limpiar, numero, tablaHtml, texto } from "../ui.js";
import { abrir, registrar } from "../navegacion.js";
import { abrirAtencion } from "./atenciones.js";

let citasEnMemoria = [];

async function verCitas() {
  const parametros = new URLSearchParams();
  if ($("cit-desde").value) parametros.set("desde", $("cit-desde").value);
  if ($("cit-hasta").value) parametros.set("hasta", $("cit-hasta").value);
  if ($("cit-festado").value) parametros.set("estado", $("cit-festado").value);
  if ($("cit-fpod").value) parametros.set("podologo", $("cit-fpod").value);

  const lista = await GET("/api/citas?" + parametros.toString());
  citasEnMemoria = lista;

  $("cit-tabla").innerHTML = tablaHtml(
    ["Fecha", "Hora", "Cliente", "Podólogo", "Motivo", "Estado", "Atención", ""],
    lista.map(c => {
      const acciones = [];
      if (!c.Id_Atencion && c.Estado !== "Cancelada" && esPodo()) {
        acciones.push(`<button class="btn btn-ok btn-sm" onclick="app.irAAtender(${c.Id_Cita})">Atender</button>`);
      }
      if (!c.Id_Atencion && esPodo()) {
        acciones.push(`<button class="btn btn-ghost btn-sm" onclick="app.cambiarEstado(${c.Id_Cita},'No asistio')">No asistió</button>`);
      }
      if (esAdmin() || esRecep()) {
        acciones.push(`<button class="btn btn-ghost btn-sm" onclick="app.editarCita(${c.Id_Cita})">Editar</button>`);
        if (!c.Id_Atencion) {
          acciones.push(`<button class="btn btn-danger btn-sm" onclick="app.eliminarCita(${c.Id_Cita})">Eliminar</button>`);
        }
      }
      return `<tr>
        <td>${fechaBonita(c.Fe_Cita)}</td>
        <td>${esc(c.Hora_Cita)}</td>
        <td>${esc(c.Cliente)}<div class="muted">DNI ${esc(c.Dni_Cliente || "—")}</div></td>
        <td>${esc(c.Podologo)}</td>
        <td>${esc(c.Motivo || "—")}</td>
        <td>${badgeCita(c.Estado)}</td>
        <td>${c.Id_Atencion ? `N.º ${c.Id_Atencion}` : "—"}</td>
        <td class="acciones">${acciones.join(" ") || '<span class="muted">—</span>'}</td>
      </tr>`;
    }),
    "No hay citas en el rango seleccionado."
  );
}

function citasDeHoy() {
  $("cit-desde").value = hoy();
  $("cit-hasta").value = hoy();
  $("cit-festado").value = "";
  $("cit-fpod").value = "";
  verCitas();
}

async function guardarCita() {
  const id = Number($("cit-id").value || 0);
  const cuerpo = {
    Id_Cita: id || undefined,
    Id_Cliente: numero("cit-cliente"),
    Id_Podologo: numero("cit-podologo"),
    Fe_Cita: $("cit-fecha").value,
    Hora_Cita: $("cit-hora").value,
    Estado: $("cit-estado").value,
    Motivo: texto("cit-motivo")
  };
  if (!cuerpo.Id_Cliente || !cuerpo.Id_Podologo || !cuerpo.Fe_Cita || !cuerpo.Hora_Cita) {
    return avisar("Complete cliente, podólogo, fecha y hora.", "error");
  }
  const r = await intentar(() => POST("/api/citas", cuerpo), id ? "Cita actualizada." : "Cita agendada.");
  if (r) { limpiarCita(); verCitas(); }
}

function editarCita(id) {
  const c = citasEnMemoria.find(x => x.Id_Cita === id);
  if (!c) return;
  $("cit-titulo").textContent = `Editando la cita N.º ${id}`;
  $("cit-id").value = c.Id_Cita;
  $("cit-cliente").value = c.Id_Cliente;
  $("cit-podologo").value = c.Id_Podologo;
  $("cit-fecha").value = String(c.Fe_Cita).slice(0, 10);
  $("cit-hora").value = String(c.Hora_Cita).slice(0, 5);
  $("cit-estado").value = c.Estado;
  $("cit-motivo").value = c.Motivo || "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarCita() {
  limpiar(["cit-id", "cit-motivo"]);
  $("cit-titulo").textContent = "Agendar cita";
  $("cit-fecha").value = hoy();
  $("cit-hora").value = "09:00";
  $("cit-estado").value = "Programada";
  if (catalogos.clientes.length) $("cit-cliente").value = catalogos.clientes[0].Id_Cliente;
  if (catalogos.podologos.length) $("cit-podologo").value = catalogos.podologos[0].Id_Podologo;
}

async function eliminarCita(id) {
  if (!confirm(`¿Eliminar la cita N.º ${id}? Esta acción queda registrada en la auditoría.`)) return;
  const r = await intentar(() => DEL(`/api/citas/${id}`), "Cita eliminada.");
  if (r) verCitas();
}

async function cambiarEstado(id, estado) {
  const r = await intentar(() => POST(`/api/citas/${id}/estado`, { Estado: estado }), `Cita marcada como ${estado}.`);
  if (r) verCitas();
}

function irAAtender(idCita) {
  abrir("atencion").then(() => {
    $("ate-cita").value = String(idCita);
    abrirAtencion();
  });
}

registrar("citas", verCitas);

export { verCitas, citasDeHoy, guardarCita, editarCita, limpiarCita, eliminarCita, cambiarEstado, irAAtender };
