
## 1. call center

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.call_center` 
(
cc_call_center_sk INT64,
cc_call_center_id STRING,
cc_rec_start_date DATE,
cc_rec_end_date DATE,
cc_closed_date_sk INT64,
cc_open_date_sk INT64,
cc_name STRING,
cc_class STRING,
cc_employees INT64,
cc_sq_ft INT64,
cc_hours STRING,
cc_manager STRING,
cc_mkt_id INT64,
cc_mkt_class STRING,
cc_mkt_desc STRING,
cc_market_manager STRING,
cc_division INT64,
cc_division_name STRING,
cc_company INT64,
cc_company_name STRING,
cc_street_number STRING,
cc_street_name STRING,
cc_street_type STRING,
cc_suite_number STRING,
cc_city STRING,
cc_county STRING,
cc_state STRING,
cc_zip STRING,
cc_country STRING,
cc_gmt_offset NUMERIC,
cc_tax_percentage NUMERIC
);




## 2. catalog page

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.catalog_page` (
  cp_catalog_page_sk INT64,
  cp_catalog_page_id STRING,
  cp_start_date_sk INT64,
  cp_end_date_sk INT64,
  cp_department STRING,
  cp_catalog_number INT64,
  cp_catalog_page_number INT64,
  cp_description STRING,
  cp_type STRING
);




## 3. catalog_returns

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.catalog_returns` (
  cr_returned_date_sk INT64,
  cr_returned_time_sk INT64,
  cr_item_sk INT64 NOT NULL,
  cr_refunded_customer_sk INT64,
  cr_refunded_cdemo_sk INT64,
  cr_refunded_hdemo_sk INT64,
  cr_refunded_addr_sk INT64,
  cr_returning_customer_sk INT64,
  cr_returning_cdemo_sk INT64,
  cr_returning_hdemo_sk INT64,
  cr_returning_addr_sk INT64,
  cr_call_center_sk INT64,
  cr_catalog_page_sk INT64,
  cr_ship_mode_sk INT64,
  cr_warehouse_sk INT64,
  cr_reason_sk INT64,
  cr_order_number INT64 NOT NULL,
  cr_return_quantity INT64,
  cr_return_amount FLOAT64,
  cr_return_tax FLOAT64,
  cr_return_amt_inc_tax FLOAT64,
  cr_fee FLOAT64,
  cr_return_ship_cost FLOAT64,
  cr_refunded_cash FLOAT64,
  cr_reversed_charge FLOAT64,
  cr_store_credit FLOAT64,
  cr_net_loss FLOAT64
);




## 4. catalog_sales

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.catalog_sales` (
    cs_sold_date_sk           INT64,
    cs_sold_time_sk           INT64,
    cs_ship_date_sk           INT64,
    cs_bill_customer_sk       INT64,
    cs_bill_cdemo_sk          INT64,
    cs_bill_hdemo_sk          INT64,
    cs_bill_addr_sk           INT64,
    cs_ship_customer_sk       INT64,
    cs_ship_cdemo_sk          INT64,
    cs_ship_hdemo_sk          INT64,
    cs_ship_addr_sk           INT64,
    cs_call_center_sk         INT64,
    cs_catalog_page_sk        INT64,
    cs_ship_mode_sk           INT64,
    cs_warehouse_sk           INT64,
    cs_item_sk                INT64 NOT NULL,
    cs_promo_sk               INT64,
    cs_order_number           INT64 NOT NULL,
    cs_quantity               INT64,
    cs_wholesale_cost         FLOAT64,
    cs_list_price             FLOAT64,
    cs_sales_price            FLOAT64,
    cs_ext_discount_amt       FLOAT64,
    cs_ext_sales_price        FLOAT64,
    cs_ext_wholesale_cost     FLOAT64,
    cs_ext_list_price         FLOAT64,
    cs_ext_tax                FLOAT64,
    cs_coupon_amt             FLOAT64,
    cs_ext_ship_cost          FLOAT64,
    cs_net_paid               FLOAT64,
    cs_net_paid_inc_tax       FLOAT64,
    cs_net_paid_inc_ship      FLOAT64,
    cs_net_paid_inc_ship_tax  FLOAT64,
    cs_net_profit             FLOAT64
);





