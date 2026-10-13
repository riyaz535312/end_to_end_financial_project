
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    --------------------------------------------------
    -- 1. Define the four batch configurations
    --------------------------------------------------
    DECLARE @BatchConfig TABLE
    (
        BatchName       VARCHAR(100),
        Description     VARCHAR(500),
        SourcePath      NVARCHAR(500),
        SinkPath        NVARCHAR(500),
        FileName        NVARCHAR(200)
    );

    INSERT INTO @BatchConfig
    VALUES
    (
        'FIN_TRANSACTIONS_LOAD',
        'Copy transactions files from landing to raw',
        'landing/transactions',
        'raw/transactions/{LOAD_DATE}',
        'transactions.csv'
    ),
    (
        'FIN_ACCOUNTS_LOAD',
        'Copy accounts files from landing to raw',
        'landing/accounts',
        'raw/accounts/{LOAD_DATE}',
        'accounts.parquet'
    ),
    (
        'FIN_MERCHANTS_LOAD',
        'Copy merchants files from landing to raw',
        'landing/merchants',
        'raw/merchants/{LOAD_DATE}',
        'merchants.csv'
    ),
    (
        'FIN_FRAUD_EVENTS_LOAD',
        'Copy fraud events files from landing to raw',
        'landing/fraudevents',
        'raw/fraudevents/{LOAD_DATE}',
        'fraud_events.json'
    );

    --------------------------------------------------
    -- 2. Register the generic pipeline if missing
    --------------------------------------------------
    IF NOT EXISTS
    (
        SELECT 1
        FROM orchestrator.Pipeline
        WHERE ADFPipelineName =
              'pl_generic_copy_landing_to_raw'
    )
    BEGIN
        INSERT INTO orchestrator.Pipeline
        (
            PipelineCode,
            ADFPipelineName,
            PipelineType,
            Description
        )
        VALUES
        (
            'COPY_LANDING_TO_RAW',
            'pl_generic_copy_landing_to_raw',
            'ADF',
            'Generic landing to raw copy pipeline'
        );
    END;

    --------------------------------------------------
    -- 3. Register the four batches if missing
    --------------------------------------------------
    INSERT INTO orchestrator.Batch
    (
        BatchName,
        Description
    )
    SELECT
        c.BatchName,
        c.Description
    FROM @BatchConfig c
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM orchestrator.Batch b
        WHERE b.BatchName = c.BatchName
    );

    --------------------------------------------------
    -- 4. Create one stage per batch
    --------------------------------------------------
    INSERT INTO orchestrator.BatchStage
    (
        BatchId,
        PipelineId,
        StageCode,
        StageName,
        StageOrder,
        IsEnabled,
        IsRequired
    )
    SELECT
        b.BatchId,
        p.PipelineId,
        'LANDING_TO_RAW',
        'Copy landing files to raw',
        1,
        1,
        1
    FROM @BatchConfig c
    INNER JOIN orchestrator.Batch b
        ON b.BatchName = c.BatchName
    INNER JOIN orchestrator.Pipeline p
        ON p.ADFPipelineName =
           'pl_generic_copy_landing_to_raw'
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM orchestrator.BatchStage bs
        WHERE bs.BatchId = b.BatchId
          AND bs.StageCode = 'LANDING_TO_RAW'
    );

    --------------------------------------------------
    -- 5. Define six parameters for every batch
    --------------------------------------------------
    DECLARE @Parameters TABLE
    (
        BatchName       VARCHAR(100),
        ParameterName   NVARCHAR(200),
        ParameterValue  NVARCHAR(2000),
        DataType        VARCHAR(50),
        IsSensitive     BIT
    );

    INSERT INTO @Parameters
    SELECT
        c.BatchName,
        v.ParameterName,
        v.ParameterValue,
        'string',
        0
    FROM @BatchConfig c
    CROSS APPLY
    (
        VALUES
        (
            'plp_source_container_name',
            'finance-lake'
        ),
        (
            'plp_target_container_name',
            'finance-lake'
        ),
        (
            'plp_source_path',
            c.SourcePath
        ),
        (
            'plp_sink_path',
            c.SinkPath
        ),
        (
            'plp_source_filename',
            c.FileName
        ),
        (
            'plp_sink_filename',
            c.FileName
        )
    ) v(ParameterName, ParameterValue);

    --------------------------------------------------
    -- 6. Update existing parameter values
    --------------------------------------------------
    UPDATE pp
    SET
        pp.ParameterValue = prm.ParameterValue,
        pp.DataType = prm.DataType,
        pp.IsSensitive = prm.IsSensitive
    FROM orchestrator.PipelineParameter pp
    INNER JOIN orchestrator.BatchStage bs
        ON bs.BatchStageId = pp.BatchStageId
    INNER JOIN orchestrator.Batch b
        ON b.BatchId = bs.BatchId
    INNER JOIN @Parameters prm
        ON prm.BatchName = b.BatchName
       AND prm.ParameterName = pp.ParameterName;

    --------------------------------------------------
    -- 7. Insert missing parameter rows
    --------------------------------------------------
    INSERT INTO orchestrator.PipelineParameter
    (
        BatchStageId,
        ParameterName,
        ParameterValue,
        DataType,
        IsSensitive
    )
    SELECT
        bs.BatchStageId,
        prm.ParameterName,
        prm.ParameterValue,
        prm.DataType,
        prm.IsSensitive
    FROM @Parameters prm
    INNER JOIN orchestrator.Batch b
        ON b.BatchName = prm.BatchName
    INNER JOIN orchestrator.BatchStage bs
        ON bs.BatchId = b.BatchId
       AND bs.StageCode = 'LANDING_TO_RAW'
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM orchestrator.PipelineParameter pp
        WHERE pp.BatchStageId = bs.BatchStageId
          AND pp.ParameterName = prm.ParameterName
    );

    COMMIT TRANSACTION;

    PRINT 'Batch configurations created successfully.';

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;




