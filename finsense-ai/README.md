# FinSense AI

**Financial intelligence that explains itself.** Upload a transaction CSV and FinSense tells you
not just *what* happened to your money, but *why* — every score, flag and label shows its evidence.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the app, create an account on the login page, then load your own CSV, the demo year, or five years
of sample data.

**Accounts** are stored locally in `.data/users.json` (git-ignored). Passwords are salted and hashed with
PBKDF2-HMAC-SHA256 — never stored as typed — and five wrong attempts lock the form for a minute. Delete that
file to remove every account.

## What makes it different

| Feature | What it does | How |
|---|---|---|
| **Anomaly radar** | Flags *your* unusual spending with plain-language reasons ("2.2× your typical Utilities spend", "possible duplicate charge") | Isolation Forest on 8 behavioural features + robust (median/MAD) z-score per category |
| **Explainable health score** | 0–100 score from six habits, with a waterfall showing where each lost point went and what wins it back | Savings power, spending control, positive months, income stability, spending steadiness, safety runway |
| **What-if lab** | Move sliders (cut Travel 30%, new EMI, salary +10%) and watch your future change | Monte Carlo — 3,000 simulated futures from a damped trend + your own historical volatility; shows the likely range and goal odds |
| **Money personality** | Behavioural archetype — Weekend Splurger, Payday Spender, Festive Season Spender (Diwali), Month-End Juggler… | Timing/shape signals from transactions; every trait quotes its evidence |
| **Report** | One-page HTML report to share or print to PDF | — |
| **Fraud lab** | Scores payments for fraud and explains each flag in plain words | Random Forest on PaySim mobile payments (explainable) or the Kaggle card dataset |

## Test files (`sample_data/`)

- `demo_transactions.csv` — one year for a salaried person in Bangalore, with planted patterns
  (a ₹9,800 electricity bill, a duplicate Amazon charge, a ₹58,000 laptop, Diwali spending,
  weekend and payday habits). Upload it on **Your data**.
- `payments_fraud_test.csv` — 3,150 mobile payments (150 frauds) from PaySim, held out from
  training, with the true `isFraud` column. Upload it on **Fraud lab** — every flag is explained in
  plain words ("emptied the sender's account", "the money never arrived").
- `card_fraud_test.csv` — 1,995 card transactions (95 frauds) from the Kaggle card model's
  held-out split, with the true `Class` column. Also works on **Fraud lab**, but its V1–V28
  columns are anonymised, so reasons can only name the signal.

Retrain the payment model with `python src/train_paysim_fraud.py` (needs `datasets/raw/paysim.csv`).

## CSV format

`Date, Category, Amount, Type` (Type = `Income` or `Expense`). Optional `Description`.

## Layout

```
app.py                 entry point: home + login when signed out, the app when signed in
finsense/
  auth.py              local accounts (salted PBKDF2 hashes, lockout)
  data.py              loading, validation, monthly aggregates, ₹ formatting
  health.py            explainable health score
  anomaly.py           personal anomaly radar
  forecast.py          Monte Carlo forecast + scenario engine
  personality.py       behavioural traits & archetype
  charts.py, theme.py  Plotly charts and the "Savings Passbook" visual theme
  views/               one module per page
src/                   offline training / research scripts
models/                trained fraud models
datasets/              raw + processed data (large files are git-ignored)
```

The large Kaggle files (`creditcard.csv`, `paysim.csv`) are git-ignored; download them from Kaggle
to re-run the training scripts in `src/`.
