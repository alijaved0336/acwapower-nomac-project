from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


def get_delta_connector():
    builder = (
        SparkSession.builder.appName("NomacDeltaLake")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
    )

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    return spark
