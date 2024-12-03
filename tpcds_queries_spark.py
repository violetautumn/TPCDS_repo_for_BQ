import time
from pyspark.sql.types import DecimalType
from pyspark.sql.functions import col
from pyspark.sql import SparkSession

spark = SparkSession \
  .builder \
  .master('yarn') \
  .appName('spark-bigquery-demo') \
  .getOrCreate()




## Query 1


start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")



query = """

    WITH customer_total_return 
         AS (SELECT sr_customer_sk     AS ctr_customer_sk, 
                    sr_store_sk        AS ctr_store_sk, 
                    Sum(sr_return_amt) AS ctr_total_return 
             FROM   store_returns, 
                    date_dim 
             WHERE  sr_returned_date_sk = d_date_sk 
                    AND d_year = 2001 
             GROUP  BY sr_customer_sk, 
                       sr_store_sk) 
    SELECT c_customer_id 
    FROM   customer_total_return ctr1, 
           store, 
           customer 
    WHERE  ctr1.ctr_total_return > (SELECT Avg(ctr_total_return) * 1.2 
                                    FROM   customer_total_return ctr2 
                                    WHERE  ctr1.ctr_store_sk = ctr2.ctr_store_sk) 
           AND s_store_sk = ctr1.ctr_store_sk 
           AND s_state = 'TN' 
           AND ctr1.ctr_customer_sk = c_customer_sk 
    ORDER  BY c_customer_id;


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_01_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))






## Query 2

start_time = time.time()
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

    WITH wscs 
         AS (SELECT sold_date_sk, 
                    sales_price 
             FROM   (SELECT ws_sold_date_sk    sold_date_sk, 
                            ws_ext_sales_price sales_price 
                     FROM   web_sales) 
             UNION ALL 
             (SELECT cs_sold_date_sk    sold_date_sk, 
                     cs_ext_sales_price sales_price 
              FROM   catalog_sales)), 
         wswscs 
         AS (SELECT d_week_seq, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Sunday' ) THEN sales_price 
                          ELSE NULL 
                        END) sun_sales, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Monday' ) THEN sales_price 
                          ELSE NULL 
                        END) mon_sales, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Tuesday' ) THEN sales_price 
                          ELSE NULL 
                        END) tue_sales, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Wednesday' ) THEN sales_price 
                          ELSE NULL 
                        END) wed_sales, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Thursday' ) THEN sales_price 
                          ELSE NULL 
                        END) thu_sales, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Friday' ) THEN sales_price 
                          ELSE NULL 
                        END) fri_sales, 
                    Sum(CASE 
                          WHEN ( d_day_name = 'Saturday' ) THEN sales_price 
                          ELSE NULL 
                        END) sat_sales 
             FROM   wscs, 
                    date_dim 
             WHERE  d_date_sk = sold_date_sk 
             GROUP  BY d_week_seq) 
    SELECT d_week_seq1, 
           Round(sun_sales1 / sun_sales2, 2), 
           Round(mon_sales1 / mon_sales2, 2), 
           Round(tue_sales1 / tue_sales2, 2), 
           Round(wed_sales1 / wed_sales2, 2), 
           Round(thu_sales1 / thu_sales2, 2), 
           Round(fri_sales1 / fri_sales2, 2), 
           Round(sat_sales1 / sat_sales2, 2) 
    FROM   (SELECT wswscs.d_week_seq d_week_seq1, 
                   sun_sales         sun_sales1, 
                   mon_sales         mon_sales1, 
                   tue_sales         tue_sales1, 
                   wed_sales         wed_sales1, 
                   thu_sales         thu_sales1, 
                   fri_sales         fri_sales1, 
                   sat_sales         sat_sales1 
            FROM   wswscs, 
                   date_dim 
            WHERE  date_dim.d_week_seq = wswscs.d_week_seq 
                   AND d_year = 1998) y, 
           (SELECT wswscs.d_week_seq d_week_seq2, 
                   sun_sales         sun_sales2, 
                   mon_sales         mon_sales2, 
                   tue_sales         tue_sales2, 
                   wed_sales         wed_sales2, 
                   thu_sales         thu_sales2, 
                   fri_sales         fri_sales2, 
                   sat_sales         sat_sales2 
            FROM   wswscs, 
                   date_dim 
            WHERE  date_dim.d_week_seq = wswscs.d_week_seq 
                   AND d_year = 1998 + 1) z 
    WHERE  d_week_seq1 = d_week_seq2 - 53 
    ORDER  BY d_week_seq1;


"""
result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_02_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))








## Query 3

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")

query = """

    SELECT dt.d_year, 
           item.i_brand_id          brand_id, 
           item.i_brand             brand, 
           Sum(ss_ext_discount_amt) sum_agg 
    FROM   date_dim dt, 
           store_sales, 
           item 
    WHERE  dt.d_date_sk = store_sales.ss_sold_date_sk 
           AND store_sales.ss_item_sk = item.i_item_sk 
           AND item.i_manufact_id = 427 
           AND dt.d_moy = 11 
    GROUP  BY dt.d_year, 
              item.i_brand, 
              item.i_brand_id 
    ORDER  BY dt.d_year, 
              sum_agg DESC, 
              brand_id;

"""
result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_03_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))








## Query 4

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")

query = """

WITH year_total 
     AS (SELECT c_customer_id                       customer_id, 
                c_first_name                        customer_first_name, 
                c_last_name                         customer_last_name, 
                c_preferred_cust_flag               customer_preferred_cust_flag 
                , 
                c_birth_country 
                customer_birth_country, 
                c_login                             customer_login, 
                c_email_address                     customer_email_address, 
                d_year                              dyear, 
                Sum(( ( ss_ext_list_price - ss_ext_wholesale_cost 
                        - ss_ext_discount_amt 
                      ) 
                      + 
                          ss_ext_sales_price ) / 2) year_total, 
                's'                                 sale_type 
         FROM   customer, 
                store_sales, 
                date_dim 
         WHERE  c_customer_sk = ss_customer_sk 
                AND ss_sold_date_sk = d_date_sk 
         GROUP  BY c_customer_id, 
                   c_first_name, 
                   c_last_name, 
                   c_preferred_cust_flag, 
                   c_birth_country, 
                   c_login, 
                   c_email_address, 
                   d_year 
         UNION ALL 
         SELECT c_customer_id                             customer_id, 
                c_first_name                              customer_first_name, 
                c_last_name                               customer_last_name, 
                c_preferred_cust_flag 
                customer_preferred_cust_flag, 
                c_birth_country                           customer_birth_country 
                , 
                c_login 
                customer_login, 
                c_email_address                           customer_email_address 
                , 
                d_year                                    dyear 
                , 
                Sum(( ( ( cs_ext_list_price 
                          - cs_ext_wholesale_cost 
                          - cs_ext_discount_amt 
                        ) + 
                              cs_ext_sales_price ) / 2 )) year_total, 
                'c'                                       sale_type 
         FROM   customer, 
                catalog_sales, 
                date_dim 
         WHERE  c_customer_sk = cs_bill_customer_sk 
                AND cs_sold_date_sk = d_date_sk 
         GROUP  BY c_customer_id, 
                   c_first_name, 
                   c_last_name, 
                   c_preferred_cust_flag, 
                   c_birth_country, 
                   c_login, 
                   c_email_address, 
                   d_year 
         UNION ALL 
         SELECT c_customer_id                             customer_id, 
                c_first_name                              customer_first_name, 
                c_last_name                               customer_last_name, 
                c_preferred_cust_flag 
                customer_preferred_cust_flag, 
                c_birth_country                           customer_birth_country 
                , 
                c_login 
                customer_login, 
                c_email_address                           customer_email_address 
                , 
                d_year                                    dyear 
                , 
                Sum(( ( ( ws_ext_list_price 
                          - ws_ext_wholesale_cost 
                          - ws_ext_discount_amt 
                        ) + 
                              ws_ext_sales_price ) / 2 )) year_total, 
                'w'                                       sale_type 
         FROM   customer, 
                web_sales, 
                date_dim 
         WHERE  c_customer_sk = ws_bill_customer_sk 
                AND ws_sold_date_sk = d_date_sk 
         GROUP  BY c_customer_id, 
                   c_first_name, 
                   c_last_name, 
                   c_preferred_cust_flag, 
                   c_birth_country, 
                   c_login, 
                   c_email_address, 
                   d_year) 
SELECT t_s_secyear.customer_id, 
               t_s_secyear.customer_first_name, 
               t_s_secyear.customer_last_name, 
               t_s_secyear.customer_preferred_cust_flag 
FROM   year_total t_s_firstyear, 
       year_total t_s_secyear, 
       year_total t_c_firstyear, 
       year_total t_c_secyear, 
       year_total t_w_firstyear, 
       year_total t_w_secyear 
WHERE  t_s_secyear.customer_id = t_s_firstyear.customer_id 
       AND t_s_firstyear.customer_id = t_c_secyear.customer_id 
       AND t_s_firstyear.customer_id = t_c_firstyear.customer_id 
       AND t_s_firstyear.customer_id = t_w_firstyear.customer_id 
       AND t_s_firstyear.customer_id = t_w_secyear.customer_id 
       AND t_s_firstyear.sale_type = 's' 
       AND t_c_firstyear.sale_type = 'c' 
       AND t_w_firstyear.sale_type = 'w' 
       AND t_s_secyear.sale_type = 's' 
       AND t_c_secyear.sale_type = 'c' 
       AND t_w_secyear.sale_type = 'w' 
       AND t_s_firstyear.dyear = 2001 
       AND t_s_secyear.dyear = 2001 + 1 
       AND t_c_firstyear.dyear = 2001 
       AND t_c_secyear.dyear = 2001 + 1 
       AND t_w_firstyear.dyear = 2001 
       AND t_w_secyear.dyear = 2001 + 1 
       AND t_s_firstyear.year_total > 0 
       AND t_c_firstyear.year_total > 0 
       AND t_w_firstyear.year_total > 0 
       AND CASE 
             WHEN t_c_firstyear.year_total > 0 THEN t_c_secyear.year_total / 
                                                    t_c_firstyear.year_total 
             ELSE NULL 
           END > CASE 
                   WHEN t_s_firstyear.year_total > 0 THEN 
                   t_s_secyear.year_total / 
                   t_s_firstyear.year_total 
                   ELSE NULL 
                 END 
       AND CASE 
             WHEN t_c_firstyear.year_total > 0 THEN t_c_secyear.year_total / 
                                                    t_c_firstyear.year_total 
             ELSE NULL 
           END > CASE 
                   WHEN t_w_firstyear.year_total > 0 THEN 
                   t_w_secyear.year_total / 
                   t_w_firstyear.year_total 
                   ELSE NULL 
                 END 
ORDER  BY t_s_secyear.customer_id, 
          t_s_secyear.customer_first_name, 
          t_s_secyear.customer_last_name, 
          t_s_secyear.customer_preferred_cust_flag;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_04_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 5

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
catalog_pagedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_page")
catalog_pagedf.createOrReplaceTempView("catalog_page")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
catalog_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_returns")
catalog_returnsdf.createOrReplaceTempView("catalog_returns")
web_sitedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_site")
web_sitedf.createOrReplaceTempView("web_site")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
web_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_returns")
web_returnsdf.createOrReplaceTempView("web_returns")


query = """

WITH ssr AS 
( 
         SELECT   s_store_id, 
                  Sum(sales_price) AS sales, 
                  Sum(profit)      AS profit, 
                  Sum(return_amt)  AS returns1, 
                  Sum(net_loss)    AS profit_loss 
         FROM     ( 
                         SELECT ss_store_sk             AS store_sk, 
                                ss_sold_date_sk         AS date_sk, 
                                ss_ext_sales_price      AS sales_price, 
                                ss_net_profit           AS profit, 
                                Cast(0 AS NUMERIC) AS return_amt, 
                                Cast(0 AS NUMERIC) AS net_loss 
                         FROM   store_sales 
                         UNION ALL 
                         SELECT sr_store_sk             AS store_sk, 
                                sr_returned_date_sk     AS date_sk, 
                                Cast(0 AS NUMERIC) AS sales_price, 
                                Cast(0 AS NUMERIC) AS profit, 
                                sr_return_amt           AS return_amt, 
                                sr_net_loss             AS net_loss 
                         FROM   store_returns ) salesreturns, 
                  date_dim, 
                  store 
         WHERE    date_sk = d_date_sk 
         AND      d_date BETWEEN Cast('2002-08-22' AS DATE) AND      ( 
                           Cast('2002-08-22' AS DATE) + INTERVAL '14' day) 
         AND      store_sk = s_store_sk 
         GROUP BY s_store_id) , csr AS 
( 
         SELECT   cp_catalog_page_id, 
                  sum(sales_price) AS sales, 
                  sum(profit)      AS profit, 
                  sum(return_amt)  AS returns1, 
                  sum(net_loss)    AS profit_loss 
         FROM     ( 
                         SELECT cs_catalog_page_sk      AS page_sk, 
                                cs_sold_date_sk         AS date_sk, 
                                cs_ext_sales_price      AS sales_price, 
                                cs_net_profit           AS profit, 
                                cast(0 AS NUMERIC) AS return_amt, 
                                cast(0 AS NUMERIC) AS net_loss 
                         FROM   catalog_sales 
                         UNION ALL 
                         SELECT cr_catalog_page_sk      AS page_sk, 
                                cr_returned_date_sk     AS date_sk, 
                                cast(0 AS NUMERIC) AS sales_price, 
                                cast(0 AS NUMERIC) AS profit, 
                                cr_return_amount        AS return_amt, 
                                cr_net_loss             AS net_loss 
                         FROM   catalog_returns ) salesreturns, 
                  date_dim, 
                  catalog_page 
         WHERE    date_sk = d_date_sk 
         AND      d_date BETWEEN cast('2002-08-22' AS date) AND      ( 
                           cast('2002-08-22' AS date) + INTERVAL '14' day) 
         AND      page_sk = cp_catalog_page_sk 
         GROUP BY cp_catalog_page_id) , wsr AS 
( 
         SELECT   web_site_id, 
                  sum(sales_price) AS sales, 
                  sum(profit)      AS profit, 
                  sum(return_amt)  AS returns1, 
                  sum(net_loss)    AS profit_loss 
         FROM     ( 
                         SELECT ws_web_site_sk          AS wsr_web_site_sk, 
                                ws_sold_date_sk         AS date_sk, 
                                ws_ext_sales_price      AS sales_price, 
                                ws_net_profit           AS profit, 
                                cast(0 AS NUMERIC) AS return_amt, 
                                cast(0 AS NUMERIC) AS net_loss 
                         FROM   web_sales 
                         UNION ALL 
                         SELECT          ws_web_site_sk          AS wsr_web_site_sk, 
                                         wr_returned_date_sk     AS date_sk, 
                                         cast(0 AS NUMERIC) AS sales_price, 
                                         cast(0 AS NUMERIC) AS profit, 
                                         wr_return_amt           AS return_amt, 
                                         wr_net_loss             AS net_loss 
                         FROM            web_returns 
                         LEFT OUTER JOIN web_sales 
                         ON              ( 
                                                         wr_item_sk = ws_item_sk 
                                         AND             wr_order_number = ws_order_number) ) salesreturns,
                  date_dim, 
                  web_site 
         WHERE    date_sk = d_date_sk 
         AND      d_date BETWEEN cast('2002-08-22' AS date) AND      ( 
                           cast('2002-08-22' AS date) + INTERVAL '14' day) 
         AND      wsr_web_site_sk = web_site_sk 
         GROUP BY web_site_id) 
