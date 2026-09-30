/* ==========================================================================
   Estado compartido: sesión abierta, catálogos y módulos del sistema.
   ========================================================================== */

export const MODULOS = [
  { id: "resumen", titulo: "Resumen" },
  { id: "citas", titulo: "Citas" },
  { id: "atencion", titulo: "Atención" },
  { id: "caja", titulo: "Caja y boletas" },
  { id: "clientes", titulo: "Clientes" },
  { id: "seguimiento", titulo: "Seguimiento" },
  { id: "servicios", titulo: "Servicios" },
  { id: "medicamentos", titulo: "Medicamentos" },
  { id: "personal", titulo: "Personal" },
  { id: "usuarios", titulo: "Usuarios y roles" },
  { id: "auditoria", titulo: "Auditoría" },
  { id: "respaldo", titulo: "Copia de seguridad" }
];

export let sesion = null;
export let catalogos = { clientes: [], podologos: [], servicios: [], medicamentos: [] };

export function guardarSesion(valor) { sesion = valor; }
export function guardarCatalogos(valor) { catalogos = valor; }

export const esAdmin = () => sesion.rol === "Administrador";
export const esRecep = () => sesion.rol === "Recepcionista";
export const esPodo = () => sesion.rol === "Podologo";
export const rolClase = () => ({ Administrador: "admin", Recepcionista: "recep", Podologo: "podo" }[sesion.rol] || "");
