
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
        'accounts.csv'
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
        'landing/fraud-events',
        'raw/fraud-events/{LOAD_DATE}',
        'fraud-events.csv'
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