SELECT 
         channel , 
         id , 
         sum(sales)   AS sales , 
         sum(returns1) AS returns1 , 
         sum(profit)  AS profit 
FROM     ( 
                SELECT 'store channel' AS channel , 
                       'store' 
                              || s_store_id AS id , 
                       sales , 
                       returns1 , 
                       (profit - profit_loss) AS profit 
                FROM   ssr 
                UNION ALL 
                SELECT 'catalog channel' AS channel , 
                       'catalog_page' 
                              || cp_catalog_page_id AS id , 
                       sales , 
                       returns1 , 
                       (profit - profit_loss) AS profit 
                FROM   csr 
                UNION ALL 
                SELECT 'web channel' AS channel , 
                       'web_site' 
                              || web_site_id AS id , 
                       sales , 
                       returns1 , 
                       (profit - profit_loss) AS profit 
                FROM   wsr ) x 
GROUP BY rollup (channel, id) 
ORDER BY channel , 
         id;

"""
result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_05_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 6

start_time = time.time()
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")

query = """

    SELECT a.ca_state state, 
                   Count(*)   cnt 
    FROM   customer_address a, 
           customer c, 
           store_sales s, 
           date_dim d, 
           item i 
    WHERE  a.ca_address_sk = c.c_current_addr_sk 
           AND c.c_customer_sk = s.ss_customer_sk 
           AND s.ss_sold_date_sk = d.d_date_sk 
           AND s.ss_item_sk = i.i_item_sk 
           AND d.d_month_seq = (SELECT DISTINCT ( d_month_seq ) 
                                FROM   date_dim 
                                WHERE  d_year = 1998 
                                       AND d_moy = 7) 
           AND i.i_current_price > 1.2 * (SELECT Avg(j.i_current_price) 
                                          FROM   item j 
                                          WHERE  j.i_category = i.i_category) 
    GROUP  BY a.ca_state 
    HAVING Count(*) >= 10 
    ORDER  BY cnt;

"""
result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_06_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))









## Query 7

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
promotiondf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/promotion")

store_salesdf.createOrReplaceTempView("store_sales")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf.createOrReplaceTempView("item")
promotiondf.createOrReplaceTempView("promotion")
query = """
    SELECT i_item_id, 
                   Avg(ss_quantity)    agg1, 
                   Avg(ss_list_price)  agg2, 
                   Avg(ss_coupon_amt)  agg3, 
                   Avg(ss_sales_price) agg4 
    FROM   store_sales, 
           customer_demographics, 
           date_dim, 
           item, 
           promotion 
    WHERE  ss_sold_date_sk = d_date_sk 
           AND ss_item_sk = i_item_sk 
           AND ss_cdemo_sk = cd_demo_sk 
           AND ss_promo_sk = p_promo_sk 
           AND cd_gender = 'F' 
           AND cd_marital_status = 'W' 
           AND cd_education_status = '2 yr Degree' 
           AND ( p_channel_email = 'N' 
                  OR p_channel_event = 'N' ) 
           AND d_year = 1998 
    GROUP  BY i_item_id 
    ORDER  BY i_item_id;
"""
result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_07_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 8

start_time = time.time()
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")

query = """

SELECT s_store_name, 
               Sum(ss_net_profit) 
FROM   store_sales, 
       date_dim, 
       store, 
       (SELECT ca_zip 
        FROM   (SELECT Substr(ca_zip, 1, 5) ca_zip 
                FROM   customer_address 
                WHERE  Substr(ca_zip, 1, 5) IN ( '67436', '26121', '38443', 
                                                 '63157', 
                                                 '68856', '19485', '86425', 
                                                 '26741', 
                                                 '70991', '60899', '63573', 
                                                 '47556', 
                                                 '56193', '93314', '87827', 
                                                 '62017', 
                                                 '85067', '95390', '48091', 
                                                 '10261', 
                                                 '81845', '41790', '42853', 
                                                 '24675', 
                                                 '12840', '60065', '84430', 
                                                 '57451', 
                                                 '24021', '91735', '75335', 
                                                 '71935', 
                                                 '34482', '56943', '70695', 
                                                 '52147', 
                                                 '56251', '28411', '86653', 
                                                 '23005', 
                                                 '22478', '29031', '34398', 
                                                 '15365', 
                                                 '42460', '33337', '59433', 
                                                 '73943', 
                                                 '72477', '74081', '74430', 
                                                 '64605', 
                                                 '39006', '11226', '49057', 
                                                 '97308', 
                                                 '42663', '18187', '19768', 
                                                 '43454', 
                                                 '32147', '76637', '51975', 
                                                 '11181', 
                                                 '45630', '33129', '45995', 
                                                 '64386', 
                                                 '55522', '26697', '20963', 
                                                 '35154', 
                                                 '64587', '49752', '66386', 
                                                 '30586', 
                                                 '59286', '13177', '66646', 
                                                 '84195', 
                                                 '74316', '36853', '32927', 
                                                 '12469', 
                                                 '11904', '36269', '17724', 
                                                 '55346', 
                                                 '12595', '53988', '65439', 
                                                 '28015', 
                                                 '63268', '73590', '29216', 
                                                 '82575', 
                                                 '69267', '13805', '91678', 
                                                 '79460', 
                                                 '94152', '14961', '15419', 
                                                 '48277', 
                                                 '62588', '55493', '28360', 
                                                 '14152', 
                                                 '55225', '18007', '53705', 
                                                 '56573', 
                                                 '80245', '71769', '57348', 
                                                 '36845', 
                                                 '13039', '17270', '22363', 
                                                 '83474', 
                                                 '25294', '43269', '77666', 
                                                 '15488', 
                                                 '99146', '64441', '43338', 
                                                 '38736', 
                                                 '62754', '48556', '86057', 
                                                 '23090', 
                                                 '38114', '66061', '18910', 
                                                 '84385', 
                                                 '23600', '19975', '27883', 
                                                 '65719', 
                                                 '19933', '32085', '49731', 
                                                 '40473', 
                                                 '27190', '46192', '23949', 
                                                 '44738', 
                                                 '12436', '64794', '68741', 
                                                 '15333', 
                                                 '24282', '49085', '31844', 
                                                 '71156', 
                                                 '48441', '17100', '98207', 
                                                 '44982', 
                                                 '20277', '71496', '96299', 
                                                 '37583', 
                                                 '22206', '89174', '30589', 
                                                 '61924', 
                                                 '53079', '10976', '13104', 
                                                 '42794', 
                                                 '54772', '15809', '56434', 
                                                 '39975', 
                                                 '13874', '30753', '77598', 
                                                 '78229', 
                                                 '59478', '12345', '55547', 
                                                 '57422', 
                                                 '42600', '79444', '29074', 
                                                 '29752', 
                                                 '21676', '32096', '43044', 
                                                 '39383', 
                                                 '37296', '36295', '63077', 
                                                 '16572', 
                                                 '31275', '18701', '40197', 
                                                 '48242', 
                                                 '27219', '49865', '84175', 
                                                 '30446', 
                                                 '25165', '13807', '72142', 
                                                 '70499', 
                                                 '70464', '71429', '18111', 
                                                 '70857', 
                                                 '29545', '36425', '52706', 
                                                 '36194', 
                                                 '42963', '75068', '47921', 
                                                 '74763', 
                                                 '90990', '89456', '62073', 
                                                 '88397', 
                                                 '73963', '75885', '62657', 
                                                 '12530', 
                                                 '81146', '57434', '25099', 
                                                 '41429', 
                                                 '98441', '48713', '52552', 
                                                 '31667', 
                                                 '14072', '13903', '44709', 
                                                 '85429', 
                                                 '58017', '38295', '44875', 
                                                 '73541', 
                                                 '30091', '12707', '23762', 
                                                 '62258', 
                                                 '33247', '78722', '77431', 
                                                 '14510', 
                                                 '35656', '72428', '92082', 
                                                 '35267', 
                                                 '43759', '24354', '90952', 
                                                 '11512', 
                                                 '21242', '22579', '56114', 
                                                 '32339', 
                                                 '52282', '41791', '24484', 
                                                 '95020', 
                                                 '28408', '99710', '11899', 
                                                 '43344', 
                                                 '72915', '27644', '62708', 
                                                 '74479', 
                                                 '17177', '32619', '12351', 
                                                 '91339', 
                                                 '31169', '57081', '53522', 
                                                 '16712', 
                                                 '34419', '71779', '44187', 
                                                 '46206', 
                                                 '96099', '61910', '53664', 
                                                 '12295', 
                                                 '31837', '33096', '10813', 
                                                 '63048', 
                                                 '31732', '79118', '73084', 
                                                 '72783', 
                                                 '84952', '46965', '77956', 
                                                 '39815', 
                                                 '32311', '75329', '48156', 
                                                 '30826', 
                                                 '49661', '13736', '92076', 
                                                 '74865', 
                                                 '88149', '92397', '52777', 
                                                 '68453', 
                                                 '32012', '21222', '52721', 
                                                 '24626', 
                                                 '18210', '42177', '91791', 
                                                 '75251', 
                                                 '82075', '44372', '45542', 
                                                 '20609', 
                                                 '60115', '17362', '22750', 
                                                 '90434', 
                                                 '31852', '54071', '33762', 
                                                 '14705', 
                                                 '40718', '56433', '30996', 
                                                 '40657', 
                                                 '49056', '23585', '66455', 
                                                 '41021', 
                                                 '74736', '72151', '37007', 
                                                 '21729', 
                                                 '60177', '84558', '59027', 
                                                 '93855', 
                                                 '60022', '86443', '19541', 
                                                 '86886', 
                                                 '30532', '39062', '48532', 
                                                 '34713', 
                                                 '52077', '22564', '64638', 
                                                 '15273', 
                                                 '31677', '36138', '62367', 
                                                 '60261', 
                                                 '80213', '42818', '25113', 
                                                 '72378', 
                                                 '69802', '69096', '55443', 
                                                 '28820', 
                                                 '13848', '78258', '37490', 
                                                 '30556', 
                                                 '77380', '28447', '44550', 
                                                 '26791', 
                                                 '70609', '82182', '33306', 
                                                 '43224', 
                                                 '22322', '86959', '68519', 
                                                 '14308', 
                                                 '46501', '81131', '34056', 
                                                 '61991', 
                                                 '19896', '87804', '65774', 
                                                 '92564' ) 
                INTERSECT DISTINCT
                SELECT ca_zip 
                FROM   (SELECT Substr(ca_zip, 1, 5) ca_zip, 
                               Count(*)             cnt 
                        FROM   customer_address, 
                               customer 
                        WHERE  ca_address_sk = c_current_addr_sk 
                               AND c_preferred_cust_flag = 'Y' 
                        GROUP  BY ca_zip 
                        HAVING Count(*) > 10)A1)A2) V1 
WHERE  ss_store_sk = s_store_sk 
       AND ss_sold_date_sk = d_date_sk 
       AND d_qoy = 2 
       AND d_year = 2000 
       AND ( Substr(s_zip, 1, 2) = Substr(V1.ca_zip, 1, 2) ) 
GROUP  BY s_store_name 
ORDER  BY s_store_name; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_08_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))









## Query 9

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
reasondf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/reason")
reasondf.createOrReplaceTempView("reason")