----- SIMPLER VERSION ------------

/* =========================================================
   GENERIC METADATA FRAMEWORK INSERT TEMPLATE
   Tables:
     1. orchestrator.Batch
     2. orchestrator.Pipeline
     3. orchestrator.BatchStage
     4. orchestrator.PipelineParameter

   IMPORTANT:
   - Run Batch INSERT only for a new batch.
   - Run Pipeline INSERT only if the pipeline is not registered.
   - Run BatchStage INSERT once per batch/stage.
   - Replace @BatchStageId with the actual ID before inserting
     PipelineParameter rows.
   ========================================================= */


/* =========================================================
   STEP 1: CREATE A BATCH
   Change the batch name and description.
   ========================================================= */

INSERT INTO orchestrator.Batch
(
    BatchName,
    Description
)
VALUES
(
    'FIN_TRANSACTIONS_LOAD',
    'Load transactions data'
);


/* =========================================================
   STEP 2: REGISTER AN ADF PIPELINE
   Run only if this pipeline does not already exist.
   Change the pipeline details as required.
   ========================================================= */

INSERT INTO orchestrator.Pipeline
(
    PipelineCode,
    ADFPipelineName,
    PipelineType,
    Description
)
VALUES
(
    'COPY_LANDING_TO_RAW',
    'pl_generic_copy_landing_to_raw',
    'ADF',
    'Copy files from landing to raw'
);


/* =========================================================
   STEP 3: ADD A STAGE TO A BATCH
   Change batch name, pipeline name, stage code, stage name,
   and stage order.

   StageOrder example:
     1 = LANDING_TO_RAW
     2 = RAW_TO_BRONZE
     3 = BRONZE_TO_SILVER
     4 = SILVER_TO_GOLD
   ========================================================= */

INSERT INTO orchestrator.BatchStage
(
    BatchId,
    PipelineId,
    StageCode,
    StageName,
    StageOrder,
    IsEnabled,
    IsRequired
)
SELECT
    b.BatchId,
    p.PipelineId,
    'LANDING_TO_RAW',
    'Copy landing files to raw',
    1,
    1,
    1
FROM orchestrator.Batch b
CROSS JOIN orchestrator.Pipeline p
WHERE b.BatchName = 'FIN_TRANSACTIONS_LOAD'
  AND p.ADFPipelineName = 'pl_generic_copy_landing_to_raw';


/* =========================================================
   STEP 4: GET THE STAGE ID
   Run this query and copy the BatchStageId for your stage.
   ========================================================= */

SELECT
    b.BatchName,
    bs.BatchStageId,
    bs.StageCode,
    bs.StageOrder,
    p.ADFPipelineName
FROM orchestrator.BatchStage bs
INNER JOIN orchestrator.Batch b
    ON b.BatchId = bs.BatchId
INNER JOIN orchestrator.Pipeline p
    ON p.PipelineId = bs.PipelineId
WHERE b.BatchName = 'FIN_TRANSACTIONS_LOAD'
ORDER BY bs.StageOrder;


/* =========================================================
   STEP 5: INSERT PARAMETERS FOR LANDING_TO_RAW
   Replace 101 with the actual BatchStageId.
   Change paths and filenames for each batch.

   These six parameters are for the generic copy pipeline.
   ========================================================= */

INSERT INTO orchestrator.PipelineParameter
(
    BatchStageId,
    ParameterName,
    ParameterValue,
    DataType,
    IsSensitive
)
VALUES
(101, 'plp_source_container_name', 'finance-lake', 'string', 0),
(101, 'plp_target_container_name', 'finance-lake', 'string', 0),
(101, 'plp_source_path', 'landing/transactions', 'string', 0),
(101, 'plp_sink_path', 'raw/transactions/{LOAD_DATE}', 'string', 0),
(101, 'plp_source_filename', 'transactions.csv', 'string', 0),
(101, 'plp_sink_filename', 'transactions.csv', 'string', 0);


/* =========================================================
   STEP 6: VERIFY THE COMPLETE BATCH CONFIGURATION
   ========================================================= */

SELECT
    b.BatchName,
    bs.StageCode,
    bs.StageOrder,
    p.ADFPipelineName,
    pp.ParameterName,
    pp.ParameterValue,
    pp.DataType
FROM orchestrator.Batch b
INNER JOIN orchestrator.BatchStage bs
    ON bs.BatchId = b.BatchId
INNER JOIN orchestrator.Pipeline p
    ON p.PipelineId = bs.PipelineId
LEFT JOIN orchestrator.PipelineParameter pp
    ON pp.BatchStageId = bs.BatchStageId
WHERE b.BatchName = 'FIN_TRANSACTIONS_LOAD'
ORDER BY
    bs.StageOrder,
    pp.ParameterName;


/* =========================================================
   FUTURE USE: ADD BRONZE, SILVER, OR GOLD STAGES

   Repeat STEP 3 with:
     - The same BatchName
     - The appropriate registered pipeline name
     - A new StageCode and StageName
     - StageOrder 2, 3, or 4

   Then repeat STEP 4 to get the new BatchStageId.

   Finally, insert the parameters required by that stage
   using STEP 5's pattern. Parameter names depend on the
   actual child pipeline's declared parameters.
   ========================================================= */

