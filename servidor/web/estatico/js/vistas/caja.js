/* ================================= CAJA ================================= */
/* Reglas R2 (los pagos no superan el importe) y R4 (boleta pagada no se     */
/* modifica ni se elimina).                                                 */

import { DEL, GET, POST, intentar } from "../api.js";
import { esAdmin } from "../estado.js";
import { $, abrirModal, avisar, badgePago, badgeTipo, cerrarModal, esc, fechaBonita, money, numero, tablaHtml } from "../ui.js";
import { registrar } from "../navegacion.js";

async function verCaja() {
  const pendientes = await GET("/api/atenciones?sin_boleta=1");
  const totalPendiente = pendientes.reduce((s, a) => s + Number(a.Total_Servicios || 0) + Number(a.Total_Medicamentos || 0), 0);
  $("caja-pend-total").textContent = pendientes.length ? `${pendientes.length} atención(es) · ${money(totalPendiente)}` : "";

  $("caja-pendientes").innerHTML = tablaHtml(
    ["Fecha", "Cliente", "Podólogo", "Diagnóstico", "Servicios", "Medicamentos", "Total", ""],
    pendientes.map(a => {
      const total = Number(a.Total_Servicios || 0) + Number(a.Total_Medicamentos || 0);
      return `<tr>
        <td>${fechaBonita(a.Fe_Atencion)}</td>
        <td>${esc(a.Cliente)}</td>
        <td>${esc(a.Podologo)}</td>
        <td>${esc(a.Diag || "—")}</td>
        <td>${money(a.Total_Servicios)}</td>
        <td>${money(a.Total_Medicamentos)}</td>
        <td><strong>${money(total)}</strong></td>
        <td class="acciones">
          <button class="btn btn-ghost btn-sm" onclick="app.verDetalleAtencion(${a.Id_Atencion})">Ver</button>
          <button class="btn btn-primary btn-sm" onclick="app.emitirBoleta(${a.Id_Atencion})">Generar boleta</button>
        </td>
      </tr>`;
    }),
    "No hay atenciones pendientes de facturar."
  );

  await verBoletas();
}

async function verBoletas() {
  const parametros = new URLSearchParams();
  if ($("caja-desde").value) parametros.set("desde", $("caja-desde").value);
  if ($("caja-hasta").value) parametros.set("hasta", $("caja-hasta").value);
  if ($("caja-estado").value) parametros.set("estado", $("caja-estado").value);

  const lista = await GET("/api/boletas?" + parametros.toString());
  $("caja-boletas").innerHTML = tablaHtml(
    ["Boleta", "Emisión", "Cliente", "Podólogo", "Importe", "Pagado", "Saldo", "Estado", ""],
    lista.map(b => {
      const saldo = Number(b.Importe) - Number(b.Pagado);
      const acciones = [`<button class="btn btn-ghost btn-sm" onclick="app.verBoleta(${b.Id_Boleta},${b.Id_Atencion})">Ver</button>`];
      if (b.Estado_Pago !== "Pagada") {
        acciones.push(`<button class="btn btn-primary btn-sm" onclick="app.cobrar(${b.Id_Boleta})">Cobrar</button>`);
      }
      if (esAdmin() && b.Estado_Pago !== "Pagada" && Number(b.N_Pagos) === 0) {
        acciones.push(`<button class="btn btn-danger btn-sm" onclick="app.anularBoleta(${b.Id_Boleta})">Anular</button>`);
      }
      return `<tr>
        <td>N.º ${b.Id_Boleta}</td>
        <td>${fechaBonita(b.Fe_Emision)}</td>
        <td>${esc(b.Cliente)}</td>
        <td>${esc(b.Podologo)}</td>
        <td>${money(b.Importe)}</td>
        <td>${money(b.Pagado)}</td>
        <td>${money(saldo)}</td>
        <td>${badgePago(b.Estado_Pago)}</td>
        <td class="acciones">${acciones.join(" ")}</td>
      </tr>`;
    }),
    "Todavía no se emitieron boletas."
  );
}

async function emitirBoleta(idAtencion) {
  if (!confirm(`¿Emitir la boleta de la atención N.º ${idAtencion}?`)) return;
  const r = await intentar(() => POST("/api/boletas", { Id_Atencion: idAtencion }));
  if (r) {
    avisar(`Boleta N.º ${r.Id_Boleta} emitida por ${money(r.Importe)}.`);
    verCaja();
  }
}

