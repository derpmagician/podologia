/* ==========================================================================
   Catálogos que alimentan los selectores de la interfaz.
   ========================================================================== */

import { GET } from "./api.js";
import { guardarCatalogos, catalogos } from "./estado.js";
import { $, opciones } from "./ui.js";

export async function recargarCatalogos() {
  guardarCatalogos(await GET("/api/catalogos"));
  llenarSelectores();
}

export function llenarSelectores() {
  if ($("cit-cliente")) $("cit-cliente").innerHTML = opciones(catalogos.clientes, "Id_Cliente", "Nombre", $("cit-cliente").value);
  if ($("cit-podologo")) $("cit-podologo").innerHTML = opciones(catalogos.podologos, "Id_Podologo", "Nombre", $("cit-podologo").value);
  if ($("cit-fpod")) $("cit-fpod").innerHTML = `<option value="">Todos</option>` + opciones(catalogos.podologos, "Id_Podologo", "Nombre", $("cit-fpod").value);
  if ($("usu-podologo")) $("usu-podologo").innerHTML = opciones(catalogos.podologos, "Id_Podologo", "Nombre", $("usu-podologo").value);
}
