with bronze as (
    select * from delta_scan('s3://lakehouse/bronze/fraud_labels')
)

select
    transaction_id,
    cast(json_extract_string(raw_json, '$.is_fraud') as boolean)      as is_fraud,
    cast(json_extract_string(raw_json, '$.labelled_at') as timestamptz)       as labelled_at
from bronze
qualify row_number() over (partition by transaction_id order by kafka_timestamp) = 1
