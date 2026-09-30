/* ============================== AUDITORÍA =============================== */
/* Regla R3: solo el Administrador ve estos registros.                      */

import { GET } from "../api.js";
import { $, esc, fechaHoraBonita, tablaHtml } from "../ui.js";
import { registrar } from "../navegacion.js";

async function verAuditoria() {
  const parametros = new URLSearchParams();
  if ($("aud-accion").value) parametros.set("accion", $("aud-accion").value);
  if ($("aud-usuario").value.trim()) parametros.set("usuario", $("aud-usuario").value.trim());
  if ($("aud-desde").value) parametros.set("desde", $("aud-desde").value);
  if ($("aud-hasta").value) parametros.set("hasta", $("aud-hasta").value);

  const lista = await GET("/api/auditoria?" + parametros.toString());
  $("aud-tabla").innerHTML = tablaHtml(
    ["Fecha y hora", "Usuario", "Rol", "Acción", "Tabla", "Registro", "Detalle", "Equipo"],
    lista.map(a => {
      const clase = { LOGIN: "b-ok", LOGIN_FALLIDO: "b-danger", LOGOUT: "b-neutral", COBRO: "b-pendiente" }[a.Accion] || "b-neutral";
      return `<tr>
        <td>${fechaHoraBonita(a.Fe_Evento)}</td>
        <td>${esc(a.Usuario || "—")}</td>
        <td>${esc(a.Rol || "—")}</td>
        <td><span class="badge ${clase}">${esc(a.Accion)}</span></td>
        <td>${esc(a.Tabla || "—")}</td>
        <td>${esc(a.Id_Registro || "—")}</td>
        <td>${esc(a.Detalle || "—")}</td>
        <td>${esc(a.Equipo || "—")}</td>
      </tr>`;
    }),
    "No hay eventos con esos filtros."
  );
}

registrar("auditoria", verAuditoria);

export { verAuditoria };
