with tx as (select * from {{ ref('stg_transactions') }}),
     labels as (select * from {{ ref('stg_fraud_labels') }})

select
    tx.transaction_id,
    tx.transaction_at,
    tx.amount,
    tx.channel,
    -- compare with this account's PAST payments only (1 preceding = exclude the current one)
    tx.amount / coalesce(
        avg(tx.amount) over (partition by tx.account_id order by tx.transaction_at
                             rows between unbounded preceding and 1 preceding),
        tx.amount)                                                       as amount_vs_account_avg,
    -- how many payments this account made in the last 10 minutes
    count(*) over (partition by tx.account_id order by tx.transaction_at
                   range between interval 10 minutes preceding and current row) as tx_last_10min,
    tx.country <> case tx.currency when 'EUR' then 'DE' when 'USD' then 'US'
                                   when 'EGP' then 'EG' end              as is_foreign,
    labels.is_fraud                                                           as is_fraud
from tx
join labels using (transaction_id)
