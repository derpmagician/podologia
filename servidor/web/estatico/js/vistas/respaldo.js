/* ========================= COPIA DE SEGURIDAD ========================== */
/* Exporta e importa en JSON y Excel. La importación solo agrega y          */
/* actualiza: nunca borra.                                                  */

import { GET } from "../api.js";
import { $, avisar, esc, tablaHtml } from "../ui.js";
import { registrar } from "../navegacion.js";

async function verRespaldo() {
  const d = await GET("/api/respaldo");
  $("res-tablas").innerHTML = tablaHtml(
    ["Tabla", "Contenido", "Registros"],
    d.tablas.map(t => `<tr>
      <td><strong>${esc(t.tabla)}</strong></td>
      <td>${esc(t.etiqueta)}</td>
      <td>${t.filas}</td>
    </tr>`),
    "No se pudieron leer las tablas."
  );
}

async function importarRespaldo(formato) {
  const entrada = $("res-archivo-" + formato);
  const archivo = entrada.files[0];
  if (!archivo) {
    return avisar(formato === "excel" ? "Seleccione el archivo Excel (.xlsx)."
                                      : "Seleccione el archivo JSON.", "error");
  }
  const confirmar = confirm(
    `¿Importar "${archivo.name}"?\n\n` +
    "Se agregará lo que falte y se actualizará lo que coincida por su clave natural.\n" +
    "No se borra ningún registro.");
  if (!confirmar) return;

  $("res-resultado").innerHTML = '<div class="aviso aviso-info">Importando… no cierre la página.</div>';
  try {
    const respuesta = await fetch("/api/respaldo/" + formato, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": archivo.type || "application/octet-stream" },
      body: archivo
    });
    const datos = await respuesta.json().catch(() => ({}));
    if (respuesta.status === 401) { location.href = "/login.html"; return; }
    if (!respuesta.ok) {
      $("res-resultado").innerHTML =
        `<div class="aviso aviso-error">${esc(datos.error || "No se pudo importar el archivo.")}</div>`;
      return;
    }
    entrada.value = "";
    pintarResultadoImportacion(datos);
    await verRespaldo();
  } catch (error) {
    $("res-resultado").innerHTML = `<div class="aviso aviso-error">${esc(error.message)}</div>`;
  }
}

function pintarResultadoImportacion(r) {
  const porTabla = grupo => {
    const entradas = Object.entries(grupo || {});
    if (!entradas.length) return '<p class="muted">Ninguno.</p>';
    return `<table><thead><tr><th>Tabla</th><th>Registros</th></tr></thead><tbody>
      ${entradas.map(([tabla, n]) => `<tr><td>${esc(tabla)}</td><td>${n}</td></tr>`).join("")}
    </tbody></table>`;
  };
  const omitidos = Object.keys(r.omitidos || {}).length
    ? `<h3>Omitidos</h3>${porTabla(r.omitidos)}` : "";
  const avisos = (r.avisos || []).length
    ? `<h3>Avisos</h3><ul class="lista-avisos">${r.avisos.map(a => `<li>${esc(a)}</li>`).join("")}</ul>` : "";

  $("res-resultado").innerHTML = `
    <div class="aviso aviso-ok">
      Importación terminada: ${r.total_insertados} registro(s) nuevo(s) y
      ${r.total_actualizados} actualizado(s).
    </div>
    <div class="grid-cards">
      <div class="kpi"><div class="label">Nuevos</div><div class="value">${r.total_insertados}</div></div>
      <div class="kpi"><div class="label">Actualizados</div><div class="value">${r.total_actualizados}</div></div>
      <div class="kpi"><div class="label">Omitidos</div><div class="value">${r.total_omitidos}</div></div>
    </div>
    <h3>Registros nuevos</h3>${porTabla(r.insertados)}
    <h3>Registros actualizados</h3>${porTabla(r.actualizados)}
    ${omitidos}
    ${avisos}`;
}

registrar("respaldo", verRespaldo);

export { verRespaldo, importarRespaldo };
