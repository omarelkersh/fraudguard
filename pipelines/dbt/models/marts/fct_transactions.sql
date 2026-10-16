select
    transaction_id,
    account_id,
    merchant_id,
    transaction_at,
    amount,
    currency,
    channel,
    country
from {{ ref('stg_transactions') }}
