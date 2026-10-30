-- One row per day, channel and country: what the fraud dashboard reads
with tx as (select * from {{ ref('stg_transactions') }}),
     labels as (select * from {{ ref('stg_fraud_labels') }})

select
    cast(timezone('UTC', tx.transaction_at) as date)   as day,  -- UTC days, same on every machine
    tx.channel,
    tx.country,
    count(*)                                      as transactions,
    count_if(labels.is_fraud)                     as frauds,
    round(count_if(labels.is_fraud) / count(*), 4) as fraud_rate,
    round(sum(tx.amount), 2)                      as total_amount,
from tx
left join labels using (transaction_id)  -- left: a payment without a label yet still counts
group by all
