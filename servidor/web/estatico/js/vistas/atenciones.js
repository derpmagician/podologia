/* =============================== ATENCIÓN =============================== */
/* El importe se calcula sumando los consumos; una atención facturada (R4)  */
/* queda bloqueada para el podólogo.                                        */

import { DEL, GET, POST, intentar } from "../api.js";
import { catalogos } from "../estado.js";
import { $, avisar, badgePago, badgeTipo, esc, fechaBonita, money, numero, opciones, tablaHtml, texto } from "../ui.js";
import { registrar } from "../navegacion.js";
import { recargarCatalogos } from "../catalogos.js";

let citasParaAtender = [];

async function verAtencion() {
  const lista = await GET("/api/citas");
  citasParaAtender = lista.filter(c => c.Estado !== "Cancelada");
  $("ate-cita").innerHTML = `<option value="">Seleccione la cita...</option>` + citasParaAtender.map(c =>
    `<option value="${c.Id_Cita}">${fechaBonita(c.Fe_Cita)} ${esc(c.Hora_Cita)} — ${esc(c.Cliente)}${c.Id_Atencion ? " · atendida N.º " + c.Id_Atencion : ""}</option>`
  ).join("");
  if (!$("ate-detalle").innerHTML.trim()) {
    $("ate-detalle").innerHTML = `<div class="panel"><p class="muted">Elija una cita para abrir la atención.</p></div>`;
  }
}

async function abrirAtencion() {
  const idCita = Number($("ate-cita").value || 0);
  if (!idCita) return avisar("Seleccione una cita.", "error");
  const cita = citasParaAtender.find(c => c.Id_Cita === idCita);
  if (cita && cita.Id_Atencion) return cargarAtencion(cita.Id_Atencion);

  const nueva = await intentar(() => POST("/api/atenciones", { Id_Cita: idCita }));
  if (nueva) {
    avisar("Atención iniciada. Registre el diagnóstico y los consumos.");
    await verAtencion();
    $("ate-cita").value = String(idCita);
    await cargarAtencion(nueva.Id_Atencion);
  }
}

async function buscarAtencionPorId() {
  const id = Number($("ate-buscar").value || 0);
  if (!id) return avisar("Escriba el número de atención.", "error");
  await cargarAtencion(id);
}

async function cargarAtencion(idAtencion) {
  const d = await intentar(() => GET(`/api/atenciones/${idAtencion}`));
  if (!d) return;
  aPintarAtencion(d);
}

