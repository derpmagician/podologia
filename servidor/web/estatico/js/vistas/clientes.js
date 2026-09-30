/* =============================== CLIENTES =============================== */

import { DEL, GET, POST, intentar } from "../api.js";
import { esAdmin } from "../estado.js";
import { $, avisar, esc, fechaBonita, limpiar, tablaHtml, texto } from "../ui.js";
import { registrar } from "../navegacion.js";
import { recargarCatalogos } from "../catalogos.js";

let clientesEnMemoria = [];

async function verClientes() {
  const busqueda = $("cli-buscar").value.trim();
  const lista = await GET("/api/clientes" + (busqueda ? "?q=" + encodeURIComponent(busqueda) : ""));
  clientesEnMemoria = lista;
  $("cli-tabla").innerHTML = tablaHtml(
    ["Cliente", "DNI", "Teléfono", "Correo", "Registro", "Citas", "Última atención", ""],
    lista.map(c => `<tr>
      <td>${esc([c.Noms_Cliente, c.Ape_Pat_Cliente, c.Ape_Mat_Cliente].filter(Boolean).join(" "))}</td>
      <td>${esc(c.Dni_Cliente || "—")}</td>
      <td>${esc(c.Tel_Cliente || "—")}</td>
      <td>${esc(c.Email_Cliente || "—")}</td>
      <td>${fechaBonita(c.Fecha_Registro)}</td>
      <td>${c.Citas}</td>
      <td>${fechaBonita(c.Ultima_Atencion)}</td>
      <td class="acciones">
        <button class="btn btn-ghost btn-sm" onclick="app.editarCliente(${c.Id_Cliente})">Editar</button>
        ${esAdmin() ? `<button class="btn btn-danger btn-sm" onclick="app.eliminarCliente(${c.Id_Cliente})">Eliminar</button>` : ""}
      </td>
    </tr>`),
    "No se encontraron clientes."
  );
}

async function guardarCliente() {
  const id = Number($("cli-id").value || 0);
  const cuerpo = {
    Id_Cliente: id || undefined,
    Noms_Cliente: texto("cli-nombres"),
    Ape_Pat_Cliente: texto("cli-pat"),
    Ape_Mat_Cliente: texto("cli-mat"),
    Dni_Cliente: texto("cli-dni"),
    Tel_Cliente: texto("cli-tel"),
    Email_Cliente: texto("cli-email")
  };
  if (!cuerpo.Noms_Cliente) return avisar("Indique los nombres del cliente.", "error");
  const r = await intentar(() => POST("/api/clientes", cuerpo), id ? "Cliente actualizado." : "Cliente registrado.");
  if (r) { limpiarCliente(); await recargarCatalogos(); verClientes(); }
}

function editarCliente(id) {
  const c = clientesEnMemoria.find(x => x.Id_Cliente === id);
  if (!c) return;
  $("cli-titulo").textContent = `Editando a ${c.Noms_Cliente}`;
  $("cli-id").value = c.Id_Cliente;
  $("cli-nombres").value = c.Noms_Cliente || "";
  $("cli-pat").value = c.Ape_Pat_Cliente || "";
  $("cli-mat").value = c.Ape_Mat_Cliente || "";
  $("cli-dni").value = c.Dni_Cliente || "";
  $("cli-tel").value = c.Tel_Cliente || "";
  $("cli-email").value = c.Email_Cliente || "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarCliente() {
  limpiar(["cli-id", "cli-nombres", "cli-pat", "cli-mat", "cli-dni", "cli-tel", "cli-email"]);
  $("cli-titulo").textContent = "Registrar cliente";
}

async function eliminarCliente(id) {
  if (!confirm("¿Eliminar este cliente? Solo es posible si no tiene citas ni historial.")) return;
  const r = await intentar(() => DEL(`/api/clientes/${id}`), "Cliente eliminado.");
  if (r) { await recargarCatalogos(); verClientes(); }
}

registrar("clientes", verClientes);

export { verClientes, guardarCliente, editarCliente, limpiarCliente, eliminarCliente };
