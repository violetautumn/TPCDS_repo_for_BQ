
## 1. call center

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.call_center \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/call_center.dat




## 2. catalog page

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.catalog_page \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/catalog_page.dat




## 3. catalog_returns

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.catalog_returns \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/catalog_returns.dat




## 4. catalog_sales

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.catalog_sales \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/catalog_sales.dat





## 5. customer

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.customer \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/customer.dat





## 6. customer_address

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.customer_address \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/customer_address.dat






## 7. customer_demographics

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.customer_demographics \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/customer_demographics.dat





## 8. date_dim

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.date_dim \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/date_dim.dat




## 9. household_demographics

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.household_demographics \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/household_demographics.dat


## 10. income_band

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.income_band \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/income_band.dat


## 11. inventory

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.inventory \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/inventory.dat




## 12. item

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.item \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/item.dat





## 13. promotion

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.promotion \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/promotion.dat




## 14. reason

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.reason \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/reason.dat





## 15. ship_mode

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.ship_mode \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/ship_mode.dat




## 16. store

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.store \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/store.dat





## 17. store_returns

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.store_returns \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/store_returns.dat



## 18. store_sales

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.store_sales \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/store_sales.dat





## 19. time_dim

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.time_dim \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/time_dim.dat






## 20. warehouse

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.warehouse \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/warehouse.dat





## 21. web_page

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.web_page \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/web_page.dat





## 22. web_returns

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.web_returns \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/web_returns.dat





## 23. web_sales

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.web_sales \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/web_sales.dat





## 24. web_site

bq load \
  --source_format=CSV \
  --field_delimiter="|" \
  --ignore_unknown_values \
  TPCDS.web_site \
  gs://tpc-ds-bucket-1/tpc-ds/tmp-1T/web_site.dat