function aPintarAtencion(d) {
  const c = d.cabecera;
  const facturada = !!c.Id_Boleta;
  const opcionesServicios = opciones(catalogos.servicios, "Id_Servicio", "Nom_serv", "");
  const opcionesMedicamentos = opciones(catalogos.medicamentos, "Id_Medicamento", "Nom_Med", "");

  const tablaServicios = tablaHtml(
    ["Servicio", "Precio", "Cant.", "Subtotal", ""],
    d.servicios.map(s => `<tr>
      <td>${esc(s.Nom_serv)}</td>
      <td>${money(s.Precio_Servicio)}</td>
      <td>${s.Cant_Aten}</td>
      <td>${money(s.Subt_Aten)}</td>
      <td class="acciones">${facturada ? '<span class="muted">—</span>' :
        `<button class="btn btn-danger btn-sm" onclick="app.quitarServicio(${c.Id_Atencion},${s.Id_Detalle_Aten})">Quitar</button>`}</td>
    </tr>`),
    "Aún no se agregaron servicios a esta atención."
  );

  const tablaMedicamentos = tablaHtml(
    ["Medicamento", "Precio", "Cant.", "Subtotal", ""],
    d.medicamentos.map(m => `<tr>
      <td>${esc(m.Nom_Med)}</td>
      <td>${money(m.Precio_Med)}</td>
      <td>${m.Cant_Med}</td>
      <td>${money(m.Subt_Med)}</td>
      <td class="acciones">${facturada ? '<span class="muted">—</span>' :
        `<button class="btn btn-danger btn-sm" onclick="app.quitarMedicamento(${c.Id_Atencion},${m.Id_Detalle_Med})">Quitar</button>`}</td>
    </tr>`),
    "Aún no se agregaron medicamentos a esta atención."
  );

  const tablaPagos = d.pagos.length ? tablaHtml(
    ["Pago N.º", "Tipo", "Monto", "Fecha"],
    d.pagos.map(p => `<tr>
      <td>${p.Id_Pago}</td><td>${badgeTipo(p.Tipo_Pago)}</td>
      <td>${money(p.Monto)}</td><td>${fechaBonita(p.Fe_Pago)}</td>
    </tr>`), "") : "";

  $("ate-detalle").innerHTML = `
    <div class="panel">
      <h2>Atención N.º ${c.Id_Atencion} — ${esc(c.Cliente)}
        ${facturada ? badgePago(c.Estado_Pago) : '<span class="badge b-pendiente">En consultorio</span>'}</h2>
      <p class="hint">
        Cita del ${fechaBonita(c.Fe_Cita)} a las ${esc(c.Hora_Cita)} ·
        ${esc(c.Podologo)} · Motivo: ${esc(c.Motivo || "—")} ·
        DNI ${esc(c.Dni_Cliente || "—")} · Tel. ${esc(c.Tel_Cliente || "—")}
      </p>
      ${facturada ? `<div class="aviso aviso-info">Regla R4: esta atención ya fue facturada con la boleta N.º ${c.Id_Boleta}, no se puede modificar.</div>` : ""}
      <div class="row">
        <div class="field"><label>Diagnóstico</label><textarea id="ate-diag" ${facturada ? "disabled" : ""}>${esc(c.Diag || "")}</textarea></div>
        <div class="field"><label>Tratamiento realizado</label><textarea id="ate-trat" ${facturada ? "disabled" : ""}>${esc(c.Trat || "")}</textarea></div>
        <div class="field"><label>Observaciones / indicaciones</label><textarea id="ate-obs" ${facturada ? "disabled" : ""}>${esc(c.Obs || "")}</textarea></div>
      </div>
      ${facturada ? "" : `<div class="actions"><button class="btn btn-primary" onclick="app.guardarFicha(${c.Id_Atencion})">Guardar ficha clínica</button></div>`}
    </div>

    <div class="panel">
      <h2>Servicios aplicados</h2>
      ${tablaServicios}
      ${facturada ? "" : `<h3>Agregar servicio</h3>
      <div class="row">
        <div class="field"><label>Servicio</label><select id="ate-servicio">${opcionesServicios}</select></div>
        <div class="field xs"><label>Cantidad</label><input id="ate-cant-serv" type="number" min="1" value="1" /></div>
        <div class="field sm" style="flex:0 1 auto"><button class="btn btn-ok" onclick="app.agregarServicio(${c.Id_Atencion})">Agregar</button></div>
      </div>`}
    </div>

    <div class="panel">
      <h2>Medicamentos entregados</h2>
      ${tablaMedicamentos}
      ${facturada ? "" : `<h3>Agregar medicamento (descuenta stock)</h3>
      <div class="row">
        <div class="field"><label>Medicamento</label><select id="ate-medicamento">${opcionesMedicamentos}</select></div>
        <div class="field xs"><label>Cantidad</label><input id="ate-cant-med" type="number" min="1" value="1" /></div>
        <div class="field sm" style="flex:0 1 auto"><button class="btn btn-ok" onclick="app.agregarMedicamento(${c.Id_Atencion})">Agregar</button></div>
      </div>`}
    </div>

    <div class="panel">
      <h2>Resumen de cobro</h2>
      <div class="grid-cards">
        <div class="kpi"><div class="label">Servicios</div><div class="value">${money(d.totales.servicios)}</div></div>
        <div class="kpi"><div class="label">Medicamentos</div><div class="value">${money(d.totales.medicamentos)}</div></div>
        <div class="kpi"><div class="label">Total a cobrar</div><div class="value">${money(d.totales.total)}</div></div>
      </div>
      ${tablaPagos}
    </div>`;
}

async function guardarFicha(idAtencion) {
  const r = await intentar(() => POST("/api/atenciones", {
    Id_Atencion: idAtencion,
    Diag: texto("ate-diag"),
    Trat: texto("ate-trat"),
    Obs: texto("ate-obs")
  }), "Ficha clínica guardada.");
  if (r) cargarAtencion(idAtencion);
}

async function agregarServicio(idAtencion) {
  const r = await intentar(() => POST(`/api/atenciones/${idAtencion}/servicios`, {
    Id_Servicio: numero("ate-servicio"),
    Cant_Aten: numero("ate-cant-serv")
  }), "Servicio agregado.");
  if (r) cargarAtencion(idAtencion);
}

async function quitarServicio(idAtencion, idDetalle) {
  const r = await intentar(() => DEL(`/api/atenciones/${idAtencion}/servicios/${idDetalle}`), "Servicio quitado.");
  if (r) cargarAtencion(idAtencion);
}

async function agregarMedicamento(idAtencion) {
  const r = await intentar(() => POST(`/api/atenciones/${idAtencion}/medicamentos`, {
    Id_Medicamento: numero("ate-medicamento"),
    Cant_Med: numero("ate-cant-med")
  }), "Medicamento agregado y stock descontado.");
  if (r) { await recargarCatalogos(); cargarAtencion(idAtencion); }
}

async function quitarMedicamento(idAtencion, idDetalle) {
  const r = await intentar(() => DEL(`/api/atenciones/${idAtencion}/medicamentos/${idDetalle}`), "Medicamento quitado y stock devuelto.");
  if (r) { await recargarCatalogos(); cargarAtencion(idAtencion); }
}

registrar("atencion", verAtencion);

export { verAtencion, abrirAtencion, buscarAtencionPorId, guardarFicha, agregarServicio, quitarServicio, agregarMedicamento, quitarMedicamento };
