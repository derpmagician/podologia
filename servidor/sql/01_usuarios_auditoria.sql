/* ============================================================================
   CLÍNICA PODOLÓGICA — COMPLEMENTO AL MODELO FÍSICO
   Base de datos : SQLData_ClinicaPodologicaV2 (SQL Server)
   Archivo       : 01_usuarios_auditoria.sql

   Qué agrega sobre el script original:
     1. Tabla USUARIO  -> credenciales únicas y roles (Administrador,
                          Recepcionista, Podologo). Requerido por la política
                          de seguridad del proyecto.
     2. Tabla AUDITORIA -> logs básicos de quién entra y quién modifica.
                          Requerido por la regla R3 y por el área de auditoría.
     3. Índice único   -> implementa la regla R1 en el motor: un podólogo no
                          puede tener dos citas activas a la misma fecha/hora.
     4. Trigger        -> implementa la regla R4: una boleta pagada no se borra.

   El script es IDEMPOTENTE: puede ejecutarse varias veces sin duplicar nada.
   ============================================================================ */

USE SQLData_ClinicaPodologicaV2;
GO

/* Necesario para los índices filtrados (regla R1). */
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/* ---------------------------------------------------------------------------
   1. USUARIO — control de acceso
   ---------------------------------------------------------------------------
   Rol 'Administrador' : no se vincula a ningún empleado (acceso total).
   Rol 'Podologo'      : se vincula obligatoriamente a un PODOLOGO.
   Rol 'Recepcionista' : se vincula obligatoriamente a un RECEPCIONISTA.
   La clave NUNCA se guarda en texto plano: se guarda un hash PBKDF2-SHA256
   con formato  pbkdf2$<iteraciones>$<sal_hex>$<hash_hex>.
   --------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.USUARIO', 'U') IS NULL
BEGIN
    CREATE TABLE USUARIO (
        Id_Usuario    INT PRIMARY KEY IDENTITY,
        Usuario       VARCHAR(50)  NOT NULL,
        Clave_Hash    VARCHAR(200) NOT NULL,
        Rol           VARCHAR(20)  NOT NULL,
        Id_Podologo   INT NULL,
        Id_Recep      INT NULL,
        Nombres       VARCHAR(120) NOT NULL,
        Activo        BIT          NOT NULL CONSTRAINT DF_USUARIO_Activo DEFAULT (1),
        Fe_Alta       DATE         NOT NULL CONSTRAINT DF_USUARIO_FeAlta  DEFAULT (GETDATE()),
        Ultimo_Acceso DATETIME     NULL,
        CONSTRAINT UQ_USUARIO_Usuario UNIQUE (Usuario),
        CONSTRAINT CK_USUARIO_Rol CHECK (Rol IN ('Administrador', 'Recepcionista', 'Podologo')),
        CONSTRAINT CK_USUARIO_Vinculo CHECK (
               (Rol = 'Administrador' AND Id_Podologo IS NULL     AND Id_Recep IS NULL)
            OR (Rol = 'Podologo'      AND Id_Podologo IS NOT NULL AND Id_Recep IS NULL)
            OR (Rol = 'Recepcionista' AND Id_Recep IS NOT NULL    AND Id_Podologo IS NULL)
        ),
        CONSTRAINT FK_USUARIO_Podologo      FOREIGN KEY (Id_Podologo) REFERENCES PODOLOGO(Id_Podologo),
        CONSTRAINT FK_USUARIO_Recepcionista FOREIGN KEY (Id_Recep)    REFERENCES RECEPCIONISTA(Id_Recep)
    );

    CREATE INDEX IX_USUARIO_Rol ON USUARIO(Rol);
END
GO

/* ---------------------------------------------------------------------------
   2. AUDITORIA — logs básicos de seguridad
   ---------------------------------------------------------------------------
   Se registra: ingreso correcto, intento fallido, salida, altas, cambios,
   bajas y la emisión/cobro de boletas. Solo el Administrador puede leerla
   (regla R3).
   --------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.AUDITORIA', 'U') IS NULL
BEGIN
    CREATE TABLE AUDITORIA (
        Id_Auditoria INT PRIMARY KEY IDENTITY,
        Fe_Evento    DATETIME     NOT NULL CONSTRAINT DF_AUD_Fe DEFAULT (GETDATE()),
        Id_Usuario   INT          NULL,
        Usuario      VARCHAR(50)  NULL,
        Rol          VARCHAR(20)  NULL,
        Accion       VARCHAR(25)  NOT NULL,
        Tabla        VARCHAR(40)  NULL,
        Id_Registro  VARCHAR(40)  NULL,
        Detalle      VARCHAR(400) NULL,
        Equipo       VARCHAR(60)  NULL,
        CONSTRAINT FK_AUDITORIA_Usuario FOREIGN KEY (Id_Usuario) REFERENCES USUARIO(Id_Usuario),
        CONSTRAINT CK_AUDITORIA_Accion CHECK (Accion IN (
            'LOGIN', 'LOGIN_FALLIDO', 'LOGOUT', 'INSERT', 'UPDATE', 'DELETE', 'COBRO',
            'EXPORTAR', 'IMPORTAR'
        ))
    );

    CREATE INDEX IX_AUDITORIA_Fe     ON AUDITORIA(Fe_Evento DESC);
    CREATE INDEX IX_AUDITORIA_Accion ON AUDITORIA(Accion);
END
GO

/* Si la tabla ya existía sin las acciones de respaldo, se actualiza la regla. */
IF EXISTS (SELECT 1 FROM sys.check_constraints
           WHERE name = 'CK_AUDITORIA_Accion' AND definition NOT LIKE '%EXPORTAR%')
