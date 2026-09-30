/* =============================== USUARIOS =============================== */
/* Regla R3: solo el Administrador administra usuarios y roles.             */

import { DEL, GET, POST, intentar } from "../api.js";
import { catalogos, sesion } from "../estado.js";
import { $, avisar, esc, fechaBonita, fechaHoraBonita, limpiar, numero, opciones, tablaHtml, texto } from "../ui.js";
import { registrar } from "../navegacion.js";

let usuariosEnMemoria = [];

async function verUsuarios() {
  const lista = await GET("/api/usuarios");
  usuariosEnMemoria = lista;

  $("usu-podologo").innerHTML = opciones(catalogos.podologos, "Id_Podologo", "Nombre", "");
  const recepcionistas = await GET("/api/recepcionistas");
  $("usu-recep").innerHTML = recepcionistas.map(r =>
    `<option value="${r.Id_Recep}">${esc([r.Noms_Recep, r.Apellidos_Recep].filter(Boolean).join(" "))}</option>`).join("");

  $("usu-tabla").innerHTML = tablaHtml(
    ["Usuario", "Nombre", "Rol", "Empleado vinculado", "Estado", "Creado", "Último acceso", ""],
    lista.map(u => `<tr>
      <td><strong>${esc(u.Usuario)}</strong></td>
      <td>${esc(u.Nombres)}</td>
      <td>${esc(u.Rol)}</td>
      <td>${esc((u.Empleado_Podologo || "").trim() || (u.Empleado_Recep || "").trim() || '<span class="muted">acceso total</span>')}</td>
      <td>${u.Activo ? '<span class="badge b-ok">Activo</span>' : '<span class="badge b-danger">Inactivo</span>'}</td>
      <td>${fechaBonita(u.Fe_Alta)}</td>
      <td>${fechaHoraBonita(u.Ultimo_Acceso)}</td>
      <td class="acciones">
        <button class="btn btn-ghost btn-sm" onclick="app.editarUsuario(${u.Id_Usuario})">Editar</button>
        <button class="btn btn-ghost btn-sm" onclick="app.resetClave(${u.Id_Usuario},'${esc(u.Usuario)}')">Contraseña</button>
        ${u.Activo && u.Id_Usuario !== sesion.id
          ? `<button class="btn btn-danger btn-sm" onclick="app.desactivarUsuario(${u.Id_Usuario})">Desactivar</button>` : ""}
      </td>
    </tr>`),
    "No hay usuarios registrados."
  );
}

function cambiarRolFormulario() {
  const rol = $("usu-rol").value;
  $("usu-campo-pod").classList.toggle("hidden", rol !== "Podologo");
  $("usu-campo-rec").classList.toggle("hidden", rol !== "Recepcionista");
}

async function guardarUsuario() {
  const id = Number($("usu-id").value || 0);
  const cuerpo = {
    Id_Usuario: id || undefined,
    Usuario: texto("usu-usuario").toLowerCase(),
    Nombres: texto("usu-nombres"),
    Rol: $("usu-rol").value,
    Id_Podologo: $("usu-rol").value === "Podologo" ? numero("usu-podologo") : null,
    Id_Recep: $("usu-rol").value === "Recepcionista" ? numero("usu-recep") : null,
    Activo: $("usu-activo").value === "1"
  };
  if (!id) cuerpo.Clave = $("usu-clave").value;
  if (!cuerpo.Usuario || !cuerpo.Nombres) return avisar("Complete usuario y nombre completo.", "error");
  if (!id && cuerpo.Clave.length < 6) return avisar("La contraseña debe tener al menos 6 caracteres.", "error");

  const r = await intentar(() => POST("/api/usuarios", cuerpo), id ? "Usuario actualizado." : "Usuario creado.");
  if (r) { limpiarUsuario(); verUsuarios(); }
}

function editarUsuario(id) {
  const u = usuariosEnMemoria.find(x => x.Id_Usuario === id);
  if (!u) return;
  $("usu-titulo").textContent = `Editando el usuario ${u.Usuario}`;
  $("usu-id").value = u.Id_Usuario;
  $("usu-usuario").value = u.Usuario;
  $("usu-nombres").value = u.Nombres || "";
  $("usu-rol").value = u.Rol;
  $("usu-activo").value = u.Activo ? "1" : "0";
  $("usu-campo-clave").classList.add("hidden");
  cambiarRolFormulario();
  if (u.Id_Podologo) $("usu-podologo").value = u.Id_Podologo;
  if (u.Id_Recep) $("usu-recep").value = u.Id_Recep;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function limpiarUsuario() {
  limpiar(["usu-id", "usu-usuario", "usu-nombres", "usu-clave"]);
  $("usu-titulo").textContent = "Crear usuario del sistema";
  $("usu-rol").value = "Administrador";
  $("usu-activo").value = "1";
  $("usu-campo-clave").classList.remove("hidden");
  cambiarRolFormulario();
}

async function resetClave(id, usuario) {
  const clave = prompt(`Nueva contraseña para "${usuario}" (mínimo 6 caracteres):`);
  if (clave === null) return;
  if (clave.length < 6) return avisar("La contraseña debe tener al menos 6 caracteres.", "error");
  const r = await intentar(() => POST(`/api/usuarios/${id}/clave`, { Clave: clave }), "Contraseña actualizada.");
  if (r) verUsuarios();
}

async function desactivarUsuario(id) {
  if (!confirm("¿Desactivar este usuario? No podrá ingresar al sistema.")) return;
  const r = await intentar(() => DEL(`/api/usuarios/${id}`), "Usuario desactivado.");
  if (r) verUsuarios();
}

registrar("usuarios", verUsuarios);

export { verUsuarios, cambiarRolFormulario, guardarUsuario, editarUsuario, limpiarUsuario, resetClave, desactivarUsuario };
