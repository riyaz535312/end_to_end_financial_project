"""
02_inject_bad_data.py

Create reproducible, intentionally corrupted copies of the clean datasets.
This script NEVER writes to data/generated; it writes only to data/test_input.

Before running:
1. Make sure the clean generated files exist.
2. Update BASE below to your actual MyProjects\data folder.
3. Run: python scripts/02_inject_bad_data.py
"""

import os
import pandas as pd
import numpy as np


# --------------------------------------------------
# 1. PATHS
# --------------------------------------------------

BASE = (
    r"C:\\MyProjects"
    r"\MyProjects\data"
)

GENERATED = os.path.join(BASE, "generated")
TEST_INPUT = os.path.join(BASE, "test_input")

# Fixed seed means the same row selections are used when the clean
# input files and their row order remain unchanged.
SEED = 42
rng = np.random.default_rng(SEED)

TABLE_DIRS = [
    "transactions",
    "customers",
    "accounts",
    "merchants",
    "fraud_events",
]

for table in TABLE_DIRS:
    os.makedirs(os.path.join(TEST_INPUT, table), exist_ok=True)


# --------------------------------------------------
# 2. HELPERS
# --------------------------------------------------

def require_file(path):
    """Stop early with a clear message if a clean input is missing."""
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Required clean input was not found:\n{path}\n"
            "Run your clean data-generation script first, and check BASE."
        )


def select_rows(df, count, random_generator, exclude=None):
    """
    Return distinct integer row positions.
    If there are fewer available rows than requested, select the available
    number and print a warning. Works safely for small fraud-event datasets.
    """
    excluded = set() if exclude is None else set(exclude)
    available = np.fromiter(
        (i for i in range(len(df)) if i not in excluded),
        dtype=np.int64,
    )

    actual_count = min(count, len(available))
    if actual_count < count:
        print(
            f"WARNING: requested {count:,} rows, but only "
            f"{actual_count:,} are available."
        )

    if actual_count == 0:
        return np.array([], dtype=np.int64)

    return random_generator.choice(
        available, size=actual_count, replace=False
    )


def inject_duplicate_keys(df, key_column, count, random_generator,
                          already_used, clean_df, table_name):
    """
    Make `count` rows reuse keys from different, untouched donor rows.
    This creates duplicate-key defects, not full duplicate records.
    Returns target row positions.
    """
    targets = select_rows(
        df, count, random_generator, already_used
    )
    already_used.update(targets)

    # Donors are selected outside the target/previously-corrupted rows.
    donors = select_rows(
        df, len(targets), random_generator, already_used
    )

    if len(targets):
        df.loc[targets, key_column] = (
            clean_df.iloc[donors][key_column].to_numpy()
        )

    print(
        f"{table_name}: duplicate {key_column} keys injected: "
        f"{len(targets):,}"
    )
    return targets


def inject_scenario(df, column, value, count, random_generator,
                    already_used, scenario_name):
    """Apply one issue to distinct rows within this table."""
    rows = select_rows(
        df, count, random_generator, already_used
    )
    already_used.update(rows)

    if len(rows):
        df.loc[rows, column] = value

    print(f"{scenario_name}: {len(rows):,} rows affected")
    return rows


def save_outputs(transactions, customers, accounts, merchants, fraud_events):
    """Save only corrupted test copies, never the clean generated files."""
    transactions.to_csv(
        os.path.join(
            TEST_INPUT, "transactions", "transactions_with_issues.csv"
        ),
        index=False,
    )

    customers.to_json(
        os.path.join(
            TEST_INPUT, "customers", "customers_with_issues.json"
        ),
        orient="records",
        lines=True,
    )

    accounts.to_parquet(
        os.path.join(
            TEST_INPUT, "accounts", "accounts_with_issues.parquet"
        ),
        index=False,
    )

    merchants.to_csv(
        os.path.join(
            TEST_INPUT, "merchants", "merchants_with_issues.csv"
        ),
        index=False,
    )

    fraud_events.to_json(
        os.path.join(
            TEST_INPUT, "fraud_events", "fraud_events_with_issues.json"
        ),
        orient="records",
        lines=False,
    )


# --------------------------------------------------
# 3. CHECK AND LOAD CLEAN INPUT FILES
# --------------------------------------------------

input_paths = {
    "transactions": os.path.join(
        GENERATED, "transactions", "transactions.csv"
    ),
    "customers": os.path.join(
        GENERATED, "customers", "customers.json"
    ),
    "accounts": os.path.join(
        GENERATED, "accounts", "accounts.parquet"
    ),
    "merchants": os.path.join(
        GENERATED, "merchants", "merchants.csv"
    ),
    "fraud_events": os.path.join(
        GENERATED, "fraud_events", "fraud_events.json"
    ),
}

for path in input_paths.values():
    require_file(path)

transactions_clean = pd.read_csv(input_paths["transactions"])
customers_clean = pd.read_json(input_paths["customers"], lines=True)
accounts_clean = pd.read_parquet(input_paths["accounts"])
merchants_clean = pd.read_csv(input_paths["merchants"])
fraud_events_clean = pd.read_json(input_paths["fraud_events"])

# Normalize row positions so integer positions and .loc are aligned.
transactions_clean = transactions_clean.reset_index(drop=True)
customers_clean = customers_clean.reset_index(drop=True)
accounts_clean = accounts_clean.reset_index(drop=True)
merchants_clean = merchants_clean.reset_index(drop=True)
fraud_events_clean = fraud_events_clean.reset_index(drop=True)