query = """

SELECT CASE 
         WHEN (SELECT Count(*) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 1 AND 20) > 3672 THEN 
         (SELECT Avg(ss_ext_list_price) 
          FROM   store_sales 
          WHERE 
         ss_quantity BETWEEN 1 AND 20) 
         ELSE (SELECT Avg(ss_net_profit) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 1 AND 20) 
       END bucket1, 
       CASE 
         WHEN (SELECT Count(*) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 21 AND 40) > 3392 THEN 
         (SELECT Avg(ss_ext_list_price) 
          FROM   store_sales 
          WHERE 
         ss_quantity BETWEEN 21 AND 40) 
         ELSE (SELECT Avg(ss_net_profit) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 21 AND 40) 
       END bucket2, 
       CASE 
         WHEN (SELECT Count(*) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 41 AND 60) > 32784 THEN 
         (SELECT Avg(ss_ext_list_price) 
          FROM   store_sales 
          WHERE 
         ss_quantity BETWEEN 41 AND 60) 
         ELSE (SELECT Avg(ss_net_profit) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 41 AND 60) 
       END bucket3, 
       CASE 
         WHEN (SELECT Count(*) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 61 AND 80) > 26032 THEN 
         (SELECT Avg(ss_ext_list_price) 
          FROM   store_sales 
          WHERE 
         ss_quantity BETWEEN 61 AND 80) 
         ELSE (SELECT Avg(ss_net_profit) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 61 AND 80) 
       END bucket4, 
       CASE 
         WHEN (SELECT Count(*) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 81 AND 100) > 23982 THEN 
         (SELECT Avg(ss_ext_list_price) 
          FROM   store_sales 
          WHERE 
         ss_quantity BETWEEN 81 AND 100) 
         ELSE (SELECT Avg(ss_net_profit) 
               FROM   store_sales 
               WHERE  ss_quantity BETWEEN 81 AND 100) 
       END bucket5 
FROM   reason 
WHERE  r_reason_sk = 1; 


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_09_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))







## Query 10

start_time = time.time()
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT cd_gender, 
               cd_marital_status, 
               cd_education_status, 
               Count(*) cnt1, 
               cd_purchase_estimate, 
               Count(*) cnt2, 
               cd_credit_rating, 
               Count(*) cnt3, 
               cd_dep_count, 
               Count(*) cnt4, 
               cd_dep_employed_count, 
               Count(*) cnt5, 
               cd_dep_college_count, 
               Count(*) cnt6 
FROM   customer c, 
       customer_address ca, 
       customer_demographics 
WHERE  c.c_current_addr_sk = ca.ca_address_sk 
       AND ca_county IN ( 'Lycoming County', 'Sheridan County', 
                          'Kandiyohi County', 
                          'Pike County', 
                                           'Greene County' ) 
       AND cd_demo_sk = c.c_current_cdemo_sk 
       AND EXISTS (SELECT * 
                   FROM   store_sales, 
                          date_dim 
                   WHERE  c.c_customer_sk = ss_customer_sk 
                          AND ss_sold_date_sk = d_date_sk 
                          AND d_year = 2002 
                          AND d_moy BETWEEN 4 AND 4 + 3) 
       AND ( EXISTS (SELECT * 
                     FROM   web_sales, 
                            date_dim 
                     WHERE  c.c_customer_sk = ws_bill_customer_sk 
                            AND ws_sold_date_sk = d_date_sk 
                            AND d_year = 2002 
                            AND d_moy BETWEEN 4 AND 4 + 3) 
              OR EXISTS (SELECT * 
                         FROM   catalog_sales, 
                                date_dim 
                         WHERE  c.c_customer_sk = cs_ship_customer_sk 
                                AND cs_sold_date_sk = d_date_sk 
                                AND d_year = 2002 
                                AND d_moy BETWEEN 4 AND 4 + 3) ) 
GROUP  BY cd_gender, 
          cd_marital_status, 
          cd_education_status, 
          cd_purchase_estimate, 
          cd_credit_rating, 
          cd_dep_count, 
          cd_dep_employed_count, 
          cd_dep_college_count 
ORDER  BY cd_gender, 
          cd_marital_status, 
          cd_education_status, 
          cd_purchase_estimate, 
          cd_credit_rating, 
          cd_dep_count, 
          cd_dep_employed_count, 
          cd_dep_college_count;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_10_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))










## Query 11

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

WITH year_total 
     AS (SELECT c_customer_id                                customer_id, 
                c_first_name                                 customer_first_name 
                , 
                c_last_name 
                customer_last_name, 
                c_preferred_cust_flag 
                   customer_preferred_cust_flag 
                    , 
                c_birth_country 
                    customer_birth_country, 
                c_login                                      customer_login, 
                c_email_address 
                customer_email_address, 
                d_year                                       dyear, 
                Sum(ss_ext_list_price - ss_ext_discount_amt) year_total, 
                's'                                          sale_type 
         FROM   customer, 
                store_sales, 
                date_dim 
         WHERE  c_customer_sk = ss_customer_sk 
                AND ss_sold_date_sk = d_date_sk 
         GROUP  BY c_customer_id, 
                   c_first_name, 
                   c_last_name, 
                   c_preferred_cust_flag, 
                   c_birth_country, 
                   c_login, 
                   c_email_address, 
                   d_year 
         UNION ALL 
         SELECT c_customer_id                                customer_id, 
                c_first_name                                 customer_first_name 
                , 
                c_last_name 
                customer_last_name, 
                c_preferred_cust_flag 
                customer_preferred_cust_flag 
                , 
                c_birth_country 
                customer_birth_country, 
                c_login                                      customer_login, 
                c_email_address 
                customer_email_address, 
                d_year                                       dyear, 
                Sum(ws_ext_list_price - ws_ext_discount_amt) year_total, 
                'w'                                          sale_type 
         FROM   customer, 
                web_sales, 
                date_dim 
         WHERE  c_customer_sk = ws_bill_customer_sk 
                AND ws_sold_date_sk = d_date_sk 
         GROUP  BY c_customer_id, 
                   c_first_name, 
                   c_last_name, 
                   c_preferred_cust_flag, 
                   c_birth_country, 
                   c_login, 
                   c_email_address, 
                   d_year) 
SELECT t_s_secyear.customer_id, 
               t_s_secyear.customer_first_name, 
               t_s_secyear.customer_last_name, 
               t_s_secyear.customer_birth_country 
FROM   year_total t_s_firstyear, 
       year_total t_s_secyear, 
       year_total t_w_firstyear, 
       year_total t_w_secyear 
WHERE  t_s_secyear.customer_id = t_s_firstyear.customer_id 
       AND t_s_firstyear.customer_id = t_w_secyear.customer_id 
       AND t_s_firstyear.customer_id = t_w_firstyear.customer_id 
       AND t_s_firstyear.sale_type = 's' 
       AND t_w_firstyear.sale_type = 'w' 
       AND t_s_secyear.sale_type = 's' 
       AND t_w_secyear.sale_type = 'w' 
       AND t_s_firstyear.dyear = 2001 
       AND t_s_secyear.dyear = 2001 + 1 
       AND t_w_firstyear.dyear = 2001 
       AND t_w_secyear.dyear = 2001 + 1 
       AND t_s_firstyear.year_total > 0 
       AND t_w_firstyear.year_total > 0 
       AND CASE 
             WHEN t_w_firstyear.year_total > 0 THEN t_w_secyear.year_total / 
                                                    t_w_firstyear.year_total 
             ELSE 0.0 
           END > CASE 
                   WHEN t_s_firstyear.year_total > 0 THEN 
                   t_s_secyear.year_total / 
                   t_s_firstyear.year_total 
                   ELSE 0.0 
                 END 
ORDER  BY t_s_secyear.customer_id, 
          t_s_secyear.customer_first_name, 
          t_s_secyear.customer_last_name, 
          t_s_secyear.customer_birth_country;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_11_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))









## Query 12

start_time = time.time()
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT
         i_item_id , 
         i_item_desc , 
         i_category , 
         i_class , 
         i_current_price , 
         Sum(ws_ext_sales_price)                                                              AS itemrevenue ,
         Sum(ws_ext_sales_price)*100/Sum(Sum(ws_ext_sales_price)) OVER (partition BY i_class) AS revenueratio
FROM     web_sales , 
         item , 
         date_dim 
WHERE    ws_item_sk = i_item_sk 
AND      i_category IN ('Home', 
                        'Men', 
                        'Women') 
AND      ws_sold_date_sk = d_date_sk 
AND      d_date BETWEEN Cast('2000-05-11' AS DATE) AND      ( 
                  Cast('2000-05-11' AS DATE) + INTERVAL '30' day) 
GROUP BY i_item_id , 
         i_item_desc , 
         i_category , 
         i_class , 
         i_current_price 
ORDER BY i_category , 
         i_class , 
         i_item_id , 
         i_item_desc , 
         revenueratio;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_12_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))


















## Query 13

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
household_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/household_demographics")
household_demographicsdf.createOrReplaceTempView("household_demographics")

query = """

SELECT Avg(ss_quantity), 
       Avg(ss_ext_sales_price), 
       Avg(ss_ext_wholesale_cost), 
       Sum(ss_ext_wholesale_cost) 
FROM   store_sales, 
       store, 
       customer_demographics, 
       household_demographics, 
       customer_address, 
       date_dim 
WHERE  s_store_sk = ss_store_sk 
       AND ss_sold_date_sk = d_date_sk 
       AND d_year = 2001 
       AND ( ( ss_hdemo_sk = hd_demo_sk 
               AND cd_demo_sk = ss_cdemo_sk 
               AND cd_marital_status = 'U' 
               AND cd_education_status = 'Advanced Degree' 
               AND ss_sales_price BETWEEN 100.00 AND 150.00 
               AND hd_dep_count = 3 ) 
              OR ( ss_hdemo_sk = hd_demo_sk 
                   AND cd_demo_sk = ss_cdemo_sk 
                   AND cd_marital_status = 'M' 
                   AND cd_education_status = 'Primary' 
                   AND ss_sales_price BETWEEN 50.00 AND 100.00 
                   AND hd_dep_count = 1 ) 
              OR ( ss_hdemo_sk = hd_demo_sk 
                   AND cd_demo_sk = ss_cdemo_sk 
                   AND cd_marital_status = 'D' 
                   AND cd_education_status = 'Secondary' 
                   AND ss_sales_price BETWEEN 150.00 AND 200.00 
                   AND hd_dep_count = 1 ) ) 
       AND ( ( ss_addr_sk = ca_address_sk 
               AND ca_country = 'United States' 
               AND ca_state IN ( 'AZ', 'NE', 'IA' ) 
               AND ss_net_profit BETWEEN 100 AND 200 ) 
              OR ( ss_addr_sk = ca_address_sk 
                   AND ca_country = 'United States' 
                   AND ca_state IN ( 'MS', 'CA', 'NV' ) 
                   AND ss_net_profit BETWEEN 150 AND 300 ) 
              OR ( ss_addr_sk = ca_address_sk 
                   AND ca_country = 'United States' 
                   AND ca_state IN ( 'GA', 'TX', 'NJ' ) 
                   AND ss_net_profit BETWEEN 50 AND 250 ) ); 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_13_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))








## Query 14

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")

query = """

WITH cross_items 
     AS (SELECT i_item_sk ss_item_sk 
         FROM   item, 
                (SELECT iss.i_brand_id    brand_id, 
                        iss.i_class_id    class_id, 
                        iss.i_category_id category_id 
                 FROM   store_sales, 
                        item iss, 
                        date_dim d1 
                 WHERE  ss_item_sk = iss.i_item_sk 
                        AND ss_sold_date_sk = d1.d_date_sk 
                        AND d1.d_year BETWEEN 1999 AND 1999 + 2 
                 INTERSECT DISTINCT
                 SELECT ics.i_brand_id, 
                        ics.i_class_id, 
                        ics.i_category_id 
                 FROM   catalog_sales, 
                        item ics, 
                        date_dim d2 
                 WHERE  cs_item_sk = ics.i_item_sk 
                        AND cs_sold_date_sk = d2.d_date_sk 
                        AND d2.d_year BETWEEN 1999 AND 1999 + 2 
                 INTERSECT DISTINCT
                 SELECT iws.i_brand_id, 
                        iws.i_class_id, 
                        iws.i_category_id 
                 FROM   web_sales, 
                        item iws, 
                        date_dim d3 
                 WHERE  ws_item_sk = iws.i_item_sk 
                        AND ws_sold_date_sk = d3.d_date_sk 
                        AND d3.d_year BETWEEN 1999 AND 1999 + 2) 
         WHERE  i_brand_id = brand_id 
                AND i_class_id = class_id 
                AND i_category_id = category_id), 
     avg_sales 
     AS (SELECT Avg(quantity * list_price) average_sales 
         FROM   (SELECT ss_quantity   quantity, 
                        ss_list_price list_price 
                 FROM   store_sales, 
                        date_dim 
                 WHERE  ss_sold_date_sk = d_date_sk 
                        AND d_year BETWEEN 1999 AND 1999 + 2 
                 UNION ALL 
                 SELECT cs_quantity   quantity, 
                        cs_list_price list_price 
                 FROM   catalog_sales, 
                        date_dim 
                 WHERE  cs_sold_date_sk = d_date_sk 
                        AND d_year BETWEEN 1999 AND 1999 + 2 
                 UNION ALL 
                 SELECT ws_quantity   quantity, 
                        ws_list_price list_price 
                 FROM   web_sales, 
                        date_dim 
                 WHERE  ws_sold_date_sk = d_date_sk 
                        AND d_year BETWEEN 1999 AND 1999 + 2) x) 
SELECT channel, 
               i_brand_id, 
               i_class_id, 
               i_category_id, 
               Sum(sales), 
               Sum(number_sales) 
FROM  (SELECT 'store'                          channel, 
              i_brand_id, 
              i_class_id, 
              i_category_id, 
              Sum(ss_quantity * ss_list_price) sales, 
              Count(*)                         number_sales 
       FROM   store_sales, 
              item, 
              date_dim 
       WHERE  ss_item_sk IN (SELECT ss_item_sk 
                             FROM   cross_items) 
              AND ss_item_sk = i_item_sk 
              AND ss_sold_date_sk = d_date_sk 
              AND d_year = 1999 + 2 
              AND d_moy = 11 
       GROUP  BY i_brand_id, 
                 i_class_id, 
                 i_category_id 
       HAVING Sum(ss_quantity * ss_list_price) > (SELECT average_sales 
                                                  FROM   avg_sales) 
       UNION ALL 
       SELECT 'catalog'                        channel, 
              i_brand_id, 
              i_class_id, 
              i_category_id, 
              Sum(cs_quantity * cs_list_price) sales, 
              Count(*)                         number_sales 
       FROM   catalog_sales, 
              item, 
              date_dim 
       WHERE  cs_item_sk IN (SELECT ss_item_sk 
                             FROM   cross_items) 
              AND cs_item_sk = i_item_sk 
              AND cs_sold_date_sk = d_date_sk 
              AND d_year = 1999 + 2 
              AND d_moy = 11 
       GROUP  BY i_brand_id, 
                 i_class_id, 
                 i_category_id 
       HAVING Sum(cs_quantity * cs_list_price) > (SELECT average_sales 
                                                  FROM   avg_sales) 
       UNION ALL 
       SELECT 'web'                            channel, 
              i_brand_id, 
              i_class_id, 
              i_category_id, 
              Sum(ws_quantity * ws_list_price) sales, 
              Count(*)                         number_sales 
       FROM   web_sales, 
              item, 
              date_dim 
       WHERE  ws_item_sk IN (SELECT ss_item_sk 
                             FROM   cross_items) 
              AND ws_item_sk = i_item_sk 
              AND ws_sold_date_sk = d_date_sk 
              AND d_year = 1999 + 2 
              AND d_moy = 11 
       GROUP  BY i_brand_id, 
                 i_class_id, 
                 i_category_id 
       HAVING Sum(ws_quantity * ws_list_price) > (SELECT average_sales 
                                                  FROM   avg_sales)) y 
GROUP  BY rollup ( channel, i_brand_id, i_class_id, i_category_id ) 
ORDER  BY channel, 
          i_brand_id, 
          i_class_id, 
          i_category_id;
"""

