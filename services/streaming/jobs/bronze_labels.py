import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder.appName("bronze-labels")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.hadoop.fs.s3a.endpoint", "http://storage:9000")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3a.access.key", "fraudguard")
    .config("spark.hadoop.fs.s3a.secret.key", os.environ["RUSTFS_SECRET_KEY"])
    .getOrCreate()
)

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:19092")
    .option("subscribe", "fraud_labels")
    .option("startingOffsets", "earliest")
    .load()
)

bronze = raw.select(
    F.col("key").cast("string").alias("transaction_id"),
    F.col("value").cast("string").alias("raw_json"),
    "partition",
    "offset",
    F.col("timestamp").alias("kafka_timestamp"),
    F.current_timestamp().alias("ingested_at"),
)

query = (
    bronze.writeStream.format("delta")
    .option("checkpointLocation", "s3a://lakehouse/_checkpoints/bronze_fraud_labels")
    .trigger(availableNow=True)  # process what's there, then stop
    .start("s3a://lakehouse/bronze/fraud_labels")
)
query.awaitTermination()
