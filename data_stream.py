import logging
import json
from pyspark.sql import SparkSession
from pyspark.sql.types import *
import pyspark.sql.functions as psf



# TODO Create a schema for incoming resources
schema = StructType([
    StructField('crime_id', LongType()),
    StructField('original_crime_type_name', StringType()),
    StructField('report_date', TimestampType()),
    StructField('call_date', TimestampType()),
    StructField('offense_date', TimestampType()),
    StructField('call_time', StringType()),
    StructField('call_date_time', TimestampType()),
    StructField('disposition', StringType()),
    StructField('address', StringType()),
    StructField('city', StringType()),
    StructField('state', StringType()),
    StructField('agency_id', IntegerType()),
    StructField('address_type', StringType()),
    StructField('common_location', StringType()),
])

def run_spark_job(spark):

    # TODO Create Spark Configuration
    # Create Spark configurations with max offset of 200 per trigger
    # set up correct bootstrap server and port
    df = spark \
        .readStream \
        .format('kafka') \
        .option('kafka.bootstrap.servers', 'localhost:9092')\
        .option('subscribe', 'crime.police-event') \
        .option('startingOffsets', 'earliest') \
        .option('maxOffsetPerTrigger', 200) \
        .option('stopGracefullyOnShutdown', 'true')\
        .load()

    # Show schema for the incoming resources for checks
    df.printSchema()

    # TODO extract the correct column from the kafka input resources
    # Take only value and convert it to String
    kafka_df = df.selectExpr("CAST(value AS STRING)")

    service_table = kafka_df\
        .select(psf.from_json(psf.col('value'), schema).alias("DF"))\
        .select("DF.*")
    
    service_table.printSchema()

    # TODO select original_crime_type_name and disposition
    distinct_table = service_table\
                    .select('original_crime_type_name', 'disposition', 'call_date_time')\
                    .distinct()

    # count the number of original crime type
    agg_df = distinct_table \
            .dropna()\
            .select('original_crime_type_name', 'call_date_time') \
            .withWatermark('call_date_time', '60 minutes') \
            .groupBy('original_crime_type_name') \
            .count()
            #.agg({'original_crime_type_name': 'count'}) \
            #.orderBy('count(original_crime_type_name)', ascending=False)

    # TODO Q1. Submit a screen shot of a batch ingestion of the aggregation
    # TODO write output stream
    query = agg_df \
            .writeStream \
            .format('console') \
            .outputMode('Update') \
            .trigger(processingTime="30 seconds") \
            .start()


    # TODO attach a ProgressReporter
    query.awaitTermination()

    # TODO get the right radio code json path
    radio_code_json_filepath = "/home/workspace/radio_code.json"
    radio_code_df = spark.read.json(radio_code_json_filepath)

    # clean up your data so that the column names match on radio_code_df and agg_df
    # we will want to join on the disposition code

    # TODO rename disposition_code column to disposition
    radio_code_df = radio_code_df.withColumnRenamed("disposition_code", "disposition")

    # TODO join on disposition column
    join_query = agg_df.join(radio_code_df, agg_df.disposition == radio_code_df.disposition, how="left")


    join_query.awaitTermination()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # TODO Create Spark in Standalone mode
    spark = SparkSession \
        .builder \
        .config('spark.ui.port', 3000)\
        .master("local[*]") \
        .appName("KafkaSparkStructuredStreaming") \
        .getOrCreate()

    logger.info("Spark started")

    run_spark_job(spark)

    spark.stop()