query_2 = """

WITH cross_items 
     AS (SELECT i_item_sk ss_item_sk 
         FROM   item, 
                (SELECT iss.i_brand_id    brand_id, 
                        iss.i_class_id    class_id, 
                        iss.i_category_id category_id 
                 FROM   store_sales, 
                        item iss, 
                        date_dim d1 
                 WHERE  ss_item_sk = iss.i_item_sk 
                        AND ss_sold_date_sk = d1.d_date_sk 
                        AND d1.d_year BETWEEN 1999 AND 1999 + 2 
                 INTERSECT DISTINCT
                 SELECT ics.i_brand_id, 
                        ics.i_class_id, 
                        ics.i_category_id 
                 FROM   catalog_sales, 
                        item ics, 
                        date_dim d2 
                 WHERE  cs_item_sk = ics.i_item_sk 
                        AND cs_sold_date_sk = d2.d_date_sk 
                        AND d2.d_year BETWEEN 1999 AND 1999 + 2 
                 INTERSECT DISTINCT
                 SELECT iws.i_brand_id, 
                        iws.i_class_id, 
                        iws.i_category_id 
                 FROM   web_sales, 
                        item iws, 
                        date_dim d3 
                 WHERE  ws_item_sk = iws.i_item_sk 
                        AND ws_sold_date_sk = d3.d_date_sk 
                        AND d3.d_year BETWEEN 1999 AND 1999 + 2) x 
         WHERE  i_brand_id = brand_id 
                AND i_class_id = class_id 
                AND i_category_id = category_id), 
     avg_sales 
     AS (SELECT Avg(quantity * list_price) average_sales 
         FROM   (SELECT ss_quantity   quantity, 
                        ss_list_price list_price 
                 FROM   store_sales, 
                        date_dim 
                 WHERE  ss_sold_date_sk = d_date_sk 
                        AND d_year BETWEEN 1999 AND 1999 + 2 
                 UNION ALL 
                 SELECT cs_quantity   quantity, 
                        cs_list_price list_price 
                 FROM   catalog_sales, 
                        date_dim 
                 WHERE  cs_sold_date_sk = d_date_sk 
                        AND d_year BETWEEN 1999 AND 1999 + 2 
                 UNION ALL 
                 SELECT ws_quantity   quantity, 
                        ws_list_price list_price 
                 FROM   web_sales, 
                        date_dim 
                 WHERE  ws_sold_date_sk = d_date_sk 
                        AND d_year BETWEEN 1999 AND 1999 + 2) x) 
SELECT  * 
FROM   (SELECT 'store' this_year_channel, 
               i_brand_id this_year_i_brand_id, 
               i_class_id this_year_i_class_id, 
               i_category_id this_year_i_category_id, 
               Sum(ss_quantity * ss_list_price) this_year_sales, 
               Count(*) this_year_number_sales 
        FROM   store_sales, 
               item, 
               date_dim 
        WHERE  ss_item_sk IN (SELECT ss_item_sk 
                              FROM   cross_items) 
               AND ss_item_sk = i_item_sk 
               AND ss_sold_date_sk = d_date_sk 
               AND d_week_seq = (SELECT d_week_seq 
                                 FROM   date_dim 
                                 WHERE  d_year = 1999 + 1 
                                        AND d_moy = 12 
                                        AND d_dom = 25) 
        GROUP  BY i_brand_id, 
                  i_class_id, 
                  i_category_id 
        HAVING Sum(ss_quantity * ss_list_price) > (SELECT average_sales 
                                                   FROM   avg_sales)) this_year, 
       (SELECT 'store' last_year_channel, 
               i_brand_id last_year_i_brand_id, 
               i_class_id last_year_i_class_id, 
               i_category_id last_year_i_category_id, 
               Sum(ss_quantity * ss_list_price) last_year_sales, 
               Count(*) last_year_number_sales 
        FROM   store_sales, 
               item, 
               date_dim 
        WHERE  ss_item_sk IN (SELECT ss_item_sk 
                              FROM   cross_items) 
               AND ss_item_sk = i_item_sk 
               AND ss_sold_date_sk = d_date_sk 
               AND d_week_seq = (SELECT d_week_seq 
                                 FROM   date_dim 
                                 WHERE  d_year = 1999 
                                        AND d_moy = 12 
                                        AND d_dom = 25) 
        GROUP  BY i_brand_id, 
                  i_class_id, 
                  i_category_id 
        HAVING Sum(ss_quantity * ss_list_price) > (SELECT average_sales 
                                                   FROM   avg_sales)) last_year 
WHERE  this_year.this_year_i_brand_id = last_year.last_year_i_brand_id 
       AND this_year.this_year_i_class_id = last_year.last_year_i_class_id 
       AND this_year.this_year_i_category_id = last_year.last_year_i_category_id 
ORDER  BY this_year.this_year_channel, 
          this_year.this_year_i_brand_id, 
          this_year.this_year_i_class_id, 
          this_year.this_year_i_category_id;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_14_spark_gcs_result")


result_df = spark.sql(query_2)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_14_part_2_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))














## Query 15

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT ca_zip, 
               Sum(cs_sales_price) 
FROM   catalog_sales, 
       customer, 
       customer_address, 
       date_dim 
WHERE  cs_bill_customer_sk = c_customer_sk 
       AND c_current_addr_sk = ca_address_sk 
       AND ( Substr(ca_zip, 1, 5) IN ( '85669', '86197', '88274', '83405', 
                                       '86475', '85392', '85460', '80348', 
                                       '81792' ) 
              OR ca_state IN ( 'CA', 'WA', 'GA' ) 
              OR cs_sales_price > 500 ) 
       AND cs_sold_date_sk = d_date_sk 
       AND d_qoy = 1 
       AND d_year = 1998 
GROUP  BY ca_zip 
ORDER  BY ca_zip;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_15_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))










## Query 16

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
catalog_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_returns")
catalog_returnsdf.createOrReplaceTempView("catalog_returns")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
call_centerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/call_center")
call_centerdf.createOrReplaceTempView("call_center")


query = """

SELECT
         Count(DISTINCT cs_order_number) AS `order count` ,
         Sum(cs_ext_ship_cost)           AS `total shipping cost` ,
         Sum(cs_net_profit)              AS `total net profit`
FROM     catalog_sales cs1 ,
         date_dim ,
         customer_address ,
         call_center
WHERE    d_date BETWEEN '2002-3-01' AND      (
                  Cast('2002-3-01' AS DATE) + INTERVAL '60' day)
AND      cs1.cs_ship_date_sk = d_date_sk
AND      cs1.cs_ship_addr_sk = ca_address_sk
AND      ca_state = 'IA'
AND      cs1.cs_call_center_sk = cc_call_center_sk
AND      cc_county IN ('Williamson County',
                       'Williamson County',
                       'Williamson County',
                       'Williamson County',
                       'Williamson County' )
AND      EXISTS
         (
                SELECT *
                FROM   catalog_sales cs2
                WHERE  cs1.cs_order_number = cs2.cs_order_number
                AND    cs1.cs_warehouse_sk <> cs2.cs_warehouse_sk)
AND      NOT EXISTS
         (
                SELECT *
                FROM   catalog_returns cr1
                WHERE  cs1.cs_order_number = cr1.cr_order_number)
ORDER BY count(DISTINCT cs_order_number);


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_16_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))














## Query 17

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_item_id, 
               i_item_desc, 
               s_state, 
               Count(ss_quantity)                                        AS 
               store_sales_quantitycount, 
               Avg(ss_quantity)                                          AS 
               store_sales_quantityave, 
               Stddev_samp(ss_quantity)                                  AS 
               store_sales_quantitystdev, 
               Stddev_samp(ss_quantity) / Avg(ss_quantity)               AS 
               store_sales_quantitycov, 
               Count(sr_return_quantity)                                 AS 
               store_returns_quantitycount, 
               Avg(sr_return_quantity)                                   AS 
               store_returns_quantityave, 
               Stddev_samp(sr_return_quantity)                           AS 
               store_returns_quantitystdev, 
               Stddev_samp(sr_return_quantity) / Avg(sr_return_quantity) AS 
               store_returns_quantitycov, 
               Count(cs_quantity)                                        AS 
               catalog_sales_quantitycount, 
               Avg(cs_quantity)                                          AS 
               catalog_sales_quantityave, 
               Stddev_samp(cs_quantity) / Avg(cs_quantity)               AS 
               catalog_sales_quantitystdev, 
               Stddev_samp(cs_quantity) / Avg(cs_quantity)               AS 
               catalog_sales_quantitycov 
FROM   store_sales, 
       store_returns, 
       catalog_sales, 
       date_dim d1, 
       date_dim d2, 
       date_dim d3, 
       store, 
       item 
WHERE  d1.d_quarter_name = '1999Q1' 
       AND d1.d_date_sk = ss_sold_date_sk 
       AND i_item_sk = ss_item_sk 
       AND s_store_sk = ss_store_sk 
       AND ss_customer_sk = sr_customer_sk 
       AND ss_item_sk = sr_item_sk 
       AND ss_ticket_number = sr_ticket_number 
       AND sr_returned_date_sk = d2.d_date_sk 
       AND d2.d_quarter_name IN ( '1999Q1', '1999Q2', '1999Q3' ) 
       AND sr_customer_sk = cs_bill_customer_sk 
       AND sr_item_sk = cs_item_sk 
       AND cs_sold_date_sk = d3.d_date_sk 
       AND d3.d_quarter_name IN ( '1999Q1', '1999Q2', '1999Q3' ) 
GROUP  BY i_item_id, 
          i_item_desc, 
          s_state 
ORDER  BY i_item_id, 
          i_item_desc, 
          s_state;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_17_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))




















## Query 18

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_item_id, 
               ca_country, 
               ca_state, 
               ca_county, 
               Avg(Cast(cs_quantity AS NUMERIC))      agg1, 
               Avg(Cast(cs_list_price AS NUMERIC))    agg2, 
               Avg(Cast(cs_coupon_amt AS NUMERIC))    agg3, 
               Avg(Cast(cs_sales_price AS NUMERIC))   agg4, 
               Avg(Cast(cs_net_profit AS NUMERIC))    agg5, 
               Avg(Cast(c_birth_year AS NUMERIC))     agg6, 
               Avg(Cast(cd1.cd_dep_count AS NUMERIC)) agg7 
FROM   catalog_sales, 
       customer_demographics cd1, 
       customer_demographics cd2, 
       customer, 
       customer_address, 
       date_dim, 
       item 
WHERE  cs_sold_date_sk = d_date_sk 
       AND cs_item_sk = i_item_sk 
       AND cs_bill_cdemo_sk = cd1.cd_demo_sk 
       AND cs_bill_customer_sk = c_customer_sk 
       AND cd1.cd_gender = 'F' 
       AND cd1.cd_education_status = 'Secondary' 
       AND c_current_cdemo_sk = cd2.cd_demo_sk 
       AND c_current_addr_sk = ca_address_sk 
       AND c_birth_month IN ( 8, 4, 2, 5, 
                              11, 9 ) 
       AND d_year = 2001 
       AND ca_state IN ( 'KS', 'IA', 'AL', 'UT', 
                         'VA', 'NC', 'TX' ) 
GROUP  BY rollup ( i_item_id, ca_country, ca_state, ca_county ) 
ORDER  BY ca_country, 
          ca_state, 
          ca_county, 
          i_item_id;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_18_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))




















## Query 19

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_brand_id              brand_id, 
               i_brand                 brand, 
               i_manufact_id, 
               i_manufact, 
               Sum(ss_ext_sales_price) ext_price 
FROM   date_dim, 
       store_sales, 
       item, 
       customer, 
       customer_address, 
       store 
WHERE  d_date_sk = ss_sold_date_sk 
       AND ss_item_sk = i_item_sk 
       AND i_manager_id = 38 
       AND d_moy = 12 
       AND d_year = 1998 
       AND ss_customer_sk = c_customer_sk 
       AND c_current_addr_sk = ca_address_sk 
       AND Substr(ca_zip, 1, 5) <> Substr(s_zip, 1, 5) 
       AND ss_store_sk = s_store_sk 
GROUP  BY i_brand, 
          i_brand_id, 
          i_manufact_id, 
          i_manufact 
ORDER  BY ext_price DESC, 
          i_brand, 
          i_brand_id, 
          i_manufact_id, 
          i_manufact;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_19_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))













## Query 20

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT 
         i_item_id , 
         i_item_desc , 
         i_category , 
         i_class , 
         i_current_price , 
         Sum(cs_ext_sales_price)                                                              AS itemrevenue ,
         Sum(cs_ext_sales_price)*100/Sum(Sum(cs_ext_sales_price)) OVER (partition BY i_class) AS revenueratio
FROM     catalog_sales , 
         item , 
         date_dim 
WHERE    cs_item_sk = i_item_sk 
AND      i_category IN ('Children', 
                        'Women', 
                        'Electronics') 
AND      cs_sold_date_sk = d_date_sk 
AND      d_date BETWEEN Cast('2001-02-03' AS DATE) AND      ( 
                  Cast('2001-02-03' AS DATE) + INTERVAL '30' day) 
GROUP BY i_item_id , 
         i_item_desc , 
         i_category , 
         i_class , 
         i_current_price 
ORDER BY i_category , 
         i_class , 
         i_item_id , 
         i_item_desc , 
         revenueratio;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_20_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))









## Query 21

start_time = time.time()
inventorydf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/inventory")
inventorydf.createOrReplaceTempView("inventory")
warehousedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/warehouse")
warehousedf.createOrReplaceTempView("warehouse")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")

query = """

SELECT
         * 
FROM    ( 
                  SELECT   w_warehouse_name , 
                           i_item_id , 
                           Sum( 
                           CASE 
                                    WHEN ( 
                                                      Cast(d_date AS DATE) < Cast ('2000-05-13' AS DATE)) THEN inv_quantity_on_hand 
                                    ELSE 0 
                           END) AS inv_before , 
                           Sum( 
                           CASE 
                                    WHEN ( 
                                                      Cast(d_date AS DATE) >= Cast ('2000-05-13' AS DATE)) THEN inv_quantity_on_hand 
                                    ELSE 0 
                           END) AS inv_after 
                  FROM     inventory , 
                           warehouse , 
                           item , 
                           date_dim 
                  WHERE    i_current_price BETWEEN 0.99 AND      1.49 
                  AND      i_item_sk = inv_item_sk 
                  AND      inv_warehouse_sk = w_warehouse_sk 
                  AND      inv_date_sk = d_date_sk 
                  AND      d_date BETWEEN (Cast ('2000-05-13' AS DATE) - INTERVAL '30' day) AND      ( 
                                    cast ('2000-05-13' AS        date) + INTERVAL '30' day) 
                  GROUP BY w_warehouse_name, 
                           i_item_id) x 
WHERE    ( 
                  CASE 
                           WHEN inv_before > 0 THEN inv_after / inv_before 
                           ELSE NULL 
                  END) BETWEEN 2.0/3.0 AND      3.0/2.0 
ORDER BY w_warehouse_name , 
         i_item_id;


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_21_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))














## Query 22

start_time = time.time()
inventorydf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/inventory")
inventorydf.createOrReplaceTempView("inventory")
warehousedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/warehouse")
warehousedf.createOrReplaceTempView("warehouse")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_product_name, 
               i_brand, 
               i_class, 
               i_category, 
               Avg(inv_quantity_on_hand) qoh 
FROM   inventory, 
       date_dim, 
       item, 
       warehouse 
WHERE  inv_date_sk = d_date_sk 
       AND inv_item_sk = i_item_sk 
       AND inv_warehouse_sk = w_warehouse_sk 
       AND d_month_seq BETWEEN 1205 AND 1205 + 11 
GROUP  BY rollup( i_product_name, i_brand, i_class, i_category ) 
ORDER  BY qoh, 
          i_product_name, 
          i_brand, 
          i_class, 
          i_category; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_22_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 23

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

WITH frequent_ss_items 
     AS (SELECT Substr(i_item_desc, 1, 30) itemdesc, 
                i_item_sk                  item_sk, 
                d_date                     solddate, 
                Count(*)                   cnt 
         FROM   store_sales, 
                date_dim, 
                item 
         WHERE  ss_sold_date_sk = d_date_sk 
                AND ss_item_sk = i_item_sk 
                AND d_year IN ( 1998, 1998 + 1, 1998 + 2, 1998 + 3 ) 
         GROUP  BY Substr(i_item_desc, 1, 30), 
                   i_item_sk, 
                   d_date 
         HAVING Count(*) > 4), 
     max_store_sales 
     AS (SELECT Max(csales) tpcds_cmax 
         FROM   (SELECT c_customer_sk, 
                        Sum(ss_quantity * ss_sales_price) csales 
                 FROM   store_sales, 
                        customer, 
                        date_dim 
                 WHERE  ss_customer_sk = c_customer_sk 
                        AND ss_sold_date_sk = d_date_sk 
                        AND d_year IN ( 1998, 1998 + 1, 1998 + 2, 1998 + 3 ) 
                 GROUP  BY c_customer_sk)), 
     best_ss_customer 
     AS (SELECT c_customer_sk, 
                Sum(ss_quantity * ss_sales_price) ssales 
         FROM   store_sales, 
                customer 
         WHERE  ss_customer_sk = c_customer_sk 
         GROUP  BY c_customer_sk 
         HAVING Sum(ss_quantity * ss_sales_price) > 
                ( 95 / 100.0 ) * (SELECT * 
                                  FROM   max_store_sales)) 
SELECT Sum(sales) 
FROM   (SELECT cs_quantity * cs_list_price sales 
        FROM   catalog_sales, 
               date_dim 
        WHERE  d_year = 1998 
               AND d_moy = 6 
               AND cs_sold_date_sk = d_date_sk 
               AND cs_item_sk IN (SELECT item_sk 
                                  FROM   frequent_ss_items) 
               AND cs_bill_customer_sk IN (SELECT c_customer_sk 
                                           FROM   best_ss_customer) 
        UNION ALL 
        SELECT ws_quantity * ws_list_price sales 
        FROM   web_sales, 
               date_dim 
        WHERE  d_year = 1998 
               AND d_moy = 6 
               AND ws_sold_date_sk = d_date_sk 
               AND ws_item_sk IN (SELECT item_sk 
                                  FROM   frequent_ss_items) 
               AND ws_bill_customer_sk IN (SELECT c_customer_sk 
                                           FROM   best_ss_customer)); 
"""