# Make working copies. All donor keys come from the clean snapshots.
transactions = transactions_clean.copy()
customers = customers_clean.copy()
accounts = accounts_clean.copy()
merchants = merchants_clean.copy()
fraud_events = fraud_events_clean.copy()

print("\nCLEAN INPUT ROW COUNTS")
for name, df in {
    "transactions": transactions,
    "customers": customers,
    "accounts": accounts,
    "merchants": merchants,
    "fraud_events": fraud_events,
}.items():
    print(f"{name:15s}: {len(df):,}")


# --------------------------------------------------
# 4. TRANSACTION ISSUES
# --------------------------------------------------

transaction_used = set()

inject_scenario(
    transactions, "transaction_id", None, 500, rng,
    transaction_used, "Transactions / missing transaction_id"
)

inject_scenario(
    transactions, "amount", -999999, 500, rng,
    transaction_used, "Transactions / invalid negative amount"
)

inject_scenario(
    transactions, "transaction_type", "UNKNOWN_TYPE", 500, rng,
    transaction_used, "Transactions / invalid transaction_type"
)

inject_scenario(
    transactions, "source_account_id", "ACC_UNKNOWN_999", 500, rng,
    transaction_used, "Transactions / unknown source account"
)

inject_scenario(
    transactions, "destination_account_id", "ACC_UNKNOWN_998", 500, rng,
    transaction_used, "Transactions / unknown destination account"
)

inject_scenario(
    transactions, "merchant_id", "MER_UNKNOWN_999999", 500, rng,
    transaction_used, "Transactions / unknown merchant"
)

inject_duplicate_keys(
    transactions, "transaction_id", 1000, rng,
    transaction_used, transactions_clean, "Transactions"
)


# --------------------------------------------------
# 5. CUSTOMER ISSUES
# --------------------------------------------------

customer_used = set()

inject_scenario(
    customers, "customer_name", None, 300, rng,
    customer_used, "Customers / missing customer_name"
)

inject_scenario(
    customers, "customer_segment", "UNKNOWN_SEGMENT", 200, rng,
    customer_used, "Customers / invalid customer_segment"
)

inject_duplicate_keys(
    customers, "customer_id", 300, rng,
    customer_used, customers_clean, "Customers"
)


# --------------------------------------------------
# 6. ACCOUNT ISSUES
# --------------------------------------------------

account_used = set()

inject_scenario(
    accounts, "customer_id", "CUS9999999", 300, rng,
    account_used, "Accounts / orphan customer reference"
)

inject_scenario(
    accounts, "account_status", "UNKNOWN_STATUS", 200, rng,
    account_used, "Accounts / invalid account_status"
)

inject_duplicate_keys(
    accounts, "account_id", 300, rng,
    account_used, accounts_clean, "Accounts"
)


# --------------------------------------------------
# 7. MERCHANT ISSUES
# --------------------------------------------------

merchant_used = set()

inject_scenario(
    merchants, "merchant_category", "UNKNOWN_CATEGORY", 100, rng,
    merchant_used, "Merchants / invalid merchant_category"
)

inject_scenario(
    merchants, "merchant_name", None, 100, rng,
    merchant_used, "Merchants / missing merchant_name"
)

inject_duplicate_keys(
    merchants, "merchant_id", 100, rng,
    merchant_used, merchants_clean, "Merchants"
)


# --------------------------------------------------
# 8. FRAUD EVENT ISSUES
# --------------------------------------------------

fraud_used = set()

inject_scenario(
    fraud_events, "risk_score", 1.50, 100, rng,
    fraud_used, "Fraud events / risk_score outside 0-1"
)

inject_scenario(
    fraud_events, "investigation_status", "UNKNOWN_STATUS", 100, rng,
    fraud_used, "Fraud events / invalid investigation_status"
)

inject_scenario(
    fraud_events, "transaction_id", "TXN_DOES_NOT_EXIST", 100, rng,
    fraud_used, "Fraud events / orphan transaction reference"
)

inject_duplicate_keys(
    fraud_events, "fraud_event_id", 100, rng,
    fraud_used, fraud_events_clean, "Fraud events"
)


# --------------------------------------------------
# 9. SAVE CORRUPTED TEST INPUTS
# --------------------------------------------------

save_outputs(
    transactions, customers, accounts, merchants, fraud_events
)

print("\nTEST INPUT FILES SAVED")
for table in TABLE_DIRS:
    print(f"{table:15s}: {os.path.join(TEST_INPUT, table)}")


# --------------------------------------------------
# 10. BASIC POST-INJECTION SUMMARY
# --------------------------------------------------

print("\nPOST-INJECTION SUMMARY")
print(
    "Transactions missing IDs:",
    int(transactions["transaction_id"].isna().sum()),
)
print(
    "Transactions with negative amounts:",
    int((transactions["amount"] < 0).sum()),
)
print(
    "Duplicate transaction ID rows (includes all members of groups):",
    int(transactions["transaction_id"].duplicated(keep=False).sum()),
)
print(
    "Duplicate customer ID rows:",
    int(customers["customer_id"].duplicated(keep=False).sum()),
)
print(
    "Duplicate account ID rows:",
    int(accounts["account_id"].duplicated(keep=False).sum()),
)
print(
    "Duplicate merchant ID rows:",
    int(merchants["merchant_id"].duplicated(keep=False).sum()),
)
print(
    "Duplicate fraud_event_id rows:",
    int(fraud_events["fraud_event_id"].duplicated(keep=False).sum()),
)

print(
    "\nDone. Clean files in 'generated' were not overwritten. "
    "Point your pipeline test run to 'test_input'."
)
