from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("KafkaStream") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") \
    .getOrCreate()

schema = StructType([
    StructField("event_id", StringType()),
    StructField("event_type", StringType()),
    StructField("occurred_at", TimestampType()),
    StructField("ingested_at", TimestampType()),
    StructField("session_id", StringType()),
    StructField("customer_id", StringType()),
    StructField("source", StringType()),
    StructField("version", StringType()),
    StructField("event_properties", MapType(StringType(), StringType()))
])

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "mkt.web.clickstream.v1") \
    .load()

parsed = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

parsed.writeStream \
    .format("parquet") \
    .option("path", "lakehouse/clickstream") \
    .option("checkpointLocation", "lakehouse/checkpoints") \
    .outputMode("append") \
    .start() \
    .awaitTermination()