/* ============================================================================
   CLINICA PODOLOGICA - CARGA AUTOMATICA DE DATOS
   Base de datos : SQLData_ClinicaPodologicaV2 (SQL Server)
   Archivo       : 02_datos_demo.sql

   Llena TODA la base con un ejemplo coherente y listo para demostrar:
     4 clientes, 2 podologos, 1 recepcionista, 5 servicios, 5 medicamentos,
     5 citas, 3 atenciones con sus consumos, 2 boletas (una pagada y una con
     saldo) y los 3 usuarios del sistema (administrador, recepcionista y
     podologo).

   Es IDEMPOTENTE: cada registro se inserta solo si no existe, asi que puede
   ejecutarlo varias veces sin duplicar nada ni perder datos.

   Como ejecutarlo:
     - SQL Server Management Studio: abra el archivo y pulse Ejecutar (F5).
     - sqlcmd:  sqlcmd -S localhost -E -i sql\02_datos_demo.sql

   Las fechas se calculan con GETDATE(), por lo que la agenda siempre queda
   "fresca": hay una cita de hoy, dos ya atendidas y dos por venir.

   Usuarios que crea:
     admin      / admin123        Administrador
     recepcion  / recepcion123    Recepcionista
     podologo   / podologo123     Podologo
   Las contrasenas no van en texto plano: son hashes PBKDF2-SHA256 con sal
   propia. Para cambiarlas use el modulo "Usuarios y roles" del sistema web.
   ============================================================================ */

