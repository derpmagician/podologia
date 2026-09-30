CLÍNICA PODOLÓGICA — SISTEMA WEB CON LOGIN Y ROLES
===================================================

Versión web del proyecto "Diseño e Implementación de un Programa de
Formación en Podología Clínica". Trabaja sobre la base de datos SQL Server
SQLData_ClinicaPodologicaV2 (script servidor/sql/00_esquema.sql) y agrega el
control de acceso por roles que pide la política de seguridad del informe.


ESTRUCTURA DEL PROYECTO
-----------------------
En la raíz solo queda la pantalla principal; todo lo demás vive en servidor/.

    index.html              Pantalla principal (única cosa en la raíz).

    servidor/
      main.py               Punto de entrada: python servidor/main.py
      config.py             Rutas, puerto y constantes del sistema.
      arranque.py           Prepara la base, carga el ejemplo y la reinicia.

      nucleo/               Lo que comparten todas las capas.
        errores.py          ErrorApi y fallo().
        utilidades.py       Validación y formato de datos.
        seguridad.py        Contraseñas (PBKDF2) y sesiones.
        permisos.py         Roles y módulos de la interfaz (regla R3).
        auditoria.py        Registro de auditoría.
        serializacion.py    Conversión de tipos a JSON.

      datos/                Acceso a SQL Server.
        conexion.py         Cadena de conexión, consultas y transacciones.

      dominio/              Reglas del negocio, sin nada de HTTP.
        citas.py            R1: sin choques de horario por podólogo.
        atenciones.py       Totales y bloqueo de atención facturada (R4).
        facturacion.py      R2 (pagos), R4 (boletas) y R5 (referencialidad).

      api/                  Capa de presentación.
        servidor.py         Servidor HTTP y archivos estáticos.
        enrutador.py        Registro de rutas y objetos Peticion/Descarga.
        rutas/              Un archivo por módulo funcional:
          sesion.py         Login, logout y sesión.
          catalogos.py      Selectores de la interfaz.
          clientes.py       Clientes.
          personal.py       Podólogos y recepcionistas.
          servicios.py      Catálogo de servicios.
          medicamentos.py   Inventario y stock.
          usuarios.py       Usuarios y roles.
          citas.py          Agenda.
          atenciones.py     Atención clínica y consumos.
          boletas.py        Caja, boletas y pagos.
          reportes.py       Resumen, seguimiento y auditoría.
          respaldo.py       Exportar e importar.

      respaldos.py          Motor de exportación/importación (JSON y Excel).

      web/                  Interfaz.
        login.html          Pantalla de ingreso.
        estatico/css/       estilos.css
        estatico/js/        api.js, ui.js, estado.js, navegacion.js,
                            catalogos.js, app.js, login.js
        estatico/js/vistas/ Una vista por módulo (resumen.js, citas.js, ...).

      sql/                  Scripts de base de datos, en orden.
        00_esquema.sql      Las 11 tablas del modelo físico.
        01_usuarios_auditoria.sql
                            USUARIO, AUDITORIA, índice único de R1 y trigger
                            de R4.
        02_datos_demo.sql   El ejemplo completo (clientes, personal, servicios,
                            medicamentos, citas, atenciones, boletas, pagos y
                            los 3 usuarios).

Por qué está ordenado así: las rutas (api/rutas/) reciben la petición,
validan la entrada y responden. La mayoría contiene su propio SQL y consulta
con datos/ directamente; solo las operaciones con reglas de negocio (citas,
atenciones y boletas) pasan por dominio/. Cambiar una de esas reglas es
tocar un solo archivo de dominio/, no varios endpoints.

nucleo/ lo comparten todas las capas, con una excepción hacia abajo:
nucleo/auditoria.py escribe en la base usando datos/.


REQUISITOS
----------
1. Python 3.8 o superior  (probado con 3.12).
2. Los conectores de base de datos y de Excel:

       python -m pip install pyodbc openpyxl

3. SQL Server en ejecución. La base SQLData_ClinicaPodologicaV2 NO hace falta
   crearla a mano: el sistema la crea sola la primera vez que arranca, con
   las 11 tablas del modelo físico. Si prefiere crearla usted con SQL, vea
   "Llenar la base solo con SQL" más abajo.
4. El driver "ODBC Driver 17 for SQL Server" instalado.
   Si usa otro, indíquelo con la variable POD_DRIVER.

