/* ==========================================================================
   Única puerta de salida hacia la API.

   Todo el front pasa por aquí: así el manejo de la sesión expirada (401) y
   el formato de los errores está en un solo sitio.
   ========================================================================== */

import { avisar } from "./ui.js";

export async function api(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...opciones
  });
  const datos = await respuesta.json().catch(() => ({}));
  if (respuesta.status === 401) {
    location.href = "/login.html";
    throw new Error("sesión expirada");
  }
  if (!respuesta.ok) throw new Error(datos.error || "No se pudo completar la operación.");
  return datos;
}

export const GET = ruta => api(ruta);
export const POST = (ruta, datos) => api(ruta, { method: "POST", body: JSON.stringify(datos || {}) });
export const DEL = ruta => api(ruta, { method: "DELETE" });

export async function intentar(accion, exito) {
  try {
    const resultado = await accion();
    if (exito) avisar(exito);
    return resultado;
  } catch (error) {
    avisar(error.message, "error");
    return null;
  }
}