query_2 = """

WITH frequent_ss_items 
     AS (SELECT Substr(i_item_desc, 1, 30) itemdesc, 
                i_item_sk                  item_sk, 
                d_date                     solddate, 
                Count(*)                   cnt 
         FROM   store_sales, 
                date_dim, 
                item 
         WHERE  ss_sold_date_sk = d_date_sk 
                AND ss_item_sk = i_item_sk 
                AND d_year IN ( 1998, 1998 + 1, 1998 + 2, 1998 + 3 ) 
         GROUP  BY Substr(i_item_desc, 1, 30), 
                   i_item_sk, 
                   d_date 
         HAVING Count(*) > 4), 
     max_store_sales 
     AS (SELECT Max(csales) tpcds_cmax 
         FROM   (SELECT c_customer_sk, 
                        Sum(ss_quantity * ss_sales_price) csales 
                 FROM   store_sales, 
                        customer, 
                        date_dim 
                 WHERE  ss_customer_sk = c_customer_sk 
                        AND ss_sold_date_sk = d_date_sk 
                        AND d_year IN ( 1998, 1998 + 1, 1998 + 2, 1998 + 3 ) 
                 GROUP  BY c_customer_sk)), 
     best_ss_customer 
     AS (SELECT c_customer_sk, 
                Sum(ss_quantity * ss_sales_price) ssales 
         FROM   store_sales, 
                customer 
         WHERE  ss_customer_sk = c_customer_sk 
         GROUP  BY c_customer_sk 
         HAVING Sum(ss_quantity * ss_sales_price) > 
                ( 95 / 100.0 ) * (SELECT * 
                                  FROM   max_store_sales)) 
SELECT c_last_name, 
               c_first_name, 
               sales 
FROM   (SELECT c_last_name, 
               c_first_name, 
               Sum(cs_quantity * cs_list_price) sales 
        FROM   catalog_sales, 
               customer, 
               date_dim 
        WHERE  d_year = 1998 
               AND d_moy = 6 
               AND cs_sold_date_sk = d_date_sk 
               AND cs_item_sk IN (SELECT item_sk 
                                  FROM   frequent_ss_items) 
               AND cs_bill_customer_sk IN (SELECT c_customer_sk 
                                           FROM   best_ss_customer) 
               AND cs_bill_customer_sk = c_customer_sk 
        GROUP  BY c_last_name, 
                  c_first_name 
        UNION ALL 
        SELECT c_last_name, 
               c_first_name, 
               Sum(ws_quantity * ws_list_price) sales 
        FROM   web_sales, 
               customer, 
               date_dim 
        WHERE  d_year = 1998 
               AND d_moy = 6 
               AND ws_sold_date_sk = d_date_sk 
               AND ws_item_sk IN (SELECT item_sk 
                                  FROM   frequent_ss_items) 
               AND ws_bill_customer_sk IN (SELECT c_customer_sk 
                                           FROM   best_ss_customer) 
               AND ws_bill_customer_sk = c_customer_sk 
        GROUP  BY c_last_name, 
                  c_first_name) 
ORDER  BY c_last_name, 
          c_first_name, 
          sales; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_23_spark_gcs_result")


result_df = spark.sql(query_2)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_23_part_2_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 24

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

WITH ssales 
     AS (SELECT c_last_name, 
                c_first_name, 
                s_store_name, 
                ca_state, 
                s_state, 
                i_color, 
                i_current_price, 
                i_manager_id, 
                i_units, 
                i_size, 
                Sum(ss_net_profit) netpaid 
         FROM   store_sales, 
                store_returns, 
                store, 
                item, 
                customer, 
                customer_address 
         WHERE  ss_ticket_number = sr_ticket_number 
                AND ss_item_sk = sr_item_sk 
                AND ss_customer_sk = c_customer_sk 
                AND ss_item_sk = i_item_sk 
                AND ss_store_sk = s_store_sk 
                AND c_birth_country = Upper(ca_country) 
                AND s_zip = ca_zip 
                AND s_market_id = 6 
         GROUP  BY c_last_name, 
                   c_first_name, 
                   s_store_name, 
                   ca_state, 
                   s_state, 
                   i_color, 
                   i_current_price, 
                   i_manager_id, 
                   i_units, 
                   i_size) 
SELECT c_last_name, 
       c_first_name, 
       s_store_name, 
       Sum(netpaid) paid 
FROM   ssales 
WHERE  i_color = 'papaya' 
GROUP  BY c_last_name, 
          c_first_name, 
          s_store_name 
HAVING Sum(netpaid) > (SELECT 0.05 * Avg(netpaid) 
                       FROM   ssales); 

"""

query_2 = """

WITH ssales 
     AS (SELECT c_last_name, 
                c_first_name, 
                s_store_name, 
                ca_state, 
                s_state, 
                i_color, 
                i_current_price, 
                i_manager_id, 
                i_units, 
                i_size, 
                Sum(ss_net_profit) netpaid 
         FROM   store_sales, 
                store_returns, 
                store, 
                item, 
                customer, 
                customer_address 
         WHERE  ss_ticket_number = sr_ticket_number 
                AND ss_item_sk = sr_item_sk 
                AND ss_customer_sk = c_customer_sk 
                AND ss_item_sk = i_item_sk 
                AND ss_store_sk = s_store_sk 
                AND c_birth_country = Upper(ca_country) 
                AND s_zip = ca_zip 
                AND s_market_id = 6 
         GROUP  BY c_last_name, 
                   c_first_name, 
                   s_store_name, 
                   ca_state, 
                   s_state, 
                   i_color, 
                   i_current_price, 
                   i_manager_id, 
                   i_units, 
                   i_size) 
SELECT c_last_name, 
       c_first_name, 
       s_store_name, 
       Sum(netpaid) paid 
FROM   ssales 
WHERE  i_color = 'chartreuse' 
GROUP  BY c_last_name, 
          c_first_name, 
          s_store_name 
HAVING Sum(netpaid) > (SELECT 0.05 * Avg(netpaid) 
                       FROM   ssales); 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_24_spark_gcs_result")


result_df = spark.sql(query_2)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_24_part_2_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))
















## Query 25

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_item_id, 
               i_item_desc, 
               s_store_id, 
               s_store_name, 
               Max(ss_net_profit) AS store_sales_profit, 
               Max(sr_net_loss)   AS store_returns_loss, 
               Max(cs_net_profit) AS catalog_sales_profit 
FROM   store_sales, 
       store_returns, 
       catalog_sales, 
       date_dim d1, 
       date_dim d2, 
       date_dim d3, 
       store, 
       item 
WHERE  d1.d_moy = 4 
       AND d1.d_year = 2001 
       AND d1.d_date_sk = ss_sold_date_sk 
       AND i_item_sk = ss_item_sk 
       AND s_store_sk = ss_store_sk 
       AND ss_customer_sk = sr_customer_sk 
       AND ss_item_sk = sr_item_sk 
       AND ss_ticket_number = sr_ticket_number 
       AND sr_returned_date_sk = d2.d_date_sk 
       AND d2.d_moy BETWEEN 4 AND 10 
       AND d2.d_year = 2001 
       AND sr_customer_sk = cs_bill_customer_sk 
       AND sr_item_sk = cs_item_sk 
       AND cs_sold_date_sk = d3.d_date_sk 
       AND d3.d_moy BETWEEN 4 AND 10 
       AND d3.d_year = 2001 
GROUP  BY i_item_id, 
          i_item_desc, 
          s_store_id, 
          s_store_name 
ORDER  BY i_item_id, 
          i_item_desc, 
          s_store_id, 
          s_store_name; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_25_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))














## Query 26
start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")
promotiondf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/promotion")
promotiondf.createOrReplaceTempView("promotion")


query = """

SELECT i_item_id, 
               Avg(cs_quantity)    agg1, 
               Avg(cs_list_price)  agg2, 
               Avg(cs_coupon_amt)  agg3, 
               Avg(cs_sales_price) agg4 
FROM   catalog_sales, 
       customer_demographics, 
       date_dim, 
       item, 
       promotion 
WHERE  cs_sold_date_sk = d_date_sk 
       AND cs_item_sk = i_item_sk 
       AND cs_bill_cdemo_sk = cd_demo_sk 
       AND cs_promo_sk = p_promo_sk 
       AND cd_gender = 'F' 
       AND cd_marital_status = 'W' 
       AND cd_education_status = 'Secondary' 
       AND ( p_channel_email = 'N' 
              OR p_channel_event = 'N' ) 
       AND d_year = 2000 
GROUP  BY i_item_id 
ORDER  BY i_item_id;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_26_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 27

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_item_id, 
               s_state, 
               Grouping(s_state)   g_state, 
               Avg(ss_quantity)    agg1, 
               Avg(ss_list_price)  agg2, 
               Avg(ss_coupon_amt)  agg3, 
               Avg(ss_sales_price) agg4 
FROM   store_sales, 
       customer_demographics, 
       date_dim, 
       store, 
       item 
WHERE  ss_sold_date_sk = d_date_sk 
       AND ss_item_sk = i_item_sk 
       AND ss_store_sk = s_store_sk 
       AND ss_cdemo_sk = cd_demo_sk 
       AND cd_gender = 'M' 
       AND cd_marital_status = 'D' 
       AND cd_education_status = 'College' 
       AND d_year = 2000 
       AND s_state IN ( 'TN', 'TN', 'TN', 'TN', 
                        'TN', 'TN' ) 
GROUP  BY rollup ( i_item_id, s_state ) 
ORDER  BY i_item_id, 
          s_state;


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_27_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))









## Query 28

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")


