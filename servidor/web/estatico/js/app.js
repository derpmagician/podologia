/* ==========================================================================
   Clínica Podológica — arranque de la interfaz.

   Este archivo solo orquesta: carga las vistas, abre la sesión y expone en
   window.app las funciones que llaman los onclick del HTML.
   ========================================================================== */

import { GET, POST } from "./api.js";
import { esPodo, guardarSesion } from "./estado.js";
import { $, avisar, cerrarModal } from "./ui.js";
import { abrir, construirTabs, pintarUsuario } from "./navegacion.js";
import { recargarCatalogos } from "./catalogos.js";

import { verResumen } from "./vistas/resumen.js";
import { cambiarEstado, citasDeHoy, editarCita, eliminarCita, guardarCita, irAAtender, limpiarCita, verCitas } from "./vistas/citas.js";
import { abrirAtencion, agregarMedicamento, agregarServicio, buscarAtencionPorId, guardarFicha, quitarMedicamento, quitarServicio } from "./vistas/atenciones.js";
import { anularBoleta, cobrar, emitirBoleta, registrarPago, verBoleta, verBoletas, verDetalleAtencion } from "./vistas/caja.js";
import { editarCliente, eliminarCliente, guardarCliente, limpiarCliente, verClientes } from "./vistas/clientes.js";
import { verSeguimiento } from "./vistas/seguimiento.js";
import { editarServicio, eliminarServicio, guardarServicio, limpiarServicio, verServicios } from "./vistas/servicios.js";
import { editarMedicamento, eliminarMedicamento, guardarMedicamento, limpiarMedicamento, moverStock, verMedicamentos } from "./vistas/medicamentos.js";
import { editarPodologo, editarRecepcionista, eliminarPodologo, eliminarRecepcionista, guardarPodologo, guardarRecepcionista, limpiarPodologo, limpiarRecepcionista, verPersonal } from "./vistas/personal.js";
import { cambiarRolFormulario, desactivarUsuario, editarUsuario, guardarUsuario, limpiarUsuario, resetClave, verUsuarios } from "./vistas/usuarios.js";
import { verAuditoria } from "./vistas/auditoria.js";
import { importarRespaldo, verRespaldo } from "./vistas/respaldo.js";

async function salir() {
  try { await POST("/api/logout"); } catch (error) { /* da igual */ }
  location.href = "/login.html";
}

async function iniciar() {
  guardarSesion(await GET("/api/sesion"));
  pintarUsuario();
  construirTabs();

  // El podólogo no agenda citas: solo ve su agenda y atiende.
  if (esPodo()) {
    $("cit-form-panel").classList.add("hidden");
    $("cit-nota").textContent = "";
  }

  await recargarCatalogos();
  limpiarCita();
  limpiarCliente();
  limpiarServicio();
  limpiarMedicamento();
  limpiarPodologo();
  limpiarRecepcionista();
  limpiarUsuario();

  $("seg-dias").value = 30;
  await abrir("resumen");
}

window.app = {
  // navegación y sesión
  salir, cerrarModal, abrir,
  // citas
  verCitas, citasDeHoy, guardarCita, editarCita, limpiarCita, eliminarCita, cambiarEstado, irAAtender,
  // atención
  abrirAtencion, buscarAtencionPorId, guardarFicha, agregarServicio, quitarServicio,
  agregarMedicamento, quitarMedicamento,
  // caja
  verBoletas, emitirBoleta, cobrar, registrarPago, verBoleta, verDetalleAtencion, anularBoleta,
  // clientes
  verClientes, guardarCliente, editarCliente, limpiarCliente, eliminarCliente,
  // seguimiento
  verSeguimiento,
  // servicios
  verServicios, guardarServicio, editarServicio, limpiarServicio, eliminarServicio,
  // medicamentos
  verMedicamentos, guardarMedicamento, editarMedicamento, limpiarMedicamento, moverStock, eliminarMedicamento,
  // personal
  verPersonal, guardarPodologo, editarPodologo, limpiarPodologo, eliminarPodologo,
  guardarRecepcionista, editarRecepcionista, limpiarRecepcionista, eliminarRecepcionista,
  // usuarios
  verUsuarios, cambiarRolFormulario, guardarUsuario, editarUsuario, limpiarUsuario, resetClave, desactivarUsuario,
  // auditoría
  verAuditoria,
  // copia de seguridad
  verRespaldo, importarRespaldo,
  // la vista de resumen se registra sola en navegacion.js
  verResumen
};

iniciar().catch(error => {
  avisar(error.message || "No se pudo iniciar el sistema.", "error");
});
