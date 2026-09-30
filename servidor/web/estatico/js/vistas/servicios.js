/* =============================== SERVICIOS ============================== */

import { DEL, GET, POST, intentar } from "../api.js";
import { $, avisar, esc, limpiar, money, numero, tablaHtml, texto } from "../ui.js";
import { registrar } from "../navegacion.js";
import { recargarCatalogos } from "../catalogos.js";

let serviciosEnMemoria = [];

async function verServicios() {
  const lista = await GET("/api/servicios");
  serviciosEnMemoria = lista;
  $("srv-tabla").innerHTML = tablaHtml(
    ["Servicio", "Descripción", "Precio", "Veces usado", ""],
    lista.map(s => `<tr>
      <td>${esc(s.Nom_serv)}</td>
      <td>${esc(s.Descripcion || "—")}</td>
      <td>${money(s.Precio_Servicio)}</td>
      <td>${s.Usos}</td>
      <td class="acciones">
        <button class="btn btn-ghost btn-sm" onclick="app.editarServicio(${s.Id_Servicio})">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="app.eliminarServicio(${s.Id_Servicio})">Eliminar</button>
      </td>
    </tr>`),
    "No hay servicios registrados."
  );
}

async function guardarServicio() {
  const id = Number($("srv-id").value || 0);
  const cuerpo = {
    Id_Servicio: id || undefined,
    Nom_serv: texto("srv-nombre"),
    Descripcion: texto("srv-desc"),
    Precio_Servicio: numero("srv-precio")
  };
  if (!cuerpo.Nom_serv) return avisar("Indique el nombre del servicio.", "error");
  const r = await intentar(() => POST("/api/servicios", cuerpo), id ? "Servicio actualizado." : "Servicio registrado.");
  if (r) { limpiarServicio(); await recargarCatalogos(); verServicios(); }
}

function editarServicio(id) {
  const s = serviciosEnMemoria.find(x => x.Id_Servicio === id);
  if (!s) return;
  $("srv-titulo").textContent = `Editando ${s.Nom_serv}`;
  $("srv-id").value = s.Id_Servicio;
  $("srv-nombre").value = s.Nom_serv || "";
  $("srv-desc").value = s.Descripcion || "";
  $("srv-precio").value = s.Precio_Servicio;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarServicio() {
  limpiar(["srv-id", "srv-nombre", "srv-desc", "srv-precio"]);
  $("srv-titulo").textContent = "Registrar servicio";
}

async function eliminarServicio(id) {
  if (!confirm("¿Eliminar este servicio? Solo si nunca se usó en una atención.")) return;
  const r = await intentar(() => DEL(`/api/servicios/${id}`), "Servicio eliminado.");
  if (r) { await recargarCatalogos(); verServicios(); }
}

registrar("servicios", verServicios);

export { verServicios, guardarServicio, editarServicio, limpiarServicio, eliminarServicio };