## 5. customer

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.customer` (
    c_customer_sk             INT64 NOT NULL,
    c_customer_id             STRING NOT NULL,
    c_current_cdemo_sk        INT64, 
    c_current_hdemo_sk        INT64,
    c_current_addr_sk         INT64,
    c_first_shipto_date_sk    INT64,
    c_first_sales_date_sk     INT64,
    c_salutation              STRING,
    c_first_name              STRING,
    c_last_name               STRING,
    c_preferred_cust_flag     STRING,
    c_birth_day               INT64,
    c_birth_month             INT64,
    c_birth_year              INT64,
    c_birth_country           STRING,
    c_login                   STRING,
    c_email_address           STRING,
    c_last_review_date		  STRING  
);






## 6. customer_address

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.customer_address` (
    ca_address_sk            INT64 NOT NULL,
    ca_address_id            STRING NOT NULL,
    ca_street_number         STRING,
    ca_street_name           STRING,
    ca_street_type           STRING,
    ca_suite_number      	 STRING,
    ca_city             	 STRING,
    ca_county           	 STRING,
    ca_state            	 STRING,
    ca_zip              	 STRING,
    ca_country          	 STRING,
    ca_gmt_offset       	 FLOAT64, 
    ca_location_type     	 STRING
);





## 7. customer_demographics

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.customer_demographics` (
    cd_demo_sk             INT64 NOT NULL,
    cd_gender              STRING,
    cd_marital_status      STRING,
    cd_education_status    STRING,
    cd_purchase_estimate   INT64,
    cd_credit_rating       STRING,
    cd_dep_count           INT64,
    cd_dep_employed_count  INT64,
    cd_dep_college_count   INT64 
);



## 8. date_dim

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.date_dim` (
    d_date_sk               INT64 NOT NULL,
    d_date_id               STRING NOT NULL,
    d_date                  DATE,
    d_month_seq             INT64,
    d_week_seq              INT64,
    d_quarter_seq           INT64,
    d_year                  INT64,
    d_dow                   INT64,
    d_moy                   INT64,
    d_dom                   INT64,
    d_qoy                   INT64,
    d_fy_year               INT64,
    d_fy_quarter_seq        INT64,
    d_fy_week_seq           INT64,
    d_day_name              STRING,
    d_quarter_name          STRING,
    d_holiday               STRING,
    d_weekend               STRING,
    d_following_holiday     STRING,
    d_first_dom             INT64,
    d_last_dom              INT64,
    d_same_day_ly           INT64,
    d_same_day_lq           INT64,
    d_current_day           STRING,
    d_current_week          STRING,
    d_current_month         STRING,
    d_current_quarter       STRING,
    d_current_year          STRING
);





## 9. household_demographics

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.household_demographics` (
    hd_demo_sk          INT64 NOT NULL,
    hd_income_band_sk   INT64,
    hd_buy_potential    STRING,
    hd_dep_count        INT64,
    hd_vehicle_count    INT64
);




## 10. income_band

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.income_band` (
    ib_income_band_sk         INT64 NOT NULL,
    ib_lower_bound            INT64, 
    ib_upper_bound            INT64
);




## 11. inventory

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.inventory` (
    inv_date_sk               INT64 NOT NULL,
    inv_item_sk               INT64 NOT NULL,
    inv_warehouse_sk          INT64 NOT NULL,
    inv_quantity_on_hand      INT64 
);





## 12. item

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.item` (
    i_item_sk             INT64 NOT NULL,
    i_item_id             STRING NOT NULL,
    i_rec_start_date      DATE,
    i_rec_end_date        DATE,
    i_item_desc           STRING,
    i_current_price       FLOAT64, 
    i_wholesale_cost      FLOAT64, 
    i_brand_id            INT64,
    i_brand               STRING,
    i_class_id            INT64,
    i_class               STRING,
    i_category_id         INT64,
    i_category            STRING,
    i_manufact_id         INT64,
    i_manufact            STRING,
    i_size                STRING,
    i_formulation         STRING,
    i_color               STRING,
    i_units               STRING,
    i_container           STRING,
    i_manager_id          INT64,
    i_product_name        STRING 

);




## 13. promotion

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.promotion` (
    p_promo_sk                INT64 NOT NULL,
    p_promo_id                STRING NOT NULL,
    p_start_date_sk           INT64, 
    p_end_date_sk             INT64, 
    p_item_sk                 INT64,
    p_cost                    FLOAT64,
    p_response_target         INT64,
    p_promo_name              STRING,
    p_channel_dmail           STRING,
    p_channel_email           STRING,
    p_channel_catalog         STRING,
    p_channel_tv              STRING,
    p_channel_radio           STRING,
    p_channel_press           STRING,
    p_channel_event           STRING,
    p_channel_demo            STRING,
    p_channel_details         STRING,
    p_purpose                 STRING,
    p_discount_active         STRING 
);




## 14. reason

CREATE or REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.reason` (
    r_reason_sk             INT64 NOT NULL,
    r_reason_id             STRING NOT NULL,
    r_reason_desc           STRING
);





