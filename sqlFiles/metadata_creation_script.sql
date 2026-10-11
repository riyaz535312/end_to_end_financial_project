/* =========================================================
   1. CREATE SCHEMA
   ========================================================= */

IF SCHEMA_ID('orchestrator') IS NULL
    EXEC('CREATE SCHEMA orchestrator');
GO


/* =========================================================
   2. BATCH MASTER
   ========================================================= */

CREATE TABLE orchestrator.Batch
(
    BatchId       INT IDENTITY(1,1) PRIMARY KEY,
    BatchName     VARCHAR(100) NOT NULL UNIQUE,
    Description   VARCHAR(500) NULL,
    IsActive      BIT NOT NULL DEFAULT 1,
    CreatedAt     DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO


/* =========================================================
   3. PIPELINE MASTER
   ========================================================= */

CREATE TABLE orchestrator.Pipeline
(
    PipelineId       INT IDENTITY(1,1) PRIMARY KEY,
    PipelineCode     VARCHAR(100) NOT NULL UNIQUE,
    ADFPipelineName  VARCHAR(200) NOT NULL,
    PipelineType     VARCHAR(50) NOT NULL DEFAULT 'ADF',
    Description      VARCHAR(500) NULL,
    IsActive         BIT NOT NULL DEFAULT 1,
    CreatedAt        DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO


/* =========================================================
   4. BATCH STAGE
   One row per pipeline invocation in a batch.
   ========================================================= */

CREATE TABLE orchestrator.BatchStage
(
    BatchStageId   INT IDENTITY(1,1) PRIMARY KEY,
    BatchId        INT NOT NULL,
    PipelineId     INT NOT NULL,
    StageCode      VARCHAR(100) NOT NULL,
    StageName      VARCHAR(200) NOT NULL,
    StageOrder     INT NOT NULL,
    IsEnabled      BIT NOT NULL DEFAULT 1,
    IsRequired     BIT NOT NULL DEFAULT 1,
    CreatedAt      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT FK_BatchStage_Batch
        FOREIGN KEY (BatchId)
        REFERENCES orchestrator.Batch(BatchId),

    CONSTRAINT FK_BatchStage_Pipeline
        FOREIGN KEY (PipelineId)
        REFERENCES orchestrator.Pipeline(PipelineId),

    CONSTRAINT UQ_BatchStage_Order
        UNIQUE (BatchId, StageOrder),

    CONSTRAINT CK_BatchStage_Order
        CHECK (StageOrder > 0)
);
GO


/* =========================================================
   5. PIPELINE PARAMETERS
   One row per parameter for each BatchStage.
   ========================================================= */

CREATE TABLE orchestrator.PipelineParameter
(
    PipelineParameterId  INT IDENTITY(1,1) PRIMARY KEY,
    BatchStageId         INT NOT NULL,
    ParameterName        VARCHAR(150) NOT NULL,
    ParameterValue       NVARCHAR(2000) NULL,
    DataType             VARCHAR(30) NOT NULL DEFAULT 'string',
    IsSensitive          BIT NOT NULL DEFAULT 0,

    CONSTRAINT FK_PipelineParameter_BatchStage
        FOREIGN KEY (BatchStageId)
        REFERENCES orchestrator.BatchStage(BatchStageId),

    CONSTRAINT UQ_PipelineParameter_Name
        UNIQUE (BatchStageId, ParameterName),

    CONSTRAINT CK_PipelineParameter_DataType
        CHECK (DataType IN
            ('string', 'int', 'float', 'bool', 'object', 'array'))
);
GO


/* =========================================================
   6. BATCH RUN LOG
   ========================================================= */

CREATE TABLE orchestrator.BatchRunLog
(
    BatchRunId     BIGINT IDENTITY(1,1) PRIMARY KEY,
    BatchId        INT NOT NULL,
    ADFRunId       VARCHAR(100) NULL,
    StartTime      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    EndTime        DATETIME2 NULL,
    RunStatus      VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    ErrorMessage   NVARCHAR(4000) NULL,

    CONSTRAINT FK_BatchRunLog_Batch
        FOREIGN KEY (BatchId)
        REFERENCES orchestrator.Batch(BatchId),

    CONSTRAINT CK_BatchRunLog_Status
        CHECK (RunStatus IN
            ('RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED'))
);
GO


/* =========================================================
   7. STAGE RUN LOG
   ========================================================= */

CREATE TABLE orchestrator.StageRunLog
(
    StageRunId     BIGINT IDENTITY(1,1) PRIMARY KEY,
    BatchRunId     BIGINT NOT NULL,
    BatchStageId   INT NOT NULL,
    ADFRunId       VARCHAR(100) NULL,
    StartTime      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    EndTime        DATETIME2 NULL,
    RunStatus      VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    ErrorMessage   NVARCHAR(4000) NULL,

    CONSTRAINT FK_StageRunLog_BatchRun
        FOREIGN KEY (BatchRunId)
        REFERENCES orchestrator.BatchRunLog(BatchRunId),

    CONSTRAINT FK_StageRunLog_BatchStage
        FOREIGN KEY (BatchStageId)
        REFERENCES orchestrator.BatchStage(BatchStageId),

    CONSTRAINT CK_StageRunLog_Status
        CHECK (RunStatus IN
            ('RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED'))
);
GO