/* ============================================================================
   CLÍNICA PODOLÓGICA — MODELO FÍSICO
   Base de datos : SQLData_ClinicaPodologicaV2 (SQL Server)
   Archivo       : 00_esquema.sql

   Crea la base de datos y las 11 tablas del informe.

   Este script NO fija una ruta absoluta para los archivos .mdf y .ldf. Le
   pregunta a SQL Server cuál es su carpeta de datos por defecto y crea los
   archivos ahí, así que se puede ejecutar en cualquier computadora sin
   editar nada. Los tamaños sí son los del modelo físico del informe.

   Para ver dónde quedaron los archivos, después de ejecutarlo:
       SELECT physical_name FROM sys.master_files
        WHERE database_id = DB_ID('SQLData_ClinicaPodologicaV2');

   Ejecutar una sola vez. Si la base ya existe, la creación dará error y el
   resto de lotes no se ejecutará.
   ============================================================================ */

DECLARE @datos NVARCHAR(400) = CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS NVARCHAR(400));
DECLARE @log   NVARCHAR(400) = CAST(SERVERPROPERTY('InstanceDefaultLogPath')  AS NVARCHAR(400));
IF @log IS NULL SET @log = @datos;

/* Si la instancia no informa su carpeta (versiones antiguas), se crea la base
   sin detallar archivos y SQL Server decide. */
DECLARE @archivos NVARCHAR(MAX) = N'';
IF @datos IS NOT NULL
    SET @archivos = N'
    ON
    (
        NAME = SQLData_ClinicaPodologicaV2_Data,
        FILENAME = ''' + @datos + N'SQLData_ClinicaPodologicaV2_Data.mdf'',
        SIZE = 10MB,
        MAXSIZE = 100MB,
        FILEGROWTH = 5MB
    )
    LOG ON
    (
        NAME = SQLData_ClinicaPodologicaV2_Log,
        FILENAME = ''' + @log + N'SQLData_ClinicaPodologicaV2_Log.ldf'',
        SIZE = 5MB,
        MAXSIZE = 50MB,
        FILEGROWTH = 2MB
    )';

EXEC (N'CREATE DATABASE SQLData_ClinicaPodologicaV2' + @archivos + N' COLLATE Latin1_General_CI_AS;');
GO

USE SQLData_ClinicaPodologicaV2;
GO

CREATE TABLE CLIENTE (
    Id_Cliente INT PRIMARY KEY IDENTITY,
    Noms_Cliente VARCHAR(100),
    Ape_Pat_Cliente VARCHAR(50),
    Ape_Mat_Cliente VARCHAR(50),
    Dni_Cliente VARCHAR(8) UNIQUE,
    Tel_Cliente VARCHAR(15),
    Email_Cliente VARCHAR(100),
    Fecha_Registro DATE
);

CREATE TABLE PODOLOGO (
    Id_Podologo INT PRIMARY KEY IDENTITY,
    Nom_Podologo VARCHAR(100),
    Ape_Pat_Podo VARCHAR(50),
    Ape_Mat_Podo VARCHAR(50),
    Esp_Podo VARCHAR(100),
    Tel_Podo VARCHAR(15),
    Email_Podo VARCHAR(100)
);

CREATE TABLE RECEPCIONISTA (
    Id_Recep INT PRIMARY KEY IDENTITY,
    Noms_Recep VARCHAR(100),
    Apellidos_Recep VARCHAR(100),
    Tel_Recep VARCHAR(15)
);

CREATE TABLE CITA (
    Id_Cita INT PRIMARY KEY IDENTITY,
    Id_Cliente INT,
    Id_Podologo INT,
    Id_Recep INT,
    Fe_Cita DATE,
    Hora_Cita TIME,
    Estado VARCHAR(30),
    Motivo VARCHAR(200),
    FOREIGN KEY (Id_Cliente) REFERENCES CLIENTE(Id_Cliente),
    FOREIGN KEY (Id_Podologo) REFERENCES PODOLOGO(Id_Podologo),
    FOREIGN KEY (Id_Recep) REFERENCES RECEPCIONISTA(Id_Recep)
);

CREATE TABLE ATENCION (
    Id_Atencion INT PRIMARY KEY IDENTITY,
    Id_Cita INT,
    Diag VARCHAR(MAX),
    Trat VARCHAR(MAX),
    Obs VARCHAR(MAX),
    Fe_Atencion DATE,
    FOREIGN KEY (Id_Cita) REFERENCES CITA(Id_Cita)
);

CREATE TABLE SERVICIO (
    Id_Servicio INT PRIMARY KEY IDENTITY,
    Nom_serv VARCHAR(100),
    Descripcion VARCHAR(200),
    Precio_Servicio DECIMAL(10,2)
);

CREATE TABLE MEDICAMENTO (
    Id_Medicamento INT PRIMARY KEY IDENTITY,
    Nom_Med VARCHAR(100),
    Stock_Med INT,
    Precio_Med DECIMAL(10,2),
    Fe_Venc_Med DATE
);

CREATE TABLE DETALLE_ATENCION (
    Id_Detalle_Aten INT PRIMARY KEY IDENTITY,
    Id_Atencion INT,
    Id_Servicio INT,
    Cant_Aten INT,
    Subt_Aten DECIMAL(10,2),
    FOREIGN KEY (Id_Atencion) REFERENCES ATENCION(Id_Atencion),
    FOREIGN KEY (Id_Servicio) REFERENCES SERVICIO(Id_Servicio)
);

CREATE TABLE DETALLE_MEDICAMENTO (
    Id_Detalle_Med INT PRIMARY KEY IDENTITY,
    Id_Atencion INT,
    Id_Medicamento INT,
    Cant_Med INT,
    Subt_Med DECIMAL(10,2),
    FOREIGN KEY (Id_Atencion) REFERENCES ATENCION(Id_Atencion),
    FOREIGN KEY (Id_Medicamento) REFERENCES MEDICAMENTO(Id_Medicamento)
);

CREATE TABLE BOLETA (
    Id_Boleta INT PRIMARY KEY IDENTITY,
    Id_Atencion INT,
    Id_Recep INT,
    Fe_Emision DATE,
    Importe DECIMAL(10,2),
    Estado_Pago VARCHAR(20),
    FOREIGN KEY (Id_Atencion) REFERENCES ATENCION(Id_Atencion),
    FOREIGN KEY (Id_Recep) REFERENCES RECEPCIONISTA(Id_Recep)
);

CREATE TABLE PAGO (
    Id_Pago INT PRIMARY KEY IDENTITY,
    Id_Boleta INT,
    Tipo_Pago VARCHAR(30),
    Monto DECIMAL(10,2),
    Fe_Pago DATE,
    FOREIGN KEY (Id_Boleta) REFERENCES BOLETA(Id_Boleta)
); 
