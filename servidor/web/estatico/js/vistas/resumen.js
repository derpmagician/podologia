/* ================================ RESUMEN =============================== */

import { GET } from "../api.js";
import { esAdmin, esPodo } from "../estado.js";
import { $, badgeCita, badgePago, esc, fechaBonita, money, tablaHtml } from "../ui.js";
import { registrar } from "../navegacion.js";

async function verResumen() {
  const d = await GET("/api/resumen");
  const k = d.kpis;

  const tarjetas = [{ label: "Citas de hoy", valor: k.citas_hoy }];
  if (esPodo()) {
    tarjetas.push({ label: "Atenciones del mes", valor: k.atenciones_mes });
    tarjetas.push({ label: "Pendientes de facturar", valor: k.sin_facturar });
  } else {
    tarjetas.push({ label: "Atenciones del mes", valor: k.atenciones_mes });
    tarjetas.push({ label: "Cobrado este mes", valor: money(k.cobrado_mes) });
    tarjetas.push({ label: "Por cobrar", valor: money(k.por_cobrar), alerta: k.por_cobrar > 0 });
    tarjetas.push({ label: "Boletas pendientes", valor: k.boletas_pendientes, alerta: k.boletas_pendientes > 0 });
    tarjetas.push({ label: "Atenciones sin boleta", valor: k.sin_facturar, alerta: k.sin_facturar > 0 });
  }
  tarjetas.push({ label: "Clientes registrados", valor: k.clientes });
  if (esAdmin()) {
    tarjetas.push({ label: "Medicamentos con stock bajo", valor: k.stock_bajo, alerta: k.stock_bajo > 0 });
    tarjetas.push({ label: "Por vencer (30 días)", valor: k.por_vencer, alerta: k.por_vencer > 0 });
  }
  $("res-kpis").innerHTML = tarjetas.map(t =>
    `<div class="kpi${t.alerta ? " alerta" : ""}">
       <div class="label">${t.label}</div><div class="value">${t.valor}</div>
     </div>`).join("");

  $("res-fecha").textContent = new Date().toLocaleDateString("es-PE",
    { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  $("res-agenda").innerHTML = tablaHtml(
    ["Hora", "Cliente", "Podólogo", "Motivo", "Estado"],
    d.agenda_hoy.map(c => `<tr>
      <td>${esc(c.Hora_Cita)}</td>
      <td>${esc(c.Cliente)}</td>
      <td>${esc(c.Podologo)}</td>
      <td>${esc(c.Motivo || "—")}</td>
      <td>${badgeCita(c.Estado)}</td>
    </tr>`),
    "No hay citas agendadas para hoy."
  );

  $("res-ultimas").innerHTML = tablaHtml(
    ["Fecha", "Cliente", "Podólogo", "Diagnóstico", "Total", "Boleta"],
    d.ultimas.map(a => `<tr>
      <td>${fechaBonita(a.Fe_Atencion)}</td>
      <td>${esc(a.Cliente)}</td>
      <td>${esc(a.Podologo)}</td>
      <td>${esc(a.Diag || "—")}</td>
      <td>${money(a.Total)}</td>
      <td>${a.Id_Boleta ? `${badgePago(a.Estado_Pago)} <span class="muted">N.º ${a.Id_Boleta}</span>` : '<span class="badge b-pendiente">Sin facturar</span>'}</td>
    </tr>`),
    "Todavía no hay atenciones registradas."
  );

  $("res-top").innerHTML = tablaHtml(
    ["Servicio", "Veces", "Importe"],
    d.top_servicios.map(s => `<tr>
      <td>${esc(s.Nom_serv)}</td><td>${s.Veces}</td><td>${money(s.Importe)}</td>
    </tr>`),
    "Aún no se registran consumos de servicios."
  );
}

registrar("resumen", verResumen);

export { verResumen };