query = """

SELECT * 
FROM   (SELECT Avg(ss_list_price)            B1_LP, 
               Count(ss_list_price)          B1_CNT, 
               Count(DISTINCT ss_list_price) B1_CNTD 
        FROM   store_sales 
        WHERE  ss_quantity BETWEEN 0 AND 5 
               AND ( ss_list_price BETWEEN 18 AND 18 + 10 
                      OR ss_coupon_amt BETWEEN 1939 AND 1939 + 1000 
                      OR ss_wholesale_cost BETWEEN 34 AND 34 + 20 )) B1, 
       (SELECT Avg(ss_list_price)            B2_LP, 
               Count(ss_list_price)          B2_CNT, 
               Count(DISTINCT ss_list_price) B2_CNTD 
        FROM   store_sales 
        WHERE  ss_quantity BETWEEN 6 AND 10 
               AND ( ss_list_price BETWEEN 1 AND 1 + 10 
                      OR ss_coupon_amt BETWEEN 35 AND 35 + 1000 
                      OR ss_wholesale_cost BETWEEN 50 AND 50 + 20 )) B2, 
       (SELECT Avg(ss_list_price)            B3_LP, 
               Count(ss_list_price)          B3_CNT, 
               Count(DISTINCT ss_list_price) B3_CNTD 
        FROM   store_sales 
        WHERE  ss_quantity BETWEEN 11 AND 15 
               AND ( ss_list_price BETWEEN 91 AND 91 + 10 
                      OR ss_coupon_amt BETWEEN 1412 AND 1412 + 1000 
                      OR ss_wholesale_cost BETWEEN 17 AND 17 + 20 )) B3, 
       (SELECT Avg(ss_list_price)            B4_LP, 
               Count(ss_list_price)          B4_CNT, 
               Count(DISTINCT ss_list_price) B4_CNTD 
        FROM   store_sales 
        WHERE  ss_quantity BETWEEN 16 AND 20 
               AND ( ss_list_price BETWEEN 9 AND 9 + 10 
                      OR ss_coupon_amt BETWEEN 5270 AND 5270 + 1000 
                      OR ss_wholesale_cost BETWEEN 29 AND 29 + 20 )) B4, 
       (SELECT Avg(ss_list_price)            B5_LP, 
               Count(ss_list_price)          B5_CNT, 
               Count(DISTINCT ss_list_price) B5_CNTD 
        FROM   store_sales 
        WHERE  ss_quantity BETWEEN 21 AND 25 
               AND ( ss_list_price BETWEEN 45 AND 45 + 10 
                      OR ss_coupon_amt BETWEEN 826 AND 826 + 1000 
                      OR ss_wholesale_cost BETWEEN 5 AND 5 + 20 )) B5, 
       (SELECT Avg(ss_list_price)            B6_LP, 
               Count(ss_list_price)          B6_CNT, 
               Count(DISTINCT ss_list_price) B6_CNTD 
        FROM   store_sales 
        WHERE  ss_quantity BETWEEN 26 AND 30 
               AND ( ss_list_price BETWEEN 174 AND 174 + 10 
                      OR ss_coupon_amt BETWEEN 5548 AND 5548 + 1000 
                      OR ss_wholesale_cost BETWEEN 42 AND 42 + 20 )) B6;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_28_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 29

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT i_item_id, 
               i_item_desc, 
               s_store_id, 
               s_store_name, 
               Avg(ss_quantity)        AS store_sales_quantity, 
               Avg(sr_return_quantity) AS store_returns_quantity, 
               Avg(cs_quantity)        AS catalog_sales_quantity 
FROM   store_sales, 
       store_returns, 
       catalog_sales, 
       date_dim d1, 
       date_dim d2, 
       date_dim d3, 
       store, 
       item 
WHERE  d1.d_moy = 4 
       AND d1.d_year = 1998 
       AND d1.d_date_sk = ss_sold_date_sk 
       AND i_item_sk = ss_item_sk 
       AND s_store_sk = ss_store_sk 
       AND ss_customer_sk = sr_customer_sk 
       AND ss_item_sk = sr_item_sk 
       AND ss_ticket_number = sr_ticket_number 
       AND sr_returned_date_sk = d2.d_date_sk 
       AND d2.d_moy BETWEEN 4 AND 4 + 3 
       AND d2.d_year = 1998 
       AND sr_customer_sk = cs_bill_customer_sk 
       AND sr_item_sk = cs_item_sk 
       AND cs_sold_date_sk = d3.d_date_sk 
       AND d3.d_year IN ( 1998, 1998 + 1, 1998 + 2 ) 
GROUP  BY i_item_id, 
          i_item_desc, 
          s_store_id, 
          s_store_name 
ORDER  BY i_item_id, 
          i_item_desc, 
          s_store_id, 
          s_store_name;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_29_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))













## Query 30

start_time = time.time()
web_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_returns")
web_returnsdf.createOrReplaceTempView("web_returns")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

WITH customer_total_return 
     AS (SELECT wr_returning_customer_sk AS ctr_customer_sk, 
                ca_state                 AS ctr_state, 
                Sum(wr_return_amt)       AS ctr_total_return 
         FROM   web_returns, 
                date_dim, 
                customer_address 
         WHERE  wr_returned_date_sk = d_date_sk 
                AND d_year = 2000 
                AND wr_returning_addr_sk = ca_address_sk 
         GROUP  BY wr_returning_customer_sk, 
                   ca_state) 
SELECT c_customer_id, 
               c_salutation, 
               c_first_name, 
               c_last_name, 
               c_preferred_cust_flag, 
               c_birth_day, 
               c_birth_month, 
               c_birth_year, 
               c_birth_country, 
               c_login, 
               c_email_address, 
               c_last_review_date, 
               ctr_total_return 
FROM   customer_total_return ctr1, 
       customer_address, 
       customer 
WHERE  ctr1.ctr_total_return > (SELECT Avg(ctr_total_return) * 1.2 
                                FROM   customer_total_return ctr2 
                                WHERE  ctr1.ctr_state = ctr2.ctr_state) 
       AND ca_address_sk = c_current_addr_sk 
       AND ca_state = 'IN' 
       AND ctr1.ctr_customer_sk = c_customer_sk 
ORDER  BY c_customer_id, 
          c_salutation, 
          c_first_name, 
          c_last_name, 
          c_preferred_cust_flag, 
          c_birth_day, 
          c_birth_month, 
          c_birth_year, 
          c_birth_country, 
          c_login, 
          c_email_address, 
          c_last_review_date, 
          ctr_total_return;


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_30_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))













## Query 31

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

WITH ss 
     AS (SELECT ca_county, 
                d_qoy, 
                d_year, 
                Sum(ss_ext_sales_price) AS store_sales 
         FROM   store_sales, 
                date_dim, 
                customer_address 
         WHERE  ss_sold_date_sk = d_date_sk 
                AND ss_addr_sk = ca_address_sk 
         GROUP  BY ca_county, 
                   d_qoy, 
                   d_year), 
     ws 
     AS (SELECT ca_county, 
                d_qoy, 
                d_year, 
                Sum(ws_ext_sales_price) AS web_sales 
         FROM   web_sales, 
                date_dim, 
                customer_address 
         WHERE  ws_sold_date_sk = d_date_sk 
                AND ws_bill_addr_sk = ca_address_sk 
         GROUP  BY ca_county, 
                   d_qoy, 
                   d_year) 
SELECT ss1.ca_county, 
       ss1.d_year, 
       ws2.web_sales / ws1.web_sales     web_q1_q2_increase, 
       ss2.store_sales / ss1.store_sales store_q1_q2_increase, 
       ws3.web_sales / ws2.web_sales     web_q2_q3_increase, 
       ss3.store_sales / ss2.store_sales store_q2_q3_increase 
FROM   ss ss1, 
       ss ss2, 
       ss ss3, 
       ws ws1, 
       ws ws2, 
       ws ws3 
WHERE  ss1.d_qoy = 1 
       AND ss1.d_year = 2001 
       AND ss1.ca_county = ss2.ca_county 
       AND ss2.d_qoy = 2 
       AND ss2.d_year = 2001 
       AND ss2.ca_county = ss3.ca_county 
       AND ss3.d_qoy = 3 
       AND ss3.d_year = 2001 
       AND ss1.ca_county = ws1.ca_county 
       AND ws1.d_qoy = 1 
       AND ws1.d_year = 2001 
       AND ws1.ca_county = ws2.ca_county 
       AND ws2.d_qoy = 2 
       AND ws2.d_year = 2001 
       AND ws1.ca_county = ws3.ca_county 
       AND ws3.d_qoy = 3 
       AND ws3.d_year = 2001 
       AND CASE 
             WHEN ws1.web_sales > 0 THEN ws2.web_sales / ws1.web_sales 
             ELSE NULL 
           END > CASE 
                   WHEN ss1.store_sales > 0 THEN 
                   ss2.store_sales / ss1.store_sales 
                   ELSE NULL 
                 END 
       AND CASE 
             WHEN ws2.web_sales > 0 THEN ws3.web_sales / ws2.web_sales 
             ELSE NULL 
           END > CASE 
                   WHEN ss2.store_sales > 0 THEN 
                   ss3.store_sales / ss2.store_sales 
                   ELSE NULL 
                 END 
ORDER  BY ss1.d_year; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_31_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 32

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT 
       Sum(cs_ext_discount_amt) AS `excess discount amount`
FROM   catalog_sales , 
       item , 
       date_dim 
WHERE  i_manufact_id = 610 
AND    i_item_sk = cs_item_sk 
AND    d_date BETWEEN '2001-03-04' AND    ( 
              Cast('2001-03-04' AS DATE) + INTERVAL '90' day) 
AND    d_date_sk = cs_sold_date_sk 
AND    cs_ext_discount_amt > 
       ( 
              SELECT 1.3 * avg(cs_ext_discount_amt) 
              FROM   catalog_sales , 
                     date_dim 
              WHERE  cs_item_sk = i_item_sk 
              AND    d_date BETWEEN '2001-03-04' AND    ( 
                            cast('2001-03-04' AS date) + INTERVAL '90' day) 
              AND    d_date_sk = cs_sold_date_sk ) ;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_32_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 33

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")


query = """

WITH ss 
     AS (SELECT i_manufact_id, 
                Sum(ss_ext_sales_price) total_sales 
         FROM   store_sales, 
                date_dim, 
                customer_address, 
                item 
         WHERE  i_manufact_id IN (SELECT i_manufact_id 
                                  FROM   item 
                                  WHERE  i_category IN ( 'Books' )) 
                AND ss_item_sk = i_item_sk 
                AND ss_sold_date_sk = d_date_sk 
                AND d_year = 1999 
                AND d_moy = 3 
                AND ss_addr_sk = ca_address_sk 
                AND ca_gmt_offset = -5 
         GROUP  BY i_manufact_id), 
     cs 
     AS (SELECT i_manufact_id, 
                Sum(cs_ext_sales_price) total_sales 
         FROM   catalog_sales, 
                date_dim, 
                customer_address, 
                item 
         WHERE  i_manufact_id IN (SELECT i_manufact_id 
                                  FROM   item 
                                  WHERE  i_category IN ( 'Books' )) 
                AND cs_item_sk = i_item_sk 
                AND cs_sold_date_sk = d_date_sk 
                AND d_year = 1999 
                AND d_moy = 3 
                AND cs_bill_addr_sk = ca_address_sk 
                AND ca_gmt_offset = -5 
         GROUP  BY i_manufact_id), 
     ws 
     AS (SELECT i_manufact_id, 
                Sum(ws_ext_sales_price) total_sales 
         FROM   web_sales, 
                date_dim, 
                customer_address, 
                item 
         WHERE  i_manufact_id IN (SELECT i_manufact_id 
                                  FROM   item 
                                  WHERE  i_category IN ( 'Books' )) 
                AND ws_item_sk = i_item_sk 
                AND ws_sold_date_sk = d_date_sk 
                AND d_year = 1999 
                AND d_moy = 3 
                AND ws_bill_addr_sk = ca_address_sk 
                AND ca_gmt_offset = -5 
         GROUP  BY i_manufact_id) 
SELECT i_manufact_id, 
               Sum(total_sales) total_sales 
FROM   (SELECT * 
        FROM   ss 
        UNION ALL 
        SELECT * 
        FROM   cs 
        UNION ALL 
        SELECT * 
        FROM   ws) tmp1 
GROUP  BY i_manufact_id 
ORDER  BY total_sales;


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_33_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))
















## Query 34

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
household_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/household_demographics")
household_demographicsdf.createOrReplaceTempView("household_demographics")


query = """

SELECT c_last_name, 
       c_first_name, 
       c_salutation, 
       c_preferred_cust_flag, 
       ss_ticket_number, 
       cnt 
FROM   (SELECT ss_ticket_number, 
               ss_customer_sk, 
               Count(*) cnt 
        FROM   store_sales, 
               date_dim, 
               store, 
               household_demographics 
        WHERE  store_sales.ss_sold_date_sk = date_dim.d_date_sk 
               AND store_sales.ss_store_sk = store.s_store_sk 
               AND store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk 
               AND ( date_dim.d_dom BETWEEN 1 AND 3 
                      OR date_dim.d_dom BETWEEN 25 AND 28 ) 
               AND ( household_demographics.hd_buy_potential = '>10000' 
                      OR household_demographics.hd_buy_potential = 'unknown' ) 
               AND household_demographics.hd_vehicle_count > 0 
               AND ( CASE 
                       WHEN household_demographics.hd_vehicle_count > 0 THEN 
                       household_demographics.hd_dep_count / 
                       household_demographics.hd_vehicle_count 
                       ELSE NULL 
                     END ) > 1.2 
               AND date_dim.d_year IN ( 1999, 1999 + 1, 1999 + 2 ) 
               AND store.s_county IN ( 'Williamson County', 'Williamson County', 
                                       'Williamson County', 
                                                             'Williamson County' 
                                       , 
                                       'Williamson County', 'Williamson County', 
                                           'Williamson County', 
                                                             'Williamson County' 
                                     ) 
        GROUP  BY ss_ticket_number, 
                  ss_customer_sk) dn, 
       customer 
WHERE  ss_customer_sk = c_customer_sk 
       AND cnt BETWEEN 15 AND 20 
ORDER  BY c_last_name, 
          c_first_name, 
          c_salutation, 
          c_preferred_cust_flag DESC; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_34_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))









## Query 35

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT ca_state, 
               cd_gender, 
               cd_marital_status, 
               cd_dep_count, 
               Count(*) cnt1, 
               Stddev_samp(cd_dep_count), 
               Avg(cd_dep_count), 
               Max(cd_dep_count), 
               cd_dep_employed_count, 
               Count(*) cnt2, 
               Stddev_samp(cd_dep_employed_count), 
               Avg(cd_dep_employed_count), 
               Max(cd_dep_employed_count), 
               cd_dep_college_count, 
               Count(*) cnt3, 
               Stddev_samp(cd_dep_college_count), 
               Avg(cd_dep_college_count), 
               Max(cd_dep_college_count) 
FROM   customer c, 
       customer_address ca, 
       customer_demographics 
WHERE  c.c_current_addr_sk = ca.ca_address_sk 
       AND cd_demo_sk = c.c_current_cdemo_sk 
       AND EXISTS (SELECT * 
                   FROM   store_sales, 
                          date_dim 
                   WHERE  c.c_customer_sk = ss_customer_sk 
                          AND ss_sold_date_sk = d_date_sk 
                          AND d_year = 2001 
                          AND d_qoy < 4) 
       AND ( EXISTS (SELECT * 
                     FROM   web_sales, 
                            date_dim 
                     WHERE  c.c_customer_sk = ws_bill_customer_sk 
                            AND ws_sold_date_sk = d_date_sk 
                            AND d_year = 2001 
                            AND d_qoy < 4) 
              OR EXISTS (SELECT * 
                         FROM   catalog_sales, 
                                date_dim 
                         WHERE  c.c_customer_sk = cs_ship_customer_sk 
                                AND cs_sold_date_sk = d_date_sk 
                                AND d_year = 2001 
                                AND d_qoy < 4) ) 
GROUP  BY ca_state, 
          cd_gender, 
          cd_marital_status, 
          cd_dep_count, 
          cd_dep_employed_count, 
          cd_dep_college_count 
ORDER  BY ca_state, 
          cd_gender, 
          cd_marital_status, 
          cd_dep_count, 
          cd_dep_employed_count, 
          cd_dep_college_count;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_35_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 36

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT Sum(ss_net_profit) / Sum(ss_ext_sales_price)                 AS 
               gross_margin, 
               i_category, 
               i_class, 
               Grouping(i_category) + Grouping(i_class)                     AS 
               lochierarchy, 
               Rank() 
                 OVER ( 
                   partition BY Grouping(i_category)+Grouping(i_class), CASE 
                 WHEN Grouping( 
                 i_class) = 0 THEN i_category END 
                   ORDER BY Sum(ss_net_profit)/Sum(ss_ext_sales_price) ASC) AS 
               rank_within_parent 
FROM   store_sales, 
       date_dim d1, 
       item, 
       store 
WHERE  d1.d_year = 2000 
       AND d1.d_date_sk = ss_sold_date_sk 
       AND i_item_sk = ss_item_sk 
       AND s_store_sk = ss_store_sk 
       AND s_state IN ( 'TN', 'TN', 'TN', 'TN', 
                        'TN', 'TN', 'TN', 'TN' ) 
GROUP  BY rollup( i_category, i_class ) 
ORDER  BY lochierarchy DESC, 
          CASE 
            WHEN lochierarchy = 0 THEN i_category 
          END, 
          rank_within_parent;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_36_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))













## Query 37

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")
inventorydf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/inventory")
inventorydf.createOrReplaceTempView("inventory")


query = """

SELECT 
         i_item_id , 
         i_item_desc , 
         i_current_price 
FROM     item, 
         inventory, 
         date_dim, 
         catalog_sales 
WHERE    i_current_price BETWEEN 20 AND      20 + 30 
AND      inv_item_sk = i_item_sk 
AND      d_date_sk=inv_date_sk 
AND      d_date BETWEEN Cast('1999-03-06' AS DATE) AND      ( 
                  Cast('1999-03-06' AS DATE) + INTERVAL '60' day) 
AND      i_manufact_id IN (843,815,850,840) 
AND      inv_quantity_on_hand BETWEEN 100 AND      500 
AND      cs_item_sk = i_item_sk 
GROUP BY i_item_id, 
         i_item_desc, 
         i_current_price 
