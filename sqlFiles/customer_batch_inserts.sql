/* Register the batch */

IF NOT EXISTS
(
    SELECT 1
    FROM orchestrator.Batch
    WHERE BatchName = 'FIN_CUSTOMER_LOAD'
)
BEGIN
    INSERT INTO orchestrator.Batch
        (BatchName, Description)
    VALUES
        ('FIN_CUSTOMER_LOAD',
         'Copies customer files from landing to raw');
END;
GO


/* Register the generic child pipeline */

IF NOT EXISTS
(
    SELECT 1
    FROM orchestrator.Pipeline
    WHERE PipelineCode = 'COPY_LANDING_TO_RAW'
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
        'Generic Binary file copy from landing to raw'
    );
END;
GO


/* Create the first pipeline invocation */

INSERT INTO orchestrator.BatchStage
(
    BatchId,
    PipelineId,
    StageCode,
    StageName,
    StageOrder
)
SELECT
    b.BatchId,
    p.PipelineId,
    'LANDING_TO_RAW',
    'Copy customer file',
    1
FROM orchestrator.Batch b
CROSS JOIN orchestrator.Pipeline p
WHERE b.BatchName = 'FIN_CUSTOMER_LOAD'
  AND p.PipelineCode = 'COPY_LANDING_TO_RAW'
  AND NOT EXISTS
  (
      SELECT 1
      FROM orchestrator.BatchStage bs
      WHERE bs.BatchId = b.BatchId
        AND bs.StageOrder = 1
  );
GO


DECLARE @BatchStageId INT;

SELECT @BatchStageId = bs.BatchStageId
FROM orchestrator.BatchStage bs
JOIN orchestrator.Batch b
    ON b.BatchId = bs.BatchId
WHERE b.BatchName = 'FIN_CUSTOMER_LOAD'
  AND bs.StageCode = 'LANDING_TO_RAW'
  AND bs.StageOrder = 1;


/* Insert the parameters only if they don't already exist */

INSERT INTO orchestrator.PipelineParameter
(
    BatchStageId,
    ParameterName,
    ParameterValue,
    DataType,
    IsSensitive
)
SELECT
    @BatchStageId,
    v.ParameterName,
    v.ParameterValue,
    'string',
    0
FROM
(
    VALUES
    (
        'plp_source_container_name',
        N'finance-lake'
    ),
    (
        'plp_target_container_name',
        N'finance-lake'
    ),
    (
        'plp_source_path',
        N'landing/customer'
    ),
    (
        'plp_sink_path',
        N'raw/customer/{LOAD_DATE}'
    ),
    (
        'plp_source_filename',
        N'customer.csv'
    ),
    (
        'plp_sink_filename',
        N'customer.csv'
    )
) v(ParameterName, ParameterValue)
WHERE @BatchStageId IS NOT NULL
  AND NOT EXISTS
  (
      SELECT 1
      FROM orchestrator.PipelineParameter pp
      WHERE pp.BatchStageId = @BatchStageId
        AND pp.ParameterName = v.ParameterName
  );
GO


SELECT
    b.BatchName,
    bs.BatchStageId,
    bs.StageCode,
    bs.StageName,
    bs.StageOrder,
    p.PipelineCode,
    p.ADFPipelineName,
    bs.IsEnabled,
    bs.IsRequired
FROM orchestrator.BatchStage bs
JOIN orchestrator.Batch b
    ON b.BatchId = bs.BatchId
JOIN orchestrator.Pipeline p
    ON p.PipelineId = bs.PipelineId
ORDER BY b.BatchName, bs.StageOrder;

SELECT
    b.BatchName,
    bs.StageCode,
    pp.ParameterName,
    pp.ParameterValue,
    pp.DataType
FROM orchestrator.PipelineParameter pp
JOIN orchestrator.BatchStage bs
    ON bs.BatchStageId = pp.BatchStageId
JOIN orchestrator.Batch b
    ON b.BatchId = bs.BatchId
WHERE b.BatchName = 'FIN_CUSTOMER_LOAD'
ORDER BY pp.ParameterName;

SELECT
    b.BatchName,
    bs.BatchStageId,
    bs.StageOrder,
    p.PipelineCode,
    p.ADFPipelineName,
    pp.ParameterName,
    pp.ParameterValue
FROM orchestrator.Batch b
JOIN orchestrator.BatchStage bs
    ON bs.BatchId = b.BatchId
JOIN orchestrator.Pipeline p
    ON p.PipelineId = bs.PipelineId
JOIN orchestrator.PipelineParameter pp
    ON pp.BatchStageId = bs.BatchStageId
WHERE b.BatchName = 'FIN_CUSTOMER_LOAD'
  AND b.IsActive = 1
  AND bs.IsEnabled = 1
  AND p.IsActive = 1
ORDER BY bs.StageOrder, pp.ParameterName;