USE SQLData_ClinicaPodologicaV2;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* ---------------------------------------------------------------------------
   1. CLIENTES
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM CLIENTE WHERE Dni_Cliente = '45678912')
    INSERT INTO CLIENTE (Noms_Cliente, Ape_Pat_Cliente, Ape_Mat_Cliente, Dni_Cliente,
                         Tel_Cliente, Email_Cliente, Fecha_Registro)
    VALUES ('Ana', 'Torres', 'Vega', '45678912', '987654321', 'ana.torres@correo.com',
            DATEADD(DAY, -120, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM CLIENTE WHERE Dni_Cliente = '41234567')
    INSERT INTO CLIENTE (Noms_Cliente, Ape_Pat_Cliente, Ape_Mat_Cliente, Dni_Cliente,
                         Tel_Cliente, Email_Cliente, Fecha_Registro)
    VALUES ('Luis', 'Ramirez', 'Soto', '41234567', '998877665', 'luis.ramirez@correo.com',
            DATEADD(DAY, -95, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM CLIENTE WHERE Dni_Cliente = '40112233')
    INSERT INTO CLIENTE (Noms_Cliente, Ape_Pat_Cliente, Ape_Mat_Cliente, Dni_Cliente,
                         Tel_Cliente, Email_Cliente, Fecha_Registro)
    VALUES ('Carmen', 'Quispe', 'Huaman', '40112233', '955443322', 'carmen.quispe@correo.com',
            DATEADD(DAY, -60, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM CLIENTE WHERE Dni_Cliente = '43344555')
    INSERT INTO CLIENTE (Noms_Cliente, Ape_Pat_Cliente, Ape_Mat_Cliente, Dni_Cliente,
                         Tel_Cliente, Email_Cliente, Fecha_Registro)
    VALUES ('Jorge', 'Salazar', 'Paredes', '43344555', '911223344', NULL,
            DATEADD(DAY, -20, CAST(GETDATE() AS DATE)));
GO

/* ---------------------------------------------------------------------------
   2. PODOLOGOS Y RECEPCIONISTA
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM PODOLOGO WHERE Email_Podo = 'maria.lopez@clinica.com')
    INSERT INTO PODOLOGO (Nom_Podologo, Ape_Pat_Podo, Ape_Mat_Podo, Esp_Podo, Tel_Podo, Email_Podo)
    VALUES ('Maria', 'Lopez', 'Rios', 'Podologia clinica y pie diabetico', '999111222',
            'maria.lopez@clinica.com');

IF NOT EXISTS (SELECT 1 FROM PODOLOGO WHERE Email_Podo = 'carlos.mendoza@clinica.com')
    INSERT INTO PODOLOGO (Nom_Podologo, Ape_Pat_Podo, Ape_Mat_Podo, Esp_Podo, Tel_Podo, Email_Podo)
    VALUES ('Carlos', 'Mendoza', 'Diaz', 'Podologia estetica', '999333444',
            'carlos.mendoza@clinica.com');

IF NOT EXISTS (SELECT 1 FROM RECEPCIONISTA WHERE Tel_Recep = '988777666')
    INSERT INTO RECEPCIONISTA (Noms_Recep, Apellidos_Recep, Tel_Recep)
    VALUES ('Rosa', 'Nunez Campos', '988777666');
GO

/* ---------------------------------------------------------------------------
   3. SERVICIOS
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM SERVICIO WHERE Nom_serv = 'Consulta podologica')
    INSERT INTO SERVICIO (Nom_serv, Descripcion, Precio_Servicio)
    VALUES ('Consulta podologica', 'Evaluacion inicial del pie', 60.00);

IF NOT EXISTS (SELECT 1 FROM SERVICIO WHERE Nom_serv = 'Quiropodia')
    INSERT INTO SERVICIO (Nom_serv, Descripcion, Precio_Servicio)
    VALUES ('Quiropodia', 'Corte y limado de unas mas hidratacion', 80.00);

IF NOT EXISTS (SELECT 1 FROM SERVICIO WHERE Nom_serv = 'Curacion de una encarnada')
    INSERT INTO SERVICIO (Nom_serv, Descripcion, Precio_Servicio)
    VALUES ('Curacion de una encarnada', 'Manejo de una encarnada', 120.00);

IF NOT EXISTS (SELECT 1 FROM SERVICIO WHERE Nom_serv = 'Tratamiento de callosidades')
    INSERT INTO SERVICIO (Nom_serv, Descripcion, Precio_Servicio)
    VALUES ('Tratamiento de callosidades', 'Remocion de hiperqueratosis', 90.00);

IF NOT EXISTS (SELECT 1 FROM SERVICIO WHERE Nom_serv = 'Evaluacion pie diabetico')
    INSERT INTO SERVICIO (Nom_serv, Descripcion, Precio_Servicio)
    VALUES ('Evaluacion pie diabetico', 'Test de monofilamento y control circulatorio', 150.00);
GO

/* ---------------------------------------------------------------------------
   4. MEDICAMENTOS  (con fechas de vencimiento relativas a hoy)
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM MEDICAMENTO WHERE Nom_Med = 'Crema hidratante ureico')
    INSERT INTO MEDICAMENTO (Nom_Med, Stock_Med, Precio_Med, Fe_Venc_Med)
    VALUES ('Crema hidratante ureico', 20, 35.00, DATEADD(DAY, 180, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM MEDICAMENTO WHERE Nom_Med = 'Antimicotico topical')
    INSERT INTO MEDICAMENTO (Nom_Med, Stock_Med, Precio_Med, Fe_Venc_Med)
    VALUES ('Antimicotico topical', 12, 45.00, DATEADD(DAY, 150, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM MEDICAMENTO WHERE Nom_Med = 'Gasas esteriles')
    INSERT INTO MEDICAMENTO (Nom_Med, Stock_Med, Precio_Med, Fe_Venc_Med)
    VALUES ('Gasas esteriles', 40, 5.00, DATEADD(DAY, 240, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM MEDICAMENTO WHERE Nom_Med = 'Alcohol isopropilico')
    INSERT INTO MEDICAMENTO (Nom_Med, Stock_Med, Precio_Med, Fe_Venc_Med)
    VALUES ('Alcohol isopropilico', 8, 12.00, DATEADD(DAY, 120, CAST(GETDATE() AS DATE)));

IF NOT EXISTS (SELECT 1 FROM MEDICAMENTO WHERE Nom_Med = 'Anestesico local')
    INSERT INTO MEDICAMENTO (Nom_Med, Stock_Med, Precio_Med, Fe_Venc_Med)
    VALUES ('Anestesico local', 4, 55.00, DATEADD(DAY, 45, CAST(GETDATE() AS DATE)));
GO

/* ---------------------------------------------------------------------------
   5. USUARIOS DEL SISTEMA (login y roles)
   ---------------------------------------------------------------------------
   Clave_Hash = pbkdf2$<iteraciones>$<sal_hex>$<hash_hex>
   El vinculo con PODOLOGO / RECEPCIONISTA lo exige la restriccion
   CK_USUARIO_Vinculo: el podologo y el recepcionista se guardan con su
   registro de empleado; el administrador no se vincula a nadie.
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM USUARIO WHERE Usuario = 'admin')
    INSERT INTO USUARIO (Usuario, Clave_Hash, Rol, Nombres)
    VALUES ('admin',
            'pbkdf2$120000$f395851d746c67d63c98d8be1b7e32ae$c826fee4e73bc60a6dfc29ac3c31a7f7384bf78e8cc84e288140adc889d807ee',
            'Administrador', 'Administrador del sistema');

IF NOT EXISTS (SELECT 1 FROM USUARIO WHERE Usuario = 'recepcion')
    INSERT INTO USUARIO (Usuario, Clave_Hash, Rol, Id_Recep, Nombres)
    SELECT 'recepcion',
           'pbkdf2$120000$1efdd1c48302120dab736599519c057e$9b24c4f4f7af4dce77b8bf11e75eb778ac3a2e4b5d05de090dc95101c5d62d29',
           'Recepcionista', r.Id_Recep, 'Rosa Nunez Campos'
    FROM RECEPCIONISTA r
    WHERE r.Tel_Recep = '988777666';

IF NOT EXISTS (SELECT 1 FROM USUARIO WHERE Usuario = 'podologo')
    INSERT INTO USUARIO (Usuario, Clave_Hash, Rol, Id_Podologo, Nombres)
    SELECT 'podologo',
           'pbkdf2$120000$1a584b6f8ddc16e1703c29af182a3870$596a079307f18982fada25c005eeece6aec255aac95d818168c3766b4959d5a5',
           'Podologo', p.Id_Podologo, 'Maria Lopez Rios'
    FROM PODOLOGO p
    WHERE p.Email_Podo = 'maria.lopez@clinica.com';
GO

/* ---------------------------------------------------------------------------
   6. FLUJO DE ATENCION COMPLETO
   ---------------------------------------------------------------------------
   Cita 1  hace 2 dias  -> atendida, con servicio y medicamento, boleta PAGADA
   Cita 2  ayer         -> atendida, con servicio, boleta con PAGO PARCIAL
   Cita 3  hoy          -> atendida, con dos servicios, SIN boleta (esta en caja)
   Cita 4  manana       -> programada
   Cita 5  en 3 dias    -> programada
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM CITA)
BEGIN
    DECLARE @ana    INT = (SELECT Id_Cliente    FROM CLIENTE       WHERE Dni_Cliente  = '45678912');
    DECLARE @luis   INT = (SELECT Id_Cliente    FROM CLIENTE       WHERE Dni_Cliente  = '41234567');
    DECLARE @carmen INT = (SELECT Id_Cliente    FROM CLIENTE       WHERE Dni_Cliente  = '40112233');
    DECLARE @maria  INT = (SELECT Id_Podologo   FROM PODOLOGO      WHERE Email_Podo   = 'maria.lopez@clinica.com');
    DECLARE @carlos INT = (SELECT Id_Podologo   FROM PODOLOGO      WHERE Email_Podo   = 'carlos.mendoza@clinica.com');
    DECLARE @rosa   INT = (SELECT Id_Recep      FROM RECEPCIONISTA WHERE Tel_Recep    = '988777666');

    DECLARE @s_consulta INT = (SELECT Id_Servicio FROM SERVICIO WHERE Nom_serv = 'Consulta podologica');
    DECLARE @s_quiro    INT = (SELECT Id_Servicio FROM SERVICIO WHERE Nom_serv = 'Quiropodia');
    DECLARE @s_diabet   INT = (SELECT Id_Servicio FROM SERVICIO WHERE Nom_serv = 'Evaluacion pie diabetico');

    DECLARE @m_crema INT = (SELECT Id_Medicamento FROM MEDICAMENTO WHERE Nom_Med = 'Crema hidratante ureico');
    DECLARE @m_gasas INT = (SELECT Id_Medicamento FROM MEDICAMENTO WHERE Nom_Med = 'Gasas esteriles');

    DECLARE @ayer DATE = DATEADD(DAY, -1, CAST(GETDATE() AS DATE));
    DECLARE @anteayer DATE = DATEADD(DAY, -2, CAST(GETDATE() AS DATE));
    DECLARE @hoy DATE = CAST(GETDATE() AS DATE);

    /* ---------------- Cita 1: atendida y pagada en su totalidad ------------ */
    INSERT INTO CITA (Id_Cliente, Id_Podologo, Id_Recep, Fe_Cita, Hora_Cita, Estado, Motivo)
    VALUES (@ana, @maria, @rosa, @anteayer, CAST('10:00' AS TIME), 'Atendida',
            'Dolor en el talon del pie derecho');
    DECLARE @cita1 INT = SCOPE_IDENTITY();

    INSERT INTO ATENCION (Id_Cita, Diag, Trat, Obs, Fe_Atencion)
    VALUES (@cita1, 'Pie diabetico sin lesiones activas',
            'Quiropodia y curacion con material esteril',
            'Se indica control preventivo en 15 dias e hidratacion diaria', @anteayer);
    DECLARE @ate1 INT = SCOPE_IDENTITY();

    INSERT INTO DETALLE_ATENCION (Id_Atencion, Id_Servicio, Cant_Aten, Subt_Aten)
    VALUES (@ate1, @s_consulta, 1, (SELECT Precio_Servicio FROM SERVICIO WHERE Id_Servicio = @s_consulta));

    INSERT INTO DETALLE_MEDICAMENTO (Id_Atencion, Id_Medicamento, Cant_Med, Subt_Med)
    VALUES (@ate1, @m_crema, 1, (SELECT Precio_Med FROM MEDICAMENTO WHERE Id_Medicamento = @m_crema));

    /* El medicamento se entrego al paciente: se descuenta del inventario. */
    UPDATE MEDICAMENTO SET Stock_Med = Stock_Med - 1 WHERE Id_Medicamento = @m_crema;

    /* Regla R2: el importe de la boleta es la suma de sus consumos. */
    DECLARE @total1 DECIMAL(10,2) =
          (SELECT ISNULL(SUM(Subt_Aten), 0) FROM DETALLE_ATENCION    WHERE Id_Atencion = @ate1)
        + (SELECT ISNULL(SUM(Subt_Med),  0) FROM DETALLE_MEDICAMENTO WHERE Id_Atencion = @ate1);

    INSERT INTO BOLETA (Id_Atencion, Id_Recep, Fe_Emision, Importe, Estado_Pago)
    VALUES (@ate1, @rosa, @anteayer, @total1, 'Pagada');
    DECLARE @bol1 INT = SCOPE_IDENTITY();

    INSERT INTO PAGO (Id_Boleta, Tipo_Pago, Monto, Fe_Pago)
    VALUES (@bol1, 'Yape', @total1, @anteayer);

    /* ---------------- Cita 2: atendida con pago parcial -------------------- */
    INSERT INTO CITA (Id_Cliente, Id_Podologo, Id_Recep, Fe_Cita, Hora_Cita, Estado, Motivo)
    VALUES (@luis, @maria, @rosa, @ayer, CAST('11:30' AS TIME), 'Atendida',
            'Una encarnada del primer dedo');
    DECLARE @cita2 INT = SCOPE_IDENTITY();

    INSERT INTO ATENCION (Id_Cita, Diag, Trat, Obs, Fe_Atencion)
    VALUES (@cita2, 'Onicocriptosis con hiperqueratosis periungueal',
            'Quiropodia con extraccion parcial de la una',
            'Volver en 15 dias para control de la una', @ayer);
    DECLARE @ate2 INT = SCOPE_IDENTITY();

    INSERT INTO DETALLE_ATENCION (Id_Atencion, Id_Servicio, Cant_Aten, Subt_Aten)
    VALUES (@ate2, @s_quiro, 1, (SELECT Precio_Servicio FROM SERVICIO WHERE Id_Servicio = @s_quiro));

    DECLARE @total2 DECIMAL(10,2) =
          (SELECT ISNULL(SUM(Subt_Aten), 0) FROM DETALLE_ATENCION    WHERE Id_Atencion = @ate2)
        + (SELECT ISNULL(SUM(Subt_Med),  0) FROM DETALLE_MEDICAMENTO WHERE Id_Atencion = @ate2);

    INSERT INTO BOLETA (Id_Atencion, Id_Recep, Fe_Emision, Importe, Estado_Pago)
    VALUES (@ate2, @rosa, @ayer, @total2, 'Pendiente');
    DECLARE @bol2 INT = SCOPE_IDENTITY();

    /* Pago parcial: queda la mitad del saldo por cobrar. */
    INSERT INTO PAGO (Id_Boleta, Tipo_Pago, Monto, Fe_Pago)
    VALUES (@bol2, 'Efectivo', CAST(@total2 / 2 AS DECIMAL(10,2)), @ayer);

    /* ---------------- Cita 3: atendida hoy, esperando en caja -------------- */
    INSERT INTO CITA (Id_Cliente, Id_Podologo, Id_Recep, Fe_Cita, Hora_Cita, Estado, Motivo)
    VALUES (@carmen, @maria, @rosa, @hoy, CAST('09:00' AS TIME), 'Atendida',
            'Control preventivo pie diabetico');
    DECLARE @cita3 INT = SCOPE_IDENTITY();

    INSERT INTO ATENCION (Id_Cita, Diag, Trat, Obs, Fe_Atencion)
    VALUES (@cita3, 'Pie diabetico sin lesiones activas',
            'Evaluacion con monofilamento, quiropodia y curacion',
            'Sensibilidad conservada. Proximo control en 30 dias', @hoy);
    DECLARE @ate3 INT = SCOPE_IDENTITY();

    INSERT INTO DETALLE_ATENCION (Id_Atencion, Id_Servicio, Cant_Aten, Subt_Aten)
    VALUES (@ate3, @s_diabet, 1, (SELECT Precio_Servicio FROM SERVICIO WHERE Id_Servicio = @s_diabet));

    INSERT INTO DETALLE_ATENCION (Id_Atencion, Id_Servicio, Cant_Aten, Subt_Aten)
    VALUES (@ate3, @s_consulta, 1, (SELECT Precio_Servicio FROM SERVICIO WHERE Id_Servicio = @s_consulta));

    INSERT INTO DETALLE_MEDICAMENTO (Id_Atencion, Id_Medicamento, Cant_Med, Subt_Med)
    VALUES (@ate3, @m_gasas, 1, (SELECT Precio_Med FROM MEDICAMENTO WHERE Id_Medicamento = @m_gasas));

    UPDATE MEDICAMENTO SET Stock_Med = Stock_Med - 1 WHERE Id_Medicamento = @m_gasas;
    /* Sin boleta: es la atencion que el recepcionista debe facturar en caja. */

    /* ---------------- Citas futuras programadas ---------------------------- */
    INSERT INTO CITA (Id_Cliente, Id_Podologo, Id_Recep, Fe_Cita, Hora_Cita, Estado, Motivo)
    VALUES (@carmen, @carlos, @rosa, DATEADD(DAY, 1, @hoy), CAST('16:00' AS TIME), 'Programada',
            'Evaluacion estetica de unas');

    INSERT INTO CITA (Id_Cliente, Id_Podologo, Id_Recep, Fe_Cita, Hora_Cita, Estado, Motivo)
    VALUES (@ana, @carlos, @rosa, DATEADD(DAY, 3, @hoy), CAST('12:00' AS TIME), 'Programada',
            'Mantenimiento preventivo');

    PRINT 'Flujo cargado: 5 citas, 3 atenciones, 1 boleta pagada y 1 con saldo pendiente.';
END
ELSE
    PRINT 'La tabla CITA ya tenia registros: no se volvio a cargar el flujo de ejemplo.';
GO

/* ---------------------------------------------------------------------------
   7. RESUMEN DE LO QUE QUEDO EN LA BASE
   --------------------------------------------------------------------------- */
SELECT 'CLIENTE'             AS Tabla, COUNT(*) AS Filas FROM CLIENTE
UNION ALL SELECT 'PODOLOGO',            COUNT(*) FROM PODOLOGO
UNION ALL SELECT 'RECEPCIONISTA',       COUNT(*) FROM RECEPCIONISTA
UNION ALL SELECT 'SERVICIO',            COUNT(*) FROM SERVICIO
UNION ALL SELECT 'MEDICAMENTO',         COUNT(*) FROM MEDICAMENTO
UNION ALL SELECT 'CITA',                COUNT(*) FROM CITA
UNION ALL SELECT 'ATENCION',            COUNT(*) FROM ATENCION
UNION ALL SELECT 'DETALLE_ATENCION',    COUNT(*) FROM DETALLE_ATENCION
UNION ALL SELECT 'DETALLE_MEDICAMENTO', COUNT(*) FROM DETALLE_MEDICAMENTO
UNION ALL SELECT 'BOLETA',              COUNT(*) FROM BOLETA
UNION ALL SELECT 'PAGO',                COUNT(*) FROM PAGO
UNION ALL SELECT 'USUARIO',             COUNT(*) FROM USUARIO;
GO

PRINT 'Listo. Ingrese al sistema con: admin / admin123  |  recepcion / recepcion123  |  podologo / podologo123';
GO
