# FraudGuard internal fraud & AML policy (fictional, for this project)

## R1 Card testing
Many small online payments (typically under 5 EUR) from one card within a few minutes indicate card testing: criminals checking whether stolen card details work. More than 5 payments in 10 minutes must be flagged. Action: block the card and contact the customer.

## R2 Foreign ATM cash-out
A large ATM withdrawal (more than 5 times the customer's usual spend) in a country other than the customer's home country suggests a stolen or skimmed card. Action: temporarily block cash withdrawals and verify with the customer.

## R3 Unusual amount
A payment far above the customer's typical amount is a risk signal, but not proof of fraud on its own. Combine it with other signals such as channel, country and timing before escalating.

## R4 Structuring
Splitting a large sum into many payments just below a reporting threshold to avoid controls is called structuring (smurfing). Repeated payments just under 10,000 EUR within days must be reported to the compliance team.

## R5 Escalation and reporting
Confirmed or strongly suspected money laundering must be escalated to the compliance officer, who decides whether to file a suspicious activity report (SAR) with the authorities. Investigators must never tell the customer that a SAR is being considered (no tipping off).

## R6 Evidence standard
Every investigation report must state the facts it relies on (transaction IDs, amounts, times, countries) and the policy rules that apply. Unsupported claims are not allowed.