La conexión usa autenticación de Windows (Trusted_Connection). Si necesita
usuario y contraseña de SQL Server, defina las variables POD_USUARIO y POD_CLAVE.


CÓMO EJECUTARLO
---------------
En una computadora nueva basta con tener Python, los conectores, SQL Server
en ejecución y el driver ODBC: el sistema crea la base la primera vez.

Por primera vez, cargue los datos de ejemplo y los usuarios de los tres roles:

       cd [ruta_raiz]
       python servidor/main.py --demo

Si la base todavía no existe, este comando la crea con las 11 tablas del
modelo físico y luego carga el ejemplo. Si ya existe, solo agrega lo que
falte. En ambos casos termina y sale: no arranca el servidor.

El ejemplo deja el sistema listo para mostrar: 4 pacientes, 2 podólogos, 5
servicios, 5 medicamentos, 5 citas (una de hoy ya atendida y dos programadas),
3 atenciones, una boleta pagada, una boleta con saldo pendiente y una atención
esperando en caja.

Después, para usar el sistema:

       python servidor/main.py

LLENAR LA BASE SOLO CON SQL (sin Python)
----------------------------------------
Alternativa manual, por si prefiere no usar Python para esto. Los scripts de
servidor/sql se ejecutan por separado y en este orden:

       sqlcmd -S localhost -E -i servidor\sql\00_esquema.sql
       sqlcmd -S localhost -E -i servidor\sql\01_usuarios_auditoria.sql
       sqlcmd -S localhost -E -i servidor\sql\02_datos_demo.sql

Desde SQL Server Management Studio: abra cada archivo y pulse Ejecutar (F5).

El primero crea la base y las 11 tablas, y se ejecuta UNA sola vez: si la base
ya existe dará error, lo cual es normal. No fija rutas absolutas: le pregunta
a SQL Server cuál es su carpeta de datos por defecto, así que sirve en
cualquier computadora sin editarlo. Los otros dos son idempotentes (se pueden
correr las veces que haga falta, no duplican registros) y el último calcula
las fechas con GETDATE(), así que la agenda siempre queda actualizada: una
cita de hoy, dos ya atendidas y dos por venir.

Para saber en qué carpeta quedaron los archivos .mdf y .ldf:

       sqlcmd -S localhost -E -Q "SELECT physical_name FROM sys.master_files WHERE database_id = DB_ID('SQLData_ClinicaPodologicaV2')"

Si quiere volver a empezar de cero antes de presentar:

       python servidor/main.py --reiniciar   (pide confirmación escribiendo SI)

Después, cada vez que quiera usar el sistema:

       python servidor/main.py

y abra en el navegador:

       http://127.0.0.1:8766

Para detenerlo: Ctrl + C en la terminal.

IMPORTANTE: abra siempre la dirección http://127.0.0.1:8766. Si hace doble
clic en el archivo index.html, el navegador no podrá conectarse a la base
de datos y volverá a la pantalla de ingreso.

Al arrancar, el sistema ejecuta servidor/sql/01_usuarios_auditoria.sql
(es idempotente, se puede correr las veces que haga falta) y, si la tabla
USUARIO está vacía, crea el administrador inicial.


USUARIOS
--------
Los que trae --demo (cámbielos antes de presentar):

       admin       / admin123        Administrador
       recepcion   / recepcion123    Recepcionista (counter)
       podologo    / podologo123     Podólogo

Si ejecuta el sistema sin --demo, el único usuario es:

       admin       / admin123        Administrador

Las contraseñas no se guardan en texto plano: se guarda un hash PBKDF2-SHA256
con sal aleatoria por usuario.


QUÉ VE CADA ROL  (regla R3)
---------------------------
Módulo              Administrador   Recepcionista   Podólogo
Resumen                   sí             sí            sí
Citas                     sí             sí        solo las suyas
Atención                  sí             no            sí
Caja y boletas            sí             sí            no
Clientes                  sí             sí            no
Seguimiento (CRM)         sí             sí            no
Servicios                 sí             no            no
Medicamentos              sí             no            no
Personal                  sí             no            no
Usuarios y roles          sí             no            no
Auditoría                 sí             no            no
Copia de seguridad        sí             no            no

