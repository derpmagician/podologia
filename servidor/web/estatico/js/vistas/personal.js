/* =============================== PERSONAL =============================== */

import { DEL, GET, POST, intentar } from "../api.js";
import { $, avisar, esc, limpiar, tablaHtml, texto } from "../ui.js";
import { registrar } from "../navegacion.js";
import { recargarCatalogos } from "../catalogos.js";

let podologosEnMemoria = [];
let recepcionistasEnMemoria = [];

async function verPersonal() {
  const [pods, recs] = await Promise.all([GET("/api/podologos"), GET("/api/recepcionistas")]);
  podologosEnMemoria = pods;
  recepcionistasEnMemoria = recs;

  $("pod-tabla").innerHTML = tablaHtml(
    ["Podólogo", "Especialidad", "Teléfono", "Correo", "Citas", ""],
    pods.map(p => `<tr>
      <td>${esc([p.Nom_Podologo, p.Ape_Pat_Podo, p.Ape_Mat_Podo].filter(Boolean).join(" "))}</td>
      <td>${esc(p.Esp_Podo || "—")}</td>
      <td>${esc(p.Tel_Podo || "—")}</td>
      <td>${esc(p.Email_Podo || "—")}</td>
      <td>${p.Citas}</td>
      <td class="acciones">
        <button class="btn btn-ghost btn-sm" onclick="app.editarPodologo(${p.Id_Podologo})">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="app.eliminarPodologo(${p.Id_Podologo})">Eliminar</button>
      </td>
    </tr>`),
    "No hay podólogos registrados."
  );

  $("rec-tabla").innerHTML = tablaHtml(
    ["Recepcionista", "Teléfono", "Citas registradas", ""],
    recs.map(r => `<tr>
      <td>${esc([r.Noms_Recep, r.Apellidos_Recep].filter(Boolean).join(" "))}</td>
      <td>${esc(r.Tel_Recep || "—")}</td>
      <td>${r.Citas}</td>
      <td class="acciones">
        <button class="btn btn-ghost btn-sm" onclick="app.editarRecepcionista(${r.Id_Recep})">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="app.eliminarRecepcionista(${r.Id_Recep})">Eliminar</button>
      </td>
    </tr>`),
    "No hay recepcionistas registrados."
  );
}

async function guardarPodologo() {
  const id = Number($("pod-id").value || 0);
  const cuerpo = {
    Id_Podologo: id || undefined,
    Nom_Podologo: texto("pod-nombres"),
    Ape_Pat_Podo: texto("pod-pat"),
    Ape_Mat_Podo: texto("pod-mat"),
    Esp_Podo: texto("pod-esp"),
    Tel_Podo: texto("pod-tel"),
    Email_Podo: texto("pod-email")
  };
  if (!cuerpo.Nom_Podologo) return avisar("Indique el nombre del podólogo.", "error");
  const r = await intentar(() => POST("/api/podologos", cuerpo), id ? "Podólogo actualizado." : "Podólogo registrado.");
  if (r) { limpiarPodologo(); await recargarCatalogos(); verPersonal(); }
}

function editarPodologo(id) {
  const p = podologosEnMemoria.find(x => x.Id_Podologo === id);
  if (!p) return;
  $("pod-titulo").textContent = `Editando a ${p.Nom_Podologo}`;
  $("pod-id").value = p.Id_Podologo;
  $("pod-nombres").value = p.Nom_Podologo || "";
  $("pod-pat").value = p.Ape_Pat_Podo || "";
  $("pod-mat").value = p.Ape_Mat_Podo || "";
  $("pod-esp").value = p.Esp_Podo || "";
  $("pod-tel").value = p.Tel_Podo || "";
  $("pod-email").value = p.Email_Podo || "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarPodologo() {
  limpiar(["pod-id", "pod-nombres", "pod-pat", "pod-mat", "pod-esp", "pod-tel", "pod-email"]);
  $("pod-titulo").textContent = "Registrar podólogo";
}

async function eliminarPodologo(id) {
  if (!confirm("¿Eliminar este podólogo?")) return;
  const r = await intentar(() => DEL(`/api/podologos/${id}`), "Podólogo eliminado.");
  if (r) { await recargarCatalogos(); verPersonal(); }
}

async function guardarRecepcionista() {
  const id = Number($("rec-id").value || 0);
  const cuerpo = {
    Id_Recep: id || undefined,
    Noms_Recep: texto("rec-nombres"),
    Apellidos_Recep: texto("rec-apellidos"),
    Tel_Recep: texto("rec-tel")
  };
  if (!cuerpo.Noms_Recep) return avisar("Indique los nombres del recepcionista.", "error");
  const r = await intentar(() => POST("/api/recepcionistas", cuerpo), id ? "Recepcionista actualizado." : "Recepcionista registrado.");
  if (r) { limpiarRecepcionista(); await recargarCatalogos(); verPersonal(); }
}

function editarRecepcionista(id) {
  const r = recepcionistasEnMemoria.find(x => x.Id_Recep === id);
  if (!r) return;
  $("rec-titulo").textContent = `Editando a ${r.Noms_Recep}`;
  $("rec-id").value = r.Id_Recep;
  $("rec-nombres").value = r.Noms_Recep || "";
  $("rec-apellidos").value = r.Apellidos_Recep || "";
  $("rec-tel").value = r.Tel_Recep || "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarRecepcionista() {
  limpiar(["rec-id", "rec-nombres", "rec-apellidos", "rec-tel"]);
  $("rec-titulo").textContent = "Registrar recepcionista";
}

async function eliminarRecepcionista(id) {
  if (!confirm("¿Eliminar este recepcionista?")) return;
  const r = await intentar(() => DEL(`/api/recepcionistas/${id}`), "Recepcionista eliminado.");
  if (r) { await recargarCatalogos(); verPersonal(); }
}

registrar("personal", verPersonal);

export {
  verPersonal,
  guardarPodologo, editarPodologo, limpiarPodologo, eliminarPodologo,
  guardarRecepcionista, editarRecepcionista, limpiarRecepcionista, eliminarRecepcionista
};
