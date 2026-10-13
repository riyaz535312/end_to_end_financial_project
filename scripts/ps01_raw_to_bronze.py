# Cell 1: Set the default Unity Catalog namespace

spark.sql("USE CATALOG finance_dev")
spark.sql("USE SCHEMA bronze")

print("Current catalog: finance_dev")
print("Current schema: bronze")

# Cell 2: Define runtime parameters

dbutils.widgets.text(
    "batch_id", "manual_test_001", "Batch ID"
)

dbutils.widgets.text(
    "source_system", "finance_source", "Source System"
)

dbutils.widgets.text(
    "entity_name", "customers", "Entity Name"
)

dbutils.widgets.text(
    "source_path", "", "ADLS Source Path"
)

dbutils.widgets.dropdown(
    "source_format", "csv",
    ["csv", "json", "parquet"], "Source Format"
)

dbutils.widgets.text(
    "target_table", "customers", "Target Table"
)

dbutils.widgets.dropdown(
    "load_type", "append",
    ["append", "overwrite"], "Load Type"
)

dbutils.widgets.dropdown(
    "schema_mode", "infer",
    ["infer", "all_string"], "Schema Mode"
)

print("Bronze notebook parameters created")

# Cell 3: Read and validate parameters

batch_id = dbutils.widgets.get("batch_id").strip()
source_system = dbutils.widgets.get("source_system").strip()
entity_name = dbutils.widgets.get("entity_name").strip()
source_path = dbutils.widgets.get("source_path").strip()
source_format = dbutils.widgets.get("source_format").strip().lower()
target_table = dbutils.widgets.get("target_table").strip()
load_type = dbutils.widgets.get("load_type").strip().lower()
schema_mode = dbutils.widgets.get("schema_mode").strip().lower()

# Required parameter validation
required_values = {
    "batch_id": batch_id,
    "source_system": source_system,
    "entity_name": entity_name,
    "source_path": source_path,
    "target_table": target_table
}

missing = [
    name for name, value in required_values.items()
    if not value
]

if missing:
    raise ValueError(
        f"Missing required parameters: {', '.join(missing)}"
    )

if source_format not in ["csv", "json", "parquet"]:
    raise ValueError(f"Unsupported format: {source_format}")

if load_type not in ["append", "overwrite"]:
    raise ValueError(f"Unsupported load type: {load_type}")

if schema_mode not in ["infer", "all_string"]:
    raise ValueError(f"Unsupported schema mode: {schema_mode}")

# Restrict the target to a simple table name
if not target_table.replace("_", "").isalnum():
    raise ValueError("Target table must be a simple alphanumeric name with underscores")

target_full_name = f"finance_dev.bronze.{target_table}"

print("Validated parameters")
print(f"Batch ID      : {batch_id}")
print(f"Source system : {source_system}")
print(f"Entity        : {entity_name}")
print(f"Source format : {source_format}")
print(f"Target table  : {target_full_name}")
print(f"Load type     : {load_type}")

# Cell 4: Read raw data into a Spark DataFrame

reader = spark.read

if source_format == "csv":
    if schema_mode == "infer":
        reader = reader.option("inferSchema", "true")
    else:
        reader = reader.option("inferSchema", "false")

    reader = reader.option("header", "true")

elif source_format == "json":
    # Spark infers the JSON schema from the input.
    reader = reader.option("multiLine", "false")

elif source_format == "parquet":
    # Parquet files contain schema information.
    pass

df = reader.format(source_format).load(source_path)

print(f"Source path: {source_path}")
print(f"Source format: {source_format}")

df.printSchema()
display(df.limit(10))

# Cell 5: Basic source validation

if len(df.columns) == 0:
    raise ValueError("Source data has no columns")

source_columns = df.columns

if len(source_columns) != len(set(source_columns)):
    raise ValueError("Source data contains duplicate column names")

print(f"Columns found: {len(source_columns)}")
print(f"Column names: {source_columns}")

source_count = df.count()

if source_count == 0:
    raise ValueError(
        "Source contains no rows. Bronze write has been stopped."
    )

print(f"Source row count: {source_count}")

# Cell 6: Add ingestion metadata

from pyspark.sql.functions import (
    current_timestamp,
    input_file_name,
    lit
)

df_bronze = (
    df
    .withColumn("_batch_id", lit(batch_id))
    .withColumn("_source_system", lit(source_system))
    .withColumn("_entity_name", lit(entity_name))
    .withColumn("_source_file", input_file_name())
    .withColumn("_ingested_at", current_timestamp())
)

display(df_bronze.limit(10))

# Cell 7: Write data to the Bronze Delta table

if load_type == "append":
    (
        df_bronze.write
        .format("delta")
        .mode("append")
        .saveAsTable(target_full_name)
    )

elif load_type == "overwrite":
    (
        df_bronze.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target_full_name)
    )

print(f"Bronze load completed: {target_full_name}")

# Cell 8: Verify the Bronze table

spark.sql(f"""
    SELECT *
    FROM {target_full_name}
    LIMIT 10
""").show(truncate=False)

bronze_count = spark.table(target_full_name).count()

print(f"Target table: {target_full_name}")
print(f"Rows currently in Bronze: {bronze_count}")

spark.sql(f"DESCRIBE TABLE {target_full_name}").show(
    truncate=False
)