La tabla describe las pestañas que ve cada rol en la interfaz. En la API los
permisos se validan en el servidor (api/servidor.py): si alguien llama a una
ruta que no le corresponde, la API responde 403 y deja constancia en la
auditoría con la acción LOGIN_FALLIDO sobre la tabla API. Las lecturas de
catálogos (clientes, servicios, medicamentos, atenciones) están abiertas a
todos los roles autenticados; las restricciones por rol aplican sobre todo a
las escrituras.


EL FLUJO DE ATENCIÓN
--------------------
1. Recepcionista — Clientes: registra al paciente (DNI de 8 dígitos, único).
2. Recepcionista — Citas: agenda la cita eligiendo podólogo, fecha y hora.
   La regla R1 impide dos citas del mismo podólogo a la misma hora.
3. Podólogo — Atención: abre la cita, escribe diagnóstico, tratamiento y
   observaciones, y agrega los servicios y medicamentos entregados.
   El stock de medicamentos se descuenta al agregarlo y se devuelve si se quita.
4. Recepcionista — Caja: ve la atención con el monto ya calculado, genera la
   boleta y registra el pago (Efectivo, Tarjeta, Yape o Transferencia).
5. Administrador — Resumen, Seguimiento y Auditoría: revisa ingresos, pacientes
   que no vuelven hace 30 días y todo lo que pasó en el sistema.


REGLAS DEL NEGOCIO Y DÓNDE ESTÁN
--------------------------------
R1  Un podólogo no puede tener dos citas activas a la misma fecha y hora.
    -> servidor/dominio/citas.py + índice único UX_CITA_Podologo_Fecha_Hora.

R2  Los pagos de una boleta no pueden superar su importe. La boleta pasa a
    "Pagada" solo cuando la suma de pagos iguala el importe.
    -> servidor/dominio/facturacion.py, dentro de la transacción (UPDLOCK).

R3  Solo el Administrador ve auditoría, usuarios y copias de seguridad. Las
    escrituras se restringen por rol; las lecturas de catálogos están
    abiertas a todos los roles autenticados (el podólogo puede leer
    clientes, servicios y medicamentos; la recepcionista puede leer
    atenciones y también eliminar citas).
    -> Cada ruta declara sus roles en el decorador @ruta con las tuplas de
       servidor/nucleo/permisos.py, y es servidor/api/servidor.py quien
       responde 403 cuando el rol no alcanza.

R4  Una boleta pagada y cerrada no se modifica ni se elimina.
    -> servidor/dominio/facturacion.py + trigger TR_BOLETA_NoEliminarPagada.

R5  No se emite boleta si no existe una atención con su cliente registrado.
    -> servidor/dominio/facturacion.py: la boleta se crea desde la atención y
       el cliente sale de la cita.

Además, una atención ya facturada queda bloqueada para el podólogo, y el
importe de la boleta siempre se calcula sumando los detalles de servicios y
medicamentos (nunca se digita a mano).


AUDITORÍA
---------
La tabla AUDITORIA guarda: LOGIN, LOGIN_FALLIDO, LOGOUT, INSERT, UPDATE,
DELETE, COBRO, EXPORTAR e IMPORTAR, con fecha y hora, usuario, rol, tabla,
registro afectado, detalle y equipo. El módulo "Auditoría" (solo
Administrador) permite filtrar por acción, usuario y rango de fechas.


COPIA DE SEGURIDAD: EXPORTAR E IMPORTAR
---------------------------------------
El módulo "Copia de seguridad" (solo Administrador) permite descargar y
cargar toda la información en dos formatos:

  Excel (.xlsx)  Cada hoja del libro es una tabla y lleva el nombre exacto de
                 la tabla (CLIENTE, PODOLOGO, CITA, ...). La PRIMERA HOJA se
                 llama INSTRUCCIONES y explica el formato, el orden de las
                 hojas y todas las restricciones y reglas del negocio.

  JSON (.json)   El mismo contenido en texto, para reimportarlo tal cual o
                 procesarlo con otro programa.

