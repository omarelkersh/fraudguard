select
    account_id,
    any_value(currency)  as currency,
    min(transaction_at)  as first_seen_at,
    count(*)             as transaction_count
from {{ ref('stg_transactions') }}
group by account_id
