/* ============================= SEGUIMIENTO ============================== */
/* Pacientes que no vuelven hace N días (CRM post-venta).                   */

import { GET } from "../api.js";
import { $, esc, fechaBonita, tablaHtml } from "../ui.js";
import { registrar } from "../navegacion.js";

async function verSeguimiento() {
  const dias = Number($("seg-dias").value || 30);
  const lista = await GET("/api/seguimiento?dias=" + dias);
  $("seg-tabla").innerHTML = tablaHtml(
    ["Cliente", "DNI", "Teléfono", "Correo", "Última atención", "Días sin volver", "Último tratamiento", "Citas futuras"],
    lista.map(c => `<tr>
      <td>${esc(c.Cliente)}</td>
      <td>${esc(c.Dni_Cliente || "—")}</td>
      <td>${esc(c.Tel_Cliente || "—")}</td>
      <td>${esc(c.Email_Cliente || "—")}</td>
      <td>${c.Ultima_Atencion ? fechaBonita(c.Ultima_Atencion) : '<span class="muted">nunca atendido</span>'}</td>
      <td>${c.Dias_Sin_Volver == null ? "—" : `<span class="badge ${c.Dias_Sin_Volver > dias ? "b-pendiente" : "b-neutral"}">${c.Dias_Sin_Volver} días</span>`}</td>
      <td>${esc(c.Ultimo_Tratamiento || "—")}</td>
      <td>${c.Citas_Futuras ? `Sí (${c.Citas_Futuras})` : "No"}</td>
    </tr>`),
    `Ningún paciente lleva ${dias} días o más sin volver.`
  );
}

registrar("seguimiento", verSeguimiento);

export { verSeguimiento };