Al importar, el sistema:
  - AGREGA los registros que no existen y ACTUALIZA los que ya existen,
    reconociéndolos por su clave natural (DNI del cliente, correo del
    podólogo, nombre del servicio o medicamento).
  - NUNCA borra nada. Se puede importar el mismo archivo varias veces sin
    duplicar registros.
  - Reengancha solo las tablas hijas: el Id de cada cita, atención, boleta o
    pago del archivo se traduce al Id que le toca en esta base.
  - Respeta las reglas: no toca una boleta pagada (R4) ni una atención ya
    facturada, y recalcula el estado de pago según los pagos (R2). Estas
    comprobaciones están reimplementadas dentro de respaldos.py (no importa
    dominio/), para que la importación sea autocontenida.
  - Ignora las hojas USUARIO y AUDITORIA. Las contraseñas no se exportan
    nunca; los usuarios se crean en el módulo "Usuarios y roles".

Sirve tanto para respaldar como para restaurar: exporte el Excel, y si algún
día la base queda vacía, impórtelo y todo vuelve con sus relaciones.

Para editar el Excel a mano: mantenga el nombre de las hojas y la primera
fila con los nombres de las columnas. Puede reordenar columnas, dejar celdas
vacías y agregar filas nuevas; las columnas que no incluya se dejan como
están.


DÓNDE ESTÁ LA INFORMACIÓN
-------------------------
Todo queda en SQL Server, base SQLData_ClinicaPodologicaV2.
Puede verla con SQL Server Management Studio o con sqlcmd:

       sqlcmd -S localhost -E -d SQLData_ClinicaPodologicaV2 -Q "SELECT * FROM CLIENTE"

Como respaldo, use el plan de copias de seguridad de SQL Server (archivos .bak)
descrito en el informe del proyecto.


CONFIGURACIÓN OPCIONAL (variables de entorno)
---------------------------------------------
POD_SERVIDOR   servidor de SQL Server        (por defecto localhost)
POD_BASE       nombre de la base de datos    (SQLData_ClinicaPodologicaV2)
POD_DRIVER     driver ODBC                   (ODBC Driver 17 for SQL Server)
POD_PUERTO     puerto del servidor web       (8766)
POD_USUARIO    usuario de SQL Server         (si no usa autenticación Windows)
POD_CLAVE      contraseña de SQL Server

Las variables de conexión (POD_SERVIDOR, POD_BASE, POD_DRIVER, POD_USUARIO y
POD_CLAVE) las lee datos/conexion.py directamente al importarse. El módulo
config.py concentra las rutas de archivos, el puerto y las constantes.


SI ALGO FALLA
-------------
"No se pudo conectar con la base de datos" al ingresar
    -> SQL Server no está corriendo, o la base no existe, o falta el driver.
       Pruebe:  sqlcmd -S localhost -E -Q "SELECT name FROM sys.databases"

"Data source name not found" / "No se encuentra el nombre del origen de datos"
    -> Falta el driver ODBC. Instale "Microsoft ODBC Driver 17 for SQL Server"
       o indique el que tenga con la variable POD_DRIVER.

"Falta el conector pyodbc"
    -> Ejecute:  python -m pip install pyodbc

"Falta el conector openpyxl"
    -> Ejecute:  python -m pip install openpyxl

"El puerto ya está en uso"
    -> Otro programa usa el 8766. Use:  python servidor/main.py --puerto 9000

"ModuleNotFoundError" al arrancar
    -> Ejecute siempre desde la raíz del proyecto y con la ruta completa:
       python servidor/main.py

Olvidó la contraseña del administrador
    -> Detenga el servidor, abra SQL Server y ejecute:
       DELETE FROM USUARIO WHERE Usuario = 'admin';
       Al volver a arrancar el sistema se crea de nuevo con admin123.

Vuelve siempre a la pantalla de ingreso
    -> Está abriendo el archivo con doble clic. Use http://127.0.0.1:8766


NOTA SOBRE EL MODELO DE DATOS
-----------------------------
Las 11 tablas del informe (CLIENTE, PODOLOGO, RECEPCIONISTA, CITA, ATENCION,
SERVICIO, MEDICAMENTO, DETALLE_ATENCION, DETALLE_MEDICAMENTO, BOLETA y PAGO)
quedan tal como están en servidor/sql/00_esquema.sql, sin modificaciones.

El script servidor/sql/01_usuarios_auditoria.sql agrega únicamente lo que el
informe pide en la sección "Políticas de seguridad de usuario" y que no estaba
en el modelo físico: las credenciales (USUARIO), los logs (AUDITORIA) y las
restricciones de las reglas R1 y R4 a nivel de motor.