## 15. ship_mode

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.ship_mode` (
    sm_ship_mode_sk           INT64 NOT NULL,
    sm_ship_mode_id           STRING NOT NULL,
    sm_type                   STRING,
    sm_code                   STRING,
    sm_carrier                STRING,
    sm_contract               STRING
);




## 16. store

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.store` (
    s_store_sk                INT64 NOT NULL,
    s_store_id                STRING NOT NULL,
    s_rec_start_date          DATE,
    s_rec_end_date            DATE,
    s_closed_date_sk          INT64,
    s_store_name              STRING,
    s_number_employees        INT64,
    s_floor_space             INT64,
    s_hours                   STRING,
    s_manager                 STRING,
    s_market_id               INT64,
    s_geography_class         STRING,
    s_market_desc             STRING,
    s_market_manager          STRING,
    s_division_id             INT64,
    s_division_name           STRING,
    s_company_id              INT64,
    s_company_name            STRING,
    s_street_number           STRING,
    s_street_name             STRING,
    s_street_type             STRING,
    s_suite_number            STRING,
    s_city                    STRING,
    s_county                  STRING,
    s_state                   STRING,
    s_zip                     STRING,
    s_country                 STRING,
    s_gmt_offset              FLOAT64, 
    s_tax_precentage          FLOAT64  
);





## 17. store_returns


CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.store_returns` (
    sr_returned_date_sk       INT64, 
    sr_return_time_sk         INT64, 
    sr_item_sk                INT64 NOT NULL,
    sr_customer_sk            INT64,
    sr_cdemo_sk               INT64,
    sr_hdemo_sk               INT64,
    sr_addr_sk                INT64,
    sr_store_sk               INT64,
    sr_reason_sk              INT64,
    sr_ticket_number 		  INT64 NOT NULL, 
    sr_return_quantity        INT64,
    sr_return_amt             FLOAT64, 
    sr_return_tax             FLOAT64, 
    sr_return_amt_inc_tax     FLOAT64, 
    sr_fee                    FLOAT64, 
    sr_return_ship_cost       FLOAT64, 
    sr_refunded_cash          FLOAT64, 
    sr_reversed_charge        FLOAT64, 
    sr_store_credit           FLOAT64, 
    sr_net_loss               FLOAT64  
);




## 18. store_sales

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.store_sales` (
    ss_sold_date_sk           INT64, 
    ss_sold_time_sk           INT64, 
    ss_item_sk                INT64 NOT NULL,
    ss_customer_sk            INT64,
    ss_cdemo_sk               INT64,
    ss_hdemo_sk               INT64,
    ss_addr_sk                INT64,
    ss_store_sk               INT64,
    ss_promo_sk               INT64,
    ss_ticket_number          INT64 NOT NULL, 
    ss_quantity               INT64,
    ss_wholesale_cost         FLOAT64, 
    ss_list_price             FLOAT64, 
    ss_sales_price            FLOAT64, 
    ss_ext_discount_amt       FLOAT64, 
    ss_ext_sales_price        FLOAT64, 
    ss_ext_wholesale_cost     FLOAT64, 
    ss_ext_list_price         FLOAT64, 
    ss_ext_tax                FLOAT64, 
    ss_coupon_amt             FLOAT64, 
    ss_net_paid               FLOAT64, 
    ss_net_paid_inc_tax       FLOAT64, 
    ss_net_profit             FLOAT64  
);





## 19. time_dim

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.time_dim` (
t_time_sk       INT64 NOT NULL,
t_time_id       STRING NOT NULL,
t_time          INT64,
t_hour          INT64,
t_minute        INT64,
t_second        INT64,
t_am_pm         STRING,
t_shift         STRING,
t_sub_shift     STRING,
t_meal_time     STRING
); 





## 20. warehouse

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.warehouse` (
w_warehouse_sk            INT64 NOT NULL,
w_warehouse_id            STRING NOT NULL,
w_warehouse_name          STRING,
w_warehouse_sq_ft         INT64,
w_street_number           STRING,
w_street_name             STRING,
w_street_type             STRING,
w_suite_number            STRING,
w_city					  STRING,
w_county                  STRING,
w_state                   STRING,
w_zip                     STRING,
w_country                 STRING,
w_gmt_offset              FLOAT64
);