async function cobrar(idBoleta) {
  const lista = await intentar(() => GET("/api/boletas"));
  if (!lista) return;
  const boleta = lista.find(x => x.Id_Boleta === idBoleta);
  if (!boleta) return avisar("No se encontró la boleta.", "error");

  const detalle = await intentar(() => GET(`/api/atenciones/${boleta.Id_Atencion}`));
  const saldo = Number(boleta.Importe) - Number(boleta.Pagado);

  const pagos = (detalle && detalle.pagos.length) ? tablaHtml(
    ["Pago", "Tipo", "Monto", "Fecha"],
    detalle.pagos.map(p => `<tr><td>${p.Id_Pago}</td><td>${badgeTipo(p.Tipo_Pago)}</td>
      <td>${money(p.Monto)}</td><td>${fechaBonita(p.Fe_Pago)}</td></tr>`), "") : '<p class="muted">Sin pagos registrados.</p>';

  abrirModal(`
    <h2>Cobrar boleta N.º ${boleta.Id_Boleta}</h2>
    <p class="hint">${esc(boleta.Cliente)} · DNI ${esc(boleta.Dni_Cliente || "—")} · emitida el ${fechaBonita(boleta.Fe_Emision)}</p>
    <div class="grid-cards">
      <div class="kpi"><div class="label">Importe</div><div class="value">${money(boleta.Importe)}</div></div>
      <div class="kpi"><div class="label">Pagado</div><div class="value">${money(boleta.Pagado)}</div></div>
      <div class="kpi alerta"><div class="label">Saldo</div><div class="value">${money(saldo)}</div></div>
    </div>
    <h3>Pagos registrados</h3>
    ${pagos}
    ${boleta.Estado_Pago === "Pagada" ? '<div class="aviso aviso-ok">Regla R4: boleta pagada y cerrada, no admite más cambios.</div>' : `
      <h3>Registrar pago</h3>
      <div class="row">
        <div class="field sm"><label>Tipo de pago</label>
          <select id="pag-tipo">
            <option value="Efectivo">Efectivo</option>
            <option value="Tarjeta">Tarjeta</option>
            <option value="Yape">Yape</option>
            <option value="Transferencia">Transferencia</option>
          </select>
        </div>
        <div class="field sm"><label>Monto (S/)</label><input id="pag-monto" type="number" min="0.01" step="0.01" value="${saldo.toFixed(2)}" /></div>
        <div class="field sm" style="flex:0 1 auto">
          <button class="btn btn-primary" onclick="app.registrarPago(${boleta.Id_Boleta}, ${saldo})">Registrar pago</button>
        </div>
      </div>
      <p class="hint" style="margin-top:10px">Regla R2: la suma de los pagos no puede superar el importe de la boleta.</p>`}
  `);
}

async function registrarPago(idBoleta, saldo) {
  const monto = numero("pag-monto");
  if (!(monto > 0)) return avisar("Indique un monto mayor que cero.", "error");

  const r = await intentar(() => POST(`/api/boletas/${idBoleta}/pagos`, {
    Tipo_Pago: $("pag-tipo").value,
    Monto: monto
  }));
  if (!r) return;

  if (r.estado === "Pagada") {
    avisar(`Boleta N.º ${idBoleta} pagada y cerrada.`);
    cerrarModal();
  } else {
    avisar(`Pago registrado. Saldo pendiente: ${money(r.saldo)}.`);
    cerrarModal();
    cobrar(idBoleta);
  }
  verCaja();
}

async function verBoleta(idBoleta, idAtencion) {
  if (!idAtencion) return avisar("No se encontró la boleta.", "error");
  await verDetalleAtencion(idAtencion, idBoleta);
}

async function verDetalleAtencion(idAtencion, idBoleta) {
  const d = await intentar(() => GET(`/api/atenciones/${idAtencion}`));
  if (!d) return;
  const c = d.cabecera;
  const filasServicios = d.servicios.map(s => `<tr><td>${esc(s.Nom_serv)}</td><td>${s.Cant_Aten}</td>
      <td>${money(s.Precio_Servicio)}</td><td>${money(s.Subt_Aten)}</td></tr>`).join("");
  const filasMedicamentos = d.medicamentos.map(m => `<tr><td>${esc(m.Nom_Med)}</td><td>${m.Cant_Med}</td>
      <td>${money(m.Precio_Med)}</td><td>${money(m.Subt_Med)}</td></tr>`).join("");
  const filasPagos = d.pagos.map(p => `<tr><td>${p.Id_Pago}</td><td>${badgeTipo(p.Tipo_Pago)}</td>
      <td>${money(p.Monto)}</td><td>${fechaBonita(p.Fe_Pago)}</td></tr>`).join("");

  abrirModal(`
    <h2>Comprobante ${c.Id_Boleta ? "de la boleta N.º " + c.Id_Boleta : "de consumo (sin boleta)"}</h2>
    <p class="hint">Atención N.º ${c.Id_Atencion} · ${fechaBonita(c.Fe_Atencion)} · ${esc(c.Podologo)}</p>
    <table>
      <tr><th>Paciente</th><td>${esc(c.Cliente)}</td><th>DNI</th><td>${esc(c.Dni_Cliente || "—")}</td></tr>
      <tr><th>Diagnóstico</th><td colspan="3">${esc(c.Diag || "—")}</td></tr>
      <tr><th>Tratamiento</th><td colspan="3">${esc(c.Trat || "—")}</td></tr>
    </table>
    <h3>Servicios</h3>
    ${filasServicios ? `<table><thead><tr><th>Servicio</th><th>Cant.</th><th>Precio</th><th>Subtotal</th></tr></thead><tbody>${filasServicios}</tbody></table>` : '<p class="muted">Sin servicios.</p>'}
    <h3>Medicamentos</h3>
    ${filasMedicamentos ? `<table><thead><tr><th>Medicamento</th><th>Cant.</th><th>Precio</th><th>Subtotal</th></tr></thead><tbody>${filasMedicamentos}</tbody></table>` : '<p class="muted">Sin medicamentos.</p>'}
    <h3>Pagos</h3>
    ${filasPagos ? `<table><thead><tr><th>N.º</th><th>Tipo</th><th>Monto</th><th>Fecha</th></tr></thead><tbody>${filasPagos}</tbody></table>` : '<p class="muted">Sin pagos.</p>'}
    <div class="actions">
      <span class="total-linea">Total: ${money(d.totales.total)}</span>
      ${c.Id_Boleta ? badgePago(c.Estado_Pago) : ""}
      <button class="btn btn-ghost" onclick="window.print()">Imprimir</button>
    </div>
  `);
}

async function anularBoleta(idBoleta) {
  if (!confirm(`¿Anular la boleta N.º ${idBoleta}?`)) return;
  const r = await intentar(() => DEL(`/api/boletas/${idBoleta}`), "Boleta anulada.");
  if (r) verCaja();
}

registrar("caja", verCaja);

export { verCaja, verBoletas, emitirBoleta, cobrar, registrarPago, verBoleta, verDetalleAtencion, anularBoleta };