ORDER BY i_item_id ;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_37_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 38

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT Count(*) 
FROM   (SELECT DISTINCT c_last_name, 
                        c_first_name, 
                        d_date 
        FROM   store_sales, 
               date_dim, 
               customer 
        WHERE  store_sales.ss_sold_date_sk = date_dim.d_date_sk 
               AND store_sales.ss_customer_sk = customer.c_customer_sk 
               AND d_month_seq BETWEEN 1188 AND 1188 + 11 
        INTERSECT DISTINCT 
        SELECT DISTINCT c_last_name, 
                        c_first_name, 
                        d_date 
        FROM   catalog_sales, 
               date_dim, 
               customer 
        WHERE  catalog_sales.cs_sold_date_sk = date_dim.d_date_sk 
               AND catalog_sales.cs_bill_customer_sk = customer.c_customer_sk 
               AND d_month_seq BETWEEN 1188 AND 1188 + 11 
        INTERSECT DISTINCT
        SELECT DISTINCT c_last_name, 
                        c_first_name, 
                        d_date 
        FROM   web_sales, 
               date_dim, 
               customer 
        WHERE  web_sales.ws_sold_date_sk = date_dim.d_date_sk 
               AND web_sales.ws_bill_customer_sk = customer.c_customer_sk 
               AND d_month_seq BETWEEN 1188 AND 1188 + 11) hot_cust;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_38_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 39

start_time = time.time()
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")
inventorydf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/inventory")
inventorydf.createOrReplaceTempView("inventory")
warehousedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/warehouse")
warehousedf.createOrReplaceTempView("warehouse")


query = """

WITH inv 
     AS (SELECT w_warehouse_name, 
                w_warehouse_sk, 
                i_item_sk, 
                d_moy, 
                stdev, 
                mean, 
                CASE mean 
                  WHEN 0 THEN NULL 
                  ELSE stdev / mean 
                END cov 
         FROM  (SELECT w_warehouse_name, 
                       w_warehouse_sk, 
                       i_item_sk, 
                       d_moy, 
                       Stddev_samp(inv_quantity_on_hand) stdev, 
                       Avg(inv_quantity_on_hand)         mean 
                FROM   inventory, 
                       item, 
                       warehouse, 
                       date_dim 
                WHERE  inv_item_sk = i_item_sk 
                       AND inv_warehouse_sk = w_warehouse_sk 
                       AND inv_date_sk = d_date_sk 
                       AND d_year = 2002 
                GROUP  BY w_warehouse_name, 
                          w_warehouse_sk, 
                          i_item_sk, 
                          d_moy) foo 
         WHERE  CASE mean 
                  WHEN 0 THEN 0 
                  ELSE stdev / mean 
                END > 1) 
SELECT inv1.w_warehouse_sk, 
       inv1.i_item_sk, 
       inv1.d_moy, 
       inv1.mean, 
       inv1.cov, 
       inv2.w_warehouse_sk w_warehouse_sk2, 
       inv2.i_item_sk i_item_sk2, 
       inv2.d_moy d_moy2, 
       inv2.mean mean2, 
       inv2.cov cov2
FROM   inv inv1, 
       inv inv2 
WHERE  inv1.i_item_sk = inv2.i_item_sk 
       AND inv1.w_warehouse_sk = inv2.w_warehouse_sk 
       AND inv1.d_moy = 1 
       AND inv2.d_moy = 1 + 1 
ORDER  BY inv1.w_warehouse_sk, 
          inv1.i_item_sk, 
          inv1.d_moy, 
          inv1.mean, 
          inv1.cov, 
          inv2.d_moy, 
          inv2.mean, 
          inv2.cov; 

"""

query_2 = """

WITH inv 
     AS (SELECT w_warehouse_name, 
                w_warehouse_sk, 
                i_item_sk, 
                d_moy, 
                stdev, 
                mean, 
                CASE mean 
                  WHEN 0 THEN NULL 
                  ELSE stdev / mean 
                END cov 
         FROM  (SELECT w_warehouse_name, 
                       w_warehouse_sk, 
                       i_item_sk, 
                       d_moy, 
                       Stddev_samp(inv_quantity_on_hand) stdev, 
                       Avg(inv_quantity_on_hand)         mean 
                FROM   inventory, 
                       item, 
                       warehouse, 
                       date_dim 
                WHERE  inv_item_sk = i_item_sk 
                       AND inv_warehouse_sk = w_warehouse_sk 
                       AND inv_date_sk = d_date_sk 
                       AND d_year = 2002 
                GROUP  BY w_warehouse_name, 
                          w_warehouse_sk, 
                          i_item_sk, 
                          d_moy) foo 
         WHERE  CASE mean 
                  WHEN 0 THEN 0 
                  ELSE stdev / mean 
                END > 1) 
SELECT inv1.w_warehouse_sk, 
       inv1.i_item_sk, 
       inv1.d_moy, 
       inv1.mean, 
       inv1.cov, 
       inv2.w_warehouse_sk w_warehouse_sk2, 
       inv2.i_item_sk i_item_sk2, 
       inv2.d_moy d_moy2, 
       inv2.mean mean2, 
       inv2.cov cov2 
FROM   inv inv1, 
       inv inv2 
WHERE  inv1.i_item_sk = inv2.i_item_sk 
       AND inv1.w_warehouse_sk = inv2.w_warehouse_sk 
       AND inv1.d_moy = 1 
       AND inv2.d_moy = 1 + 1 
       AND inv1.cov > 1.5 
ORDER  BY inv1.w_warehouse_sk, 
          inv1.i_item_sk, 
          inv1.d_moy, 
          inv1.mean, 
          inv1.cov, 
          inv2.d_moy, 
          inv2.mean, 
          inv2.cov; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_39_spark_gcs_result")


result_df = spark.sql(query_2)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_39_part_2_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))










## Query 40

start_time = time.time()
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
catalog_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_returns")
catalog_returnsdf.createOrReplaceTempView("catalog_returns")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")
warehousedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/warehouse")
warehousedf.createOrReplaceTempView("warehouse")


query = """

SELECT
                w_state , 
                i_item_id , 
                Sum( 
                CASE 
                                WHEN ( 
                                                                Cast(d_date AS DATE) < Cast ('2002-06-01' AS DATE)) THEN cs_sales_price - COALESCE(cr_refunded_cash,0) 
                                ELSE 0 
                END) AS sales_before , 
                Sum( 
                CASE 
                                WHEN ( 
                                                                Cast(d_date AS DATE) >= Cast ('2002-06-01' AS DATE)) THEN cs_sales_price - COALESCE(cr_refunded_cash,0) 
                                ELSE 0 
                END) AS sales_after 
FROM            catalog_sales 
LEFT OUTER JOIN catalog_returns 
ON              ( 
                                cs_order_number = cr_order_number 
                AND             cs_item_sk = cr_item_sk) , 
                warehouse , 
                item , 
                date_dim 
WHERE           i_current_price BETWEEN 0.99 AND             1.49 
AND             i_item_sk = cs_item_sk 
AND             cs_warehouse_sk = w_warehouse_sk 
AND             cs_sold_date_sk = d_date_sk 
AND             d_date BETWEEN (Cast ('2002-06-01' AS DATE) - INTERVAL '30' day) AND             ( 
                                cast ('2002-06-01' AS date) + INTERVAL '30' day) 
GROUP BY        w_state, 
                i_item_id 
ORDER BY        w_state, 
                i_item_id ;

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_40_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))











## Query 41

start_time = time.time()
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT Distinct(i_product_name) 
FROM   item i1 
WHERE  i_manufact_id BETWEEN 765 AND 765 + 40 
       AND (SELECT Count(*) AS item_cnt 
            FROM   item 
            WHERE  ( i_manufact = i1.i_manufact 
                     AND ( ( i_category = 'Women' 
                             AND ( i_color = 'dim' 
                                    OR i_color = 'green' ) 
                             AND ( i_units = 'Gross' 
                                    OR i_units = 'Dozen' ) 
                             AND ( i_size = 'economy' 
                                    OR i_size = 'petite' ) ) 
                            OR ( i_category = 'Women' 
                                 AND ( i_color = 'navajo' 
                                        OR i_color = 'aquamarine' ) 
                                 AND ( i_units = 'Case' 
                                        OR i_units = 'Unknown' ) 
                                 AND ( i_size = 'large' 
                                        OR i_size = 'N/A' ) ) 
                            OR ( i_category = 'Men' 
                                 AND ( i_color = 'indian' 
                                        OR i_color = 'dark' ) 
                                 AND ( i_units = 'Oz' 
                                        OR i_units = 'Lb' ) 
                                 AND ( i_size = 'extra large' 
                                        OR i_size = 'small' ) ) 
                            OR ( i_category = 'Men' 
                                 AND ( i_color = 'peach' 
                                        OR i_color = 'purple' ) 
                                 AND ( i_units = 'Tbl' 
                                        OR i_units = 'Bunch' ) 
                                 AND ( i_size = 'economy' 
                                        OR i_size = 'petite' ) ) ) ) 
                    OR ( i_manufact = i1.i_manufact 
                         AND ( ( i_category = 'Women' 
                                 AND ( i_color = 'orchid' 
                                        OR i_color = 'peru' ) 
                                 AND ( i_units = 'Carton' 
                                        OR i_units = 'Cup' ) 
                                 AND ( i_size = 'economy' 
                                        OR i_size = 'petite' ) ) 
                                OR ( i_category = 'Women' 
                                     AND ( i_color = 'violet' 
                                            OR i_color = 'papaya' ) 
                                     AND ( i_units = 'Ounce' 
                                            OR i_units = 'Box' ) 
                                     AND ( i_size = 'large' 
                                            OR i_size = 'N/A' ) ) 
                                OR ( i_category = 'Men' 
                                     AND ( i_color = 'drab' 
                                            OR i_color = 'grey' ) 
                                     AND ( i_units = 'Each' 
                                            OR i_units = 'N/A' ) 
                                     AND ( i_size = 'extra large' 
                                            OR i_size = 'small' ) ) 
                                OR ( i_category = 'Men' 
                                     AND ( i_color = 'chocolate' 
                                            OR i_color = 'antique' ) 
                                     AND ( i_units = 'Dram' 
                                            OR i_units = 'Gram' ) 
                                     AND ( i_size = 'economy' 
                                            OR i_size = 'petite' ) ) ) )) > 0 
ORDER  BY i_product_name; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_41_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))















## Query 42

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT dt.d_year, 
               item.i_category_id, 
               item.i_category, 
               Sum(ss_ext_sales_price) 
FROM   date_dim dt, 
       store_sales, 
       item 
WHERE  dt.d_date_sk = store_sales.ss_sold_date_sk 
       AND store_sales.ss_item_sk = item.i_item_sk 
       AND item.i_manager_id = 1 
       AND dt.d_moy = 12 
       AND dt.d_year = 2000 
GROUP  BY dt.d_year, 
          item.i_category_id, 
          item.i_category 
ORDER  BY Sum(ss_ext_sales_price) DESC, 
          dt.d_year, 
          item.i_category_id, 
          item.i_category; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_42_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))















## Query 43

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT s_store_name, 
               s_store_id, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Sunday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) sun_sales, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Monday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) mon_sales, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Tuesday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) tue_sales, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Wednesday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) wed_sales, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Thursday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) thu_sales, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Friday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) fri_sales, 
               Sum(CASE 
                     WHEN ( d_day_name = 'Saturday' ) THEN ss_sales_price 
                     ELSE NULL 
                   END) sat_sales 
FROM   date_dim, 
       store_sales, 
       store 
WHERE  d_date_sk = ss_sold_date_sk 
       AND s_store_sk = ss_store_sk 
       AND s_gmt_offset = -5 
       AND d_year = 2002 
GROUP  BY s_store_name, 
          s_store_id 
ORDER  BY s_store_name, 
          s_store_id, 
          sun_sales, 
          mon_sales, 
          tue_sales, 
          wed_sales, 
          thu_sales, 
          fri_sales, 
          sat_sales; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_43_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 44

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT asceding.rnk, 
               i1.i_product_name best_performing, 
               i2.i_product_name worst_performing 
FROM  (SELECT * 
       FROM   (SELECT item_sk, 
                      Rank() 
                        OVER ( 
                          ORDER BY rank_col ASC) rnk 
               FROM   (SELECT ss_item_sk         item_sk, 
                              Avg(ss_net_profit) rank_col 
                       FROM   store_sales ss1 
                       WHERE  ss_store_sk = 4 
                       GROUP  BY ss_item_sk 
                       HAVING Avg(ss_net_profit) > 0.9 * 
                              (SELECT Avg(ss_net_profit) 
                                      rank_col 
                               FROM   store_sales 
                               WHERE  ss_store_sk = 4 
                                      AND ss_cdemo_sk IS 
                                          NULL 
                               GROUP  BY ss_store_sk))V1) 
              V11 
       WHERE  rnk < 11) asceding, 
      (SELECT * 
       FROM   (SELECT item_sk, 
                      Rank() 
                        OVER ( 
                          ORDER BY rank_col DESC) rnk 
               FROM   (SELECT ss_item_sk         item_sk, 
                              Avg(ss_net_profit) rank_col 
                       FROM   store_sales ss1 
                       WHERE  ss_store_sk = 4 
                       GROUP  BY ss_item_sk 
                       HAVING Avg(ss_net_profit) > 0.9 * 
                              (SELECT Avg(ss_net_profit) 
                                      rank_col 
                               FROM   store_sales 
                               WHERE  ss_store_sk = 4 
                                      AND ss_cdemo_sk IS 
                                          NULL 
                               GROUP  BY ss_store_sk))V2) 
              V21 
       WHERE  rnk < 11) descending, 
      item i1, 
      item i2 
WHERE  asceding.rnk = descending.rnk 
       AND i1.i_item_sk = asceding.item_sk 
       AND i2.i_item_sk = descending.item_sk 
ORDER  BY asceding.rnk; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_44_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))










## Query 45

start_time = time.time()
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

SELECT ca_zip, 
               ca_state, 
               Sum(ws_sales_price) 
FROM   web_sales, 
       customer, 
       customer_address, 
       date_dim, 
       item 
WHERE  ws_bill_customer_sk = c_customer_sk 
       AND c_current_addr_sk = ca_address_sk 
       AND ws_item_sk = i_item_sk 
       AND ( Substr(ca_zip, 1, 5) IN ( '85669', '86197', '88274', '83405', 
                                       '86475', '85392', '85460', '80348', 
                                       '81792' ) 
              OR i_item_id IN (SELECT i_item_id 
                               FROM   item 
                               WHERE  i_item_sk IN ( 2, 3, 5, 7, 
                                                     11, 13, 17, 19, 
                                                     23, 29 )) ) 
       AND ws_sold_date_sk = d_date_sk 
       AND d_qoy = 1 
       AND d_year = 2000 
GROUP  BY ca_zip, 
          ca_state 
ORDER  BY ca_zip, 
          ca_state; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_45_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))












## Query 46

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customerdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer")
customerdf.createOrReplaceTempView("customer")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
household_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/household_demographics")
household_demographicsdf.createOrReplaceTempView("household_demographics")


