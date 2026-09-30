/* Ingreso al sistema — Clínica Podológica */

import { $, esc } from "./ui.js";

function aviso(texto, tipo) {
  $("aviso").innerHTML = texto ? `<div class="aviso aviso-${tipo}">${esc(texto)}</div>` : "";
}

async function entrar(evento) {
  evento.preventDefault();
  const boton = $("entrar");
  boton.disabled = true;
  boton.textContent = "Verificando...";
  aviso("");
  try {
    const r = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario: $("usuario").value.trim(), clave: $("clave").value })
    });
    const datos = await r.json().catch(() => ({}));
    if (!r.ok) {
      aviso(datos.error || "No se pudo ingresar.", "error");
      $("clave").value = "";
      $("clave").focus();
      return;
    }
    location.href = "/index.html";
  } catch (error) {
    aviso("No hay conexión con el servidor. Ejecute: python servidor/main.py", "error");
  } finally {
    boton.disabled = false;
    boton.textContent = "Ingresar";
  }
}

/* Si ya hay una sesión abierta, pasa directo al sistema. */
(async () => {
  try {
    const r = await fetch("/api/sesion");
    if (r.ok) location.href = "/index.html";
  } catch (error) { /* sin servidor: se queda en el formulario */ }
})();

$("formulario").addEventListener("submit", entrar);