BEGIN
    ALTER TABLE AUDITORIA DROP CONSTRAINT CK_AUDITORIA_Accion;
    ALTER TABLE AUDITORIA ADD CONSTRAINT CK_AUDITORIA_Accion CHECK (Accion IN (
        'LOGIN', 'LOGIN_FALLIDO', 'LOGOUT', 'INSERT', 'UPDATE', 'DELETE', 'COBRO',
        'EXPORTAR', 'IMPORTAR'
    ));
END
GO

/* ---------------------------------------------------------------------------
   3. REGLA R1 — Identidad única de la cita
   Un podólogo no puede tener dos citas a la misma fecha y hora.
   Las citas 'Cancelada' se excluyen para que ese horario quede libre.
   --------------------------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_CITA_Podologo_Fecha_Hora')
BEGIN
    CREATE UNIQUE INDEX UX_CITA_Podologo_Fecha_Hora
        ON CITA(Id_Podologo, Fe_Cita, Hora_Cita)
        WHERE Estado <> 'Cancelada';
END
GO

/* Índices de apoyo para la agenda y la caja */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_CITA_Fecha')
    CREATE INDEX IX_CITA_Fecha ON CITA(Fe_Cita, Hora_Cita);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_BOLETA_Estado')
    CREATE INDEX IX_BOLETA_Estado ON BOLETA(Estado_Pago);
GO

/* ---------------------------------------------------------------------------
   4. REGLA R4 — Inmutabilidad de la boleta pagada
   Una boleta con Estado_Pago = 'Pagada' no se puede eliminar. Tampoco se
   elimina una boleta que ya tiene pagos asociados (primero se anulan).
   --------------------------------------------------------------------------- */
IF OBJECT_ID('dbo.TR_BOLETA_NoEliminarPagada', 'TR') IS NULL
BEGIN
    EXEC('
    CREATE TRIGGER TR_BOLETA_NoEliminarPagada
    ON BOLETA
    INSTEAD OF DELETE
    AS
    BEGIN
        SET NOCOUNT ON;

        IF EXISTS (SELECT 1 FROM deleted WHERE Estado_Pago = ''Pagada'')
        BEGIN
            RAISERROR(''Regla R4: una boleta pagada no se puede eliminar.'', 16, 1);
            RETURN;
        END

        IF EXISTS (SELECT 1 FROM deleted d INNER JOIN PAGO p ON p.Id_Boleta = d.Id_Boleta)
        BEGIN
            RAISERROR(''La boleta tiene pagos registrados: no se puede eliminar.'', 16, 1);
            RETURN;
        END

        DELETE FROM BOLETA WHERE Id_Boleta IN (SELECT Id_Boleta FROM deleted);
    END');
END
GO

PRINT 'Listo: USUARIO, AUDITORIA, indices y trigger creados en SQLData_ClinicaPodologicaV2.';
GO