query = """

SELECT c_last_name, 
               c_first_name, 
               ca_city, 
               bought_city, 
               ss_ticket_number, 
               amt, 
               profit 
FROM   (SELECT ss_ticket_number, 
               ss_customer_sk, 
               ca_city            bought_city, 
               Sum(ss_coupon_amt) amt, 
               Sum(ss_net_profit) profit 
        FROM   store_sales, 
               date_dim, 
               store, 
               household_demographics, 
               customer_address 
        WHERE  store_sales.ss_sold_date_sk = date_dim.d_date_sk 
               AND store_sales.ss_store_sk = store.s_store_sk 
               AND store_sales.ss_hdemo_sk = household_demographics.hd_demo_sk 
               AND store_sales.ss_addr_sk = customer_address.ca_address_sk 
               AND ( household_demographics.hd_dep_count = 6 
                      OR household_demographics.hd_vehicle_count = 0 ) 
               AND date_dim.d_dow IN ( 6, 0 ) 
               AND date_dim.d_year IN ( 2000, 2000 + 1, 2000 + 2 ) 
               AND store.s_city IN ( 'Midway', 'Fairview', 'Fairview', 
                                     'Fairview', 
                                     'Fairview' ) 
        GROUP  BY ss_ticket_number, 
                  ss_customer_sk, 
                  ss_addr_sk, 
                  ca_city) dn, 
       customer, 
       customer_address current_addr 
WHERE  ss_customer_sk = c_customer_sk 
       AND customer.c_current_addr_sk = current_addr.ca_address_sk 
       AND current_addr.ca_city <> bought_city 
ORDER  BY c_last_name, 
          c_first_name, 
          ca_city, 
          bought_city, 
          ss_ticket_number; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_46_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))





















## Query 47

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")
itemdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/item")
itemdf.createOrReplaceTempView("item")


query = """

WITH v1 
     AS (SELECT i_category, 
                i_brand, 
                s_store_name, 
                s_company_name, 
                d_year, 
                d_moy, 
                Sum(ss_sales_price)         sum_sales, 
                Avg(Sum(ss_sales_price)) 
                  OVER ( 
                    partition BY i_category, i_brand, s_store_name, 
                  s_company_name, 
                  d_year) 
                                            avg_monthly_sales, 
                Rank() 
                  OVER ( 
                    partition BY i_category, i_brand, s_store_name, 
                  s_company_name 
                    ORDER BY d_year, d_moy) rn 
         FROM   item, 
                store_sales, 
                date_dim, 
                store 
         WHERE  ss_item_sk = i_item_sk 
                AND ss_sold_date_sk = d_date_sk 
                AND ss_store_sk = s_store_sk 
                AND ( d_year = 1999 
                       OR ( d_year = 1999 - 1 
                            AND d_moy = 12 ) 
                       OR ( d_year = 1999 + 1 
                            AND d_moy = 1 ) ) 
         GROUP  BY i_category, 
                   i_brand, 
                   s_store_name, 
                   s_company_name, 
                   d_year, 
                   d_moy), 
     v2 
     AS (SELECT v1.i_category, 
                v1.d_year, 
                v1.d_moy, 
                v1.avg_monthly_sales, 
                v1.sum_sales, 
                v1_lag.sum_sales  psum, 
                v1_lead.sum_sales nsum 
         FROM   v1, 
                v1 v1_lag, 
                v1 v1_lead 
         WHERE  v1.i_category = v1_lag.i_category 
                AND v1.i_category = v1_lead.i_category 
                AND v1.i_brand = v1_lag.i_brand 
                AND v1.i_brand = v1_lead.i_brand 
                AND v1.s_store_name = v1_lag.s_store_name 
                AND v1.s_store_name = v1_lead.s_store_name 
                AND v1.s_company_name = v1_lag.s_company_name 
                AND v1.s_company_name = v1_lead.s_company_name 
                AND v1.rn = v1_lag.rn + 1 
                AND v1.rn = v1_lead.rn - 1) 
SELECT * 
FROM   v2 
WHERE  d_year = 1999 
       AND avg_monthly_sales > 0 
       AND CASE 
             WHEN avg_monthly_sales > 0 THEN Abs(sum_sales - avg_monthly_sales) 
                                             / 
                                             avg_monthly_sales 
             ELSE NULL 
           END > 0.1 
ORDER  BY sum_sales - avg_monthly_sales, 
          3; 


"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_47_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))



















## Query 48

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
customer_addressdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_address")
customer_addressdf.createOrReplaceTempView("customer_address")
customer_demographicsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/customer_demographics")
customer_demographicsdf.createOrReplaceTempView("customer_demographics")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT Sum (ss_quantity) 
FROM   store_sales, 
       store, 
       customer_demographics, 
       customer_address, 
       date_dim 
WHERE  s_store_sk = ss_store_sk 
       AND ss_sold_date_sk = d_date_sk 
       AND d_year = 1999 
       AND ( ( cd_demo_sk = ss_cdemo_sk 
               AND cd_marital_status = 'W' 
               AND cd_education_status = 'Secondary' 
               AND ss_sales_price BETWEEN 100.00 AND 150.00 ) 
              OR ( cd_demo_sk = ss_cdemo_sk 
                   AND cd_marital_status = 'M' 
                   AND cd_education_status = 'Advanced Degree' 
                   AND ss_sales_price BETWEEN 50.00 AND 100.00 ) 
              OR ( cd_demo_sk = ss_cdemo_sk 
                   AND cd_marital_status = 'D' 
                   AND cd_education_status = '2 yr Degree' 
                   AND ss_sales_price BETWEEN 150.00 AND 200.00 ) ) 
       AND ( ( ss_addr_sk = ca_address_sk 
               AND ca_country = 'United States' 
               AND ca_state IN ( 'TX', 'NE', 'MO' ) 
               AND ss_net_profit BETWEEN 0 AND 2000 ) 
              OR ( ss_addr_sk = ca_address_sk 
                   AND ca_country = 'United States' 
                   AND ca_state IN ( 'CO', 'TN', 'ND' ) 
                   AND ss_net_profit BETWEEN 150 AND 3000 ) 
              OR ( ss_addr_sk = ca_address_sk 
                   AND ca_country = 'United States' 
                   AND ca_state IN ( 'OK', 'PA', 'CA' ) 
                   AND ss_net_profit BETWEEN 50 AND 25000 ) ); 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_48_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))













## Query 49

start_time = time.time()
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
web_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_sales")
web_salesdf.createOrReplaceTempView("web_sales")
web_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/web_returns")
web_returnsdf.createOrReplaceTempView("web_returns")
catalog_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_sales")
catalog_salesdf.createOrReplaceTempView("catalog_sales")
catalog_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/catalog_returns")
catalog_returnsdf.createOrReplaceTempView("catalog_returns")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT 'web' AS channel, 
               web.item, 
               web.return_ratio, 
               web.return_rank, 
               web.currency_rank 
FROM   (SELECT item, 
               return_ratio, 
               currency_ratio, 
               Rank() 
                 OVER ( 
                   ORDER BY return_ratio)   AS return_rank, 
               Rank() 
                 OVER ( 
                   ORDER BY currency_ratio) AS currency_rank 
        FROM   (SELECT ws.ws_item_sk                                       AS 
                       item, 
                       ( Cast(Sum(COALESCE(wr.wr_return_quantity, 0)) AS NUMERIC) / 
                         Cast( 
                         Sum(COALESCE(ws.ws_quantity, 0)) AS NUMERIC))  AS 
                       return_ratio, 
                       ( Cast(Sum(COALESCE(wr.wr_return_amt, 0)) AS NUMERIC) 
                         / Cast( 
                         Sum( 
                         COALESCE(ws.ws_net_paid, 0)) AS NUMERIC) )                                             AS 
                       currency_ratio 
                FROM   web_sales ws 
                       LEFT OUTER JOIN web_returns wr 
                                    ON ( ws.ws_order_number = wr.wr_order_number 
                                         AND ws.ws_item_sk = wr.wr_item_sk ), 
                       date_dim 
                WHERE  wr.wr_return_amt > 10000 
                       AND ws.ws_net_profit > 1 
                       AND ws.ws_net_paid > 0 
                       AND ws.ws_quantity > 0 
                       AND ws_sold_date_sk = d_date_sk 
                       AND d_year = 1999 
                       AND d_moy = 12 
                GROUP  BY ws.ws_item_sk) in_web) web 
WHERE  ( web.return_rank <= 10 
          OR web.currency_rank <= 10 ) 
UNION ALL
SELECT 'catalog' AS channel, 
       catalog.item, 
       catalog.return_ratio, 
       catalog.return_rank, 
       catalog.currency_rank 
FROM   (SELECT item, 
               return_ratio, 
               currency_ratio, 
               Rank() 
                 OVER ( 
                   ORDER BY return_ratio)   AS return_rank, 
               Rank() 
                 OVER ( 
                   ORDER BY currency_ratio) AS currency_rank 
        FROM   (SELECT cs.cs_item_sk                                       AS 
                       item, 
                       ( Cast(Sum(COALESCE(cr.cr_return_quantity, 0)) AS NUMERIC) / 
                         Cast( 
                         Sum(COALESCE(cs.cs_quantity, 0)) AS NUMERIC) ) AS 
                       return_ratio, 
                       ( Cast(Sum(COALESCE(cr.cr_return_amount, 0)) AS NUMERIC
                              ) / 
                         Cast(Sum( 
                         COALESCE(cs.cs_net_paid, 0)) AS NUMERIC))                                         AS 
                       currency_ratio 
                FROM   catalog_sales cs 
                       LEFT OUTER JOIN catalog_returns cr 
                                    ON ( cs.cs_order_number = cr.cr_order_number 
                                         AND cs.cs_item_sk = cr.cr_item_sk ), 
                       date_dim 
                WHERE  cr.cr_return_amount > 10000 
                       AND cs.cs_net_profit > 1 
                       AND cs.cs_net_paid > 0 
                       AND cs.cs_quantity > 0 
                       AND cs_sold_date_sk = d_date_sk 
                       AND d_year = 1999 
                       AND d_moy = 12 
                GROUP  BY cs.cs_item_sk) in_cat) catalog 
WHERE  ( catalog.return_rank <= 10 
          OR catalog.currency_rank <= 10 ) 
UNION ALL
SELECT 'store' AS channel, 
       store.item, 
       store.return_ratio, 
       store.return_rank, 
       store.currency_rank 
FROM   (SELECT item, 
               return_ratio, 
               currency_ratio, 
               Rank() 
                 OVER ( 
                   ORDER BY return_ratio)   AS return_rank, 
               Rank() 
                 OVER ( 
                   ORDER BY currency_ratio) AS currency_rank 
        FROM   (SELECT sts.ss_item_sk                                       AS 
                       item, 
                       ( Cast(Sum(COALESCE(sr.sr_return_quantity, 0)) AS NUMERIC) / 
                         Cast( 
                         Sum(COALESCE(sts.ss_quantity, 0)) AS NUMERIC) ) AS 
                       return_ratio, 
                       ( Cast(Sum(COALESCE(sr.sr_return_amt, 0)) AS NUMERIC) 
                         / Cast( 
                         Sum( 
                         COALESCE(sts.ss_net_paid, 0)) AS NUMERIC) )     AS 
                       currency_ratio 
                FROM   store_sales sts 
                       LEFT OUTER JOIN store_returns sr 
                                    ON ( sts.ss_ticket_number = 
                                         sr.sr_ticket_number 
                                         AND sts.ss_item_sk = sr.sr_item_sk ), 
                       date_dim 
                WHERE  sr.sr_return_amt > 10000 
                       AND sts.ss_net_profit > 1 
                       AND sts.ss_net_paid > 0 
                       AND sts.ss_quantity > 0 
                       AND ss_sold_date_sk = d_date_sk 
                       AND d_year = 1999 
                       AND d_moy = 12 
                GROUP  BY sts.ss_item_sk) in_store) store 
WHERE  ( store.return_rank <= 10 
          OR store.currency_rank <= 10 ) 
ORDER  BY 1, 
          4, 
          5; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_49_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))














## Query 50

start_time = time.time()
storedf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store")
storedf.createOrReplaceTempView("store")
store_salesdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_sales")
store_salesdf.createOrReplaceTempView("store_sales")
store_returnsdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/store_returns")
store_returnsdf.createOrReplaceTempView("store_returns")
date_dimdf = spark.read.parquet("gs://benchmarking-source/TPCDS/1TB/date_dim")
date_dimdf.createOrReplaceTempView("date_dim")


query = """

SELECT s_store_name, 
               s_company_id, 
               s_street_number, 
               s_street_name, 
               s_street_type, 
               s_suite_number, 
               s_city, 
               s_county, 
               s_state, 
               s_zip, 
               Sum(CASE 
                     WHEN ( sr_returned_date_sk - ss_sold_date_sk <= 30 ) THEN 1 
                     ELSE 0 
                   END) AS `30 days`, 
               Sum(CASE 
                     WHEN ( sr_returned_date_sk - ss_sold_date_sk > 30 ) 
                          AND ( sr_returned_date_sk - ss_sold_date_sk <= 60 ) 
                   THEN 1 
                     ELSE 0 
                   END) AS `31-60 days`, 
               Sum(CASE 
                     WHEN ( sr_returned_date_sk - ss_sold_date_sk > 60 ) 
                          AND ( sr_returned_date_sk - ss_sold_date_sk <= 90 ) 
                   THEN 1 
                     ELSE 0 
                   END) AS `61-90 days`, 
               Sum(CASE 
                     WHEN ( sr_returned_date_sk - ss_sold_date_sk > 90 ) 
                          AND ( sr_returned_date_sk - ss_sold_date_sk <= 120 ) 
                   THEN 1 
                     ELSE 0 
                   END) AS `91-120 days`, 
               Sum(CASE 
                     WHEN ( sr_returned_date_sk - ss_sold_date_sk > 120 ) THEN 1 
                     ELSE 0 
                   END) AS `>120 days` 
FROM   store_sales, 
       store_returns, 
       store, 
       date_dim d1, 
       date_dim d2 
WHERE  d2.d_year = 2002 
       AND d2.d_moy = 9 
       AND ss_ticket_number = sr_ticket_number 
       AND ss_item_sk = sr_item_sk 
       AND ss_sold_date_sk = d1.d_date_sk 
       AND sr_returned_date_sk = d2.d_date_sk 
       AND ss_customer_sk = sr_customer_sk 
       AND ss_store_sk = s_store_sk 
GROUP  BY s_store_name, 
          s_company_id, 
          s_street_number, 
          s_street_name, 
          s_street_type, 
          s_suite_number, 
          s_city, 
          s_county, 
          s_state, 
          s_zip 
ORDER  BY s_store_name, 
          s_company_id, 
          s_street_number, 
          s_street_name, 
          s_street_type, 
          s_suite_number, 
          s_city, 
          s_county, 
          s_state, 
          s_zip; 

"""

result_df = spark.sql(query)

for field in result_df.schema.fields:
    if isinstance(field.dataType, DecimalType):
        result_df = result_df.withColumn(field.name, col(field.name).cast(DecimalType(38, 9)))

result_df.write.parquet("gs://benchmarking-source/output_folder/1TB/query_50_spark_gcs_result")

end_time = time.time()
print("_______________")
print("Execution time:"+str(end_time-start_time))





















