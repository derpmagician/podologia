/* ==========================================================================
   Utilidades de interfaz: formato, escapado, tablas, avisos y modales.
   ========================================================================== */

export const $ = id => document.getElementById(id);

export const esc = valor => String(valor ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const money = n => "S/ " + Number(n || 0).toFixed(2);

export const hoy = () => {
  const d = new Date(), p = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

export function fechaBonita(valor) {
  if (!valor) return "—";
  const f = String(valor).slice(0, 10).split("-");
  return f.length === 3 ? `${f[2]}/${f[1]}/${f[0]}` : String(valor);
}

export function fechaHoraBonita(valor) {
  if (!valor) return "—";
  const s = String(valor);
  return s.length > 10 ? `${fechaBonita(s)} ${s.slice(11, 16)}` : fechaBonita(s);
}

export const numero = id => Number($(id).value || 0);
export const texto = id => $(id).value.trim();
export const limpiar = ids => ids.forEach(id => { if ($(id)) $(id).value = ""; });

export const badgeCita = e => {
  const clase = { Programada: "programada", Atendida: "atendida", Cancelada: "cancelada", "No asistio": "noasistio" }[e] || "neutral";
  return `<span class="badge b-${clase}">${esc(e)}</span>`;
};
export const badgePago = e => `<span class="badge ${e === "Pagada" ? "b-pagado" : "b-pendiente"}">${esc(e)}</span>`;
export const badgeTipo = t => `<span class="badge b-${esc((t || "").toLowerCase())}">${esc(t || "—")}</span>`;

export function tablaHtml(cabeceras, filas, mensajeVacio) {
  if (!filas.length) return `<p class="muted">${mensajeVacio || "Sin registros."}</p>`;
  return `<table><thead><tr>${cabeceras.map(c => `<th>${c}</th>`).join("")}</tr></thead>
    <tbody>${filas.join("")}</tbody></table>`;
}

export function opciones(lista, valor, etiqueta, seleccionado) {
  return lista.map(x => {
    const v = String(x[valor]);
    return `<option value="${esc(v)}"${String(seleccionado ?? "") === v ? " selected" : ""}>${esc(x[etiqueta])}</option>`;
  }).join("");
}

let temporizador = null;
export function avisar(mensaje, tipo = "ok") {
  $("mensajes").innerHTML = `<div class="aviso aviso-${tipo === "error" ? "error" : "ok"}">${esc(mensaje)}</div>`;
  clearTimeout(temporizador);
  temporizador = setTimeout(() => { $("mensajes").innerHTML = ""; }, 4500);
}

export function abrirModal(html) {
  $("modal").innerHTML =
    `<div class="modal-fondo" onclick="if(event.target===this) app.cerrarModal()">
       <div class="modal"><button class="cerrar" onclick="app.cerrarModal()">Cerrar</button>${html}</div>
     </div>`;
}

export const cerrarModal = () => { $("modal").innerHTML = ""; };
