with bronze as (
    select * from delta_scan('s3://lakehouse/bronze/transactions')
)

select
    json_extract_string(raw_json, '$.transaction_id')                 as transaction_id,
    account_id,
    json_extract_string(raw_json, '$.merchant_id')                    as merchant_id,
    cast(json_extract_string(raw_json, '$.amount') as decimal(12, 2)) as amount,
    json_extract_string(raw_json, '$.currency')                       as currency,
    cast(json_extract_string(raw_json, '$.timestamp') as timestamptz) as transaction_at,
    json_extract_string(raw_json, '$.channel')                            as channel,
    json_extract_string(raw_json, '$.country')                            as country,
    kafka_timestamp,
    ingested_at
from bronze

qualify row_number() over (partition by transaction_id order by kafka_timestamp) = 1
