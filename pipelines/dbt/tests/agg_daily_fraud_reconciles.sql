-- The dashboard mart must count every payment exactly once
select mart.total, fact.total
from (select sum(transactions) as total from {{ ref('agg_daily_fraud') }}) as mart,
     (select count(*) as total from {{ ref('fct_transactions') }}) as fact
where mart.total <> fact.total
