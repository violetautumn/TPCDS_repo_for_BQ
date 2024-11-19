

import time
from pyspark.sql import SparkSession

spark = SparkSession \
  .builder \
  .master('yarn') \
  .appName('spark-bigquery-demo') \
  .getOrCreate()

start_time = time.time()


filenames = ["income_band", "promotion", "household_demographics", "customer_address", "web_page", "date_dim", "call_center", "catalog_returns", "web_site", "store", "web_returns", "customer_demographics", "catalog_page", "catalog_sales", "item", "customer", "inventory", "ship_mode", "web_sales", "reason", "store_returns", "store_sales", "warehouse", "time_dim"]


for filename in filenames:
  test_table_df = spark.read.format('com.google.cloud.spark.bigquery').option('table', "stock-data-ingess.TPCDS." + filename).load()
  test_table_df.createOrReplaceTempView("table")

  query = """
      SELECT * FROM table;
  """
  result_df = spark.sql(query)
  result_df.show()

  result_df.write.parquet("gs://tpc-ds-data-1tb/" + filename)



end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))





# bq load \
# --source_format=PARQUET \
# TPCDS.store_sales \
# "gs://tpc-ds-data-1tb/store_sales/*.parquet"

