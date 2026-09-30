/* ==========================================================================
   Navegación: pestañas, usuario en pantalla y cambio de módulo.

   Cada vista se registra con registrar(id, funcion) al cargarse, así que
   navegación no necesita conocer a ninguna de ellas.
   ========================================================================== */

import { MODULOS, sesion, rolClase } from "./estado.js";
import { $, esc, avisar } from "./ui.js";

const RENDER = {};

export function registrar(id, funcion) {
  RENDER[id] = funcion;
}

export function pintarUsuario() {
  const titulo = { Administrador: "Administrador", Recepcionista: "Recepcionista (counter)", Podologo: "Podólogo" }[sesion.rol];
  $("chip-usuario").innerHTML = `${esc(sesion.nombres)} <span class="rol ${rolClase()}">${esc(titulo)}</span>`;
}

export function construirTabs() {
  $("tabs").innerHTML = MODULOS
    .filter(m => sesion.modulos.includes(m.id))
    .map(m => `<button data-tab="${m.id}">${m.titulo}</button>`).join("");
  $("tabs").querySelectorAll("button").forEach(boton => {
    boton.addEventListener("click", () => abrir(boton.dataset.tab));
  });
}

export async function abrir(id) {
  $("tabs").querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.tab === id));
  MODULOS.forEach(m => {
    const seccion = $("tab-" + m.id);
    if (seccion) seccion.classList.toggle("hidden", m.id !== id);
  });
  try {
    await RENDER[id]();
  } catch (error) {
    avisar(error.message, "error");
  }
}