## 21. web_page

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.web_page` (
    wp_web_page_sk 			INT64 NOT NULL,
    wp_web_page_id 			STRING NOT NULL,
    wp_rec_start_date 		DATE,
    wp_rec_end_date 		DATE,
    wp_creation_date_sk 	INT64,
    wp_access_date_sk 		INT64,
    wp_autogen_flag 		STRING,
    wp_customer_sk 			INT64,
    wp_url 					STRING,
    wp_type 				STRING,
    wp_char_count 			INT64,
    wp_link_count 			INT64,
    wp_image_count 			INT64,
    wp_max_ad_count 		INT64
);





## 22. web_returns

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.web_returns` (
    wr_returned_date_sk INT64,
    wr_returned_time_sk INT64,
    wr_item_sk INT64 NOT NULL,
    wr_refunded_customer_sk INT64,
    wr_refunded_cdemo_sk INT64,
    wr_refunded_hdemo_sk INT64,
    wr_refunded_addr_sk INT64,
    wr_returning_customer_sk INT64,
    wr_returning_cdemo_sk INT64,
    wr_returning_hdemo_sk INT64,
    wr_returning_addr_sk INT64,
    wr_web_page_sk INT64,
    wr_reason_sk INT64,
    wr_order_number INT64 NOT NULL,
    wr_return_quantity INT64,
    wr_return_amt FLOAT64, 
    wr_return_tax FLOAT64,
    wr_return_amt_inc_tax FLOAT64,
    wr_fee FLOAT64,
    wr_return_ship_cost FLOAT64,
    wr_refunded_cash FLOAT64,
    wr_reversed_charge FLOAT64,
    wr_account_credit FLOAT64,
    wr_net_loss FLOAT64 
);





## 23. web_sales

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.web_sales` (
    ws_sold_date_sk           INT64,
    ws_sold_time_sk           INT64,
    ws_ship_date_sk           INT64,
    ws_item_sk                INT64 NOT NULL,
    ws_bill_customer_sk       INT64,
    ws_bill_cdemo_sk          INT64,
    ws_bill_hdemo_sk          INT64,
    ws_bill_addr_sk           INT64,
    ws_ship_customer_sk       INT64, 
    ws_ship_cdemo_sk          INT64,
    ws_ship_hdemo_sk          INT64,
    ws_ship_addr_sk           INT64,
    ws_web_page_sk            INT64,
    ws_web_site_sk            INT64,
    ws_ship_mode_sk           INT64,
    ws_warehouse_sk           INT64,
    ws_promo_sk               INT64,
    ws_order_number           INT64 NOT NULL,
    ws_quantity               INT64,
    ws_wholesale_cost         FLOAT64, 
    ws_list_price             FLOAT64,
    ws_sales_price            FLOAT64,
    ws_ext_discount_amt       FLOAT64,
    ws_ext_sales_price        FLOAT64,
    ws_ext_wholesale_cost     FLOAT64,
    ws_ext_list_price         FLOAT64,
    ws_ext_tax                FLOAT64,
    ws_coupon_amt             FLOAT64,
    ws_ext_ship_cost          FLOAT64,
    ws_net_paid               FLOAT64,
    ws_net_paid_inc_tax       FLOAT64,
    ws_net_paid_inc_ship      FLOAT64,
    ws_net_paid_inc_ship_tax  FLOAT64,
    ws_net_profit             FLOAT64 
);






## 24. web_site

CREATE OR REPLACE TABLE `dataproc-pp-benchmark.tpc_ds_1TB.web_site` (
  web_site_sk               INT64 NOT NULL,
  web_site_id               STRING NOT NULL,
  web_rec_start_date        DATE,
  web_rec_end_date          DATE,
  web_name                  STRING,
  web_open_date_sk          INT64,
  web_close_date_sk         INT64,
  web_class                 STRING,
  web_manager               STRING,
  web_mkt_id                INT64,
  web_mkt_class             STRING,
  web_mkt_desc              STRING,
  web_market_manager        STRING,
  web_company_id            INT64,
  web_company_name          STRING,
  web_street_number         STRING,
  web_street_name           STRING,
  web_street_type           STRING,
  web_suite_number          STRING,
  web_city                  STRING,
  web_county                STRING,
  web_state                 STRING,
  web_zip                   STRING,
  web_country               STRING,
  web_gmt_offset            FLOAT64,  
  web_tax_percentage        FLOAT64 
);




