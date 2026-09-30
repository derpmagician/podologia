/* ============================= MEDICAMENTOS ============================= */
/* El stock se descuenta al agregarlo a una atención y se devuelve al        */
/* quitarlo (ver vistas/atenciones.js).                                     */

import { DEL, GET, POST, intentar } from "../api.js";
import { $, avisar, esc, fechaBonita, limpiar, money, numero, tablaHtml, texto } from "../ui.js";
import { registrar } from "../navegacion.js";
import { recargarCatalogos } from "../catalogos.js";

let medicamentosEnMemoria = [];

async function verMedicamentos() {
  const lista = await GET("/api/medicamentos");
  medicamentosEnMemoria = lista;
  $("med-tabla").innerHTML = tablaHtml(
    ["Medicamento", "Stock", "Precio", "Vence", "Estado", "Usos", ""],
    lista.map(m => {
      let estado = '<span class="badge b-ok">Vigente</span>';
      if (m.Dias_Vencer != null && m.Dias_Vencer < 0) estado = '<span class="badge b-danger">Vencido</span>';
      else if (m.Dias_Vencer != null && m.Dias_Vencer <= 30) estado = `<span class="badge b-pendiente">Vence en ${m.Dias_Vencer} días</span>`;
      const stock = m.Stock_Med < 5 ? `<span class="badge b-pendiente">${m.Stock_Med}</span>` : m.Stock_Med;
      return `<tr>
        <td>${esc(m.Nom_Med)}</td>
        <td>${stock}</td>
        <td>${money(m.Precio_Med)}</td>
        <td>${fechaBonita(m.Fe_Venc_Med)}</td>
        <td>${estado}</td>
        <td>${m.Usos}</td>
        <td class="acciones">
          <button class="btn btn-ghost btn-sm" onclick="app.moverStock(${m.Id_Medicamento},1)">+ Ingreso</button>
          <button class="btn btn-ghost btn-sm" onclick="app.moverStock(${m.Id_Medicamento},-1)">− Salida</button>
          <button class="btn btn-ghost btn-sm" onclick="app.editarMedicamento(${m.Id_Medicamento})">Editar</button>
          <button class="btn btn-danger btn-sm" onclick="app.eliminarMedicamento(${m.Id_Medicamento})">Eliminar</button>
        </td>
      </tr>`;
    }),
    "No hay medicamentos registrados."
  );
}

async function guardarMedicamento() {
  const id = Number($("med-id").value || 0);
  const cuerpo = {
    Id_Medicamento: id || undefined,
    Nom_Med: texto("med-nombre"),
    Stock_Med: numero("med-stock"),
    Precio_Med: numero("med-precio"),
    Fe_Venc_Med: texto("med-vence")
  };
  if (!cuerpo.Nom_Med) return avisar("Indique el nombre del medicamento.", "error");
  const r = await intentar(() => POST("/api/medicamentos", cuerpo), id ? "Medicamento actualizado." : "Medicamento registrado.");
  if (r) { limpiarMedicamento(); await recargarCatalogos(); verMedicamentos(); }
}

function editarMedicamento(id) {
  const m = medicamentosEnMemoria.find(x => x.Id_Medicamento === id);
  if (!m) return;
  $("med-titulo").textContent = `Editando ${m.Nom_Med}`;
  $("med-id").value = m.Id_Medicamento;
  $("med-nombre").value = m.Nom_Med || "";
  $("med-stock").value = m.Stock_Med;
  $("med-precio").value = m.Precio_Med;
  $("med-vence").value = m.Fe_Venc_Med ? String(m.Fe_Venc_Med).slice(0, 10) : "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarMedicamento() {
  limpiar(["med-id", "med-nombre", "med-stock", "med-precio", "med-vence"]);
  $("med-titulo").textContent = "Registrar medicamento";
}

async function moverStock(id, signo) {
  const cantidad = prompt(signo > 0 ? "¿Cuántas unidades ingresan?" : "¿Cuántas unidades salen?", "1");
  if (cantidad === null) return;
  const n = Number(cantidad);
  if (!(n > 0)) return avisar("Indique una cantidad mayor que cero.", "error");
  const r = await intentar(() => POST(`/api/medicamentos/${id}/stock`, { Cantidad: signo * n }),
    signo > 0 ? "Stock incrementado." : "Stock retirado.");
  if (r) { await recargarCatalogos(); verMedicamentos(); }
}

async function eliminarMedicamento(id) {
  if (!confirm("¿Eliminar este medicamento? Solo si nunca se usó en una atención.")) return;
  const r = await intentar(() => DEL(`/api/medicamentos/${id}`), "Medicamento eliminado.");
  if (r) { await recargarCatalogos(); verMedicamentos(); }
}

registrar("medicamentos", verMedicamentos);

export { verMedicamentos, guardarMedicamento, editarMedicamento, limpiarMedicamento, moverStock, eliminarMedicamento };
