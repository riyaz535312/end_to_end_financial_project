import pandas as pd
import numpy as np
import os


file_path= "C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\raw\\PS_20174392719_log.csv"

df=pd.read_csv(file_path)

transactions=df.rename(columns={
    "step":"transaction_step",
    "type": "transaction_type",
    "amount": "amount",
    "nameOrig": "source_account_id",
    "nameDest": "destination_account_id",
    "oldbalanceOrg": "source_balance_before",
    "newbalanceOrig": "source_balance_after",
    "oldbalanceDest": "destination_balance_before",
    "newbalanceDest": "destination_balance_after",
    "isFraud": "fraud_ground_truth",
    "isFlaggedFraud": "fraud_rule_flag"
})

#DataFrame index
#      ↓
#     25
#      ↓
# convert to string
#     "25"
#      ↓
# add zeros until length = 10
# "0000000025"
#      ↓
# add "TXN"
#"TXN0000000025"

transactions["transaction_id"]=(
    "TXN" +
    transactions.index.astype(str).str.zfill(10)
)

start_date=pd.Timestamp("2026-10-08")

transactions['transaction_timestamp']=(
    start_date +
    pd.to_timedelta(transactions['transaction_step'],unit="h")
)

print("Transaction \n ",transactions.head())

#####################################
# Create Customer Data

number_of_customers=100_000

customers=pd.DataFrame({
    "customer_id" : [
        f"CUS{i:07d}" for i in range(1, number_of_customers +1)
    ],
     "customer_name": [
        f"Customer_{i}"
        for i in range(1, number_of_customers + 1)
    ],

    "city": np.random.choice(
        ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai","Kochi"],
        number_of_customers
    ),

    "customer_segment": np.random.choice(
        ["STANDARD", "PREMIUM", "VIP"],
        number_of_customers,
        p=[0.70, 0.25, 0.05]
    )
})

print("customer \n",customers.head())

###########################################
# CREATE ACCOUNTS DATA 

#number_of_accounts=150_000

source_accounts=pd.concat([
    transactions['source_account_id'],transactions['destination_account_id']
]).drop_duplicates()

accounts=pd.DataFrame({

    "account_id" : source_accounts ,
    #[
    #    f"ACC{i:08d}" for i in range(1,number_of_accounts + 1 )
    #],


    "customer_id" : np.random.choice(
        customers['customer_id'],len(source_accounts)
    ),

     "account_type": np.random.choice(
        ["SAVINGS", "CURRENT"],
        len(source_accounts),
        p=[0.8, 0.2]
    ),

    "account_status": np.random.choice(
        ["ACTIVE", "BLOCKED", "CLOSED"],
        len(source_accounts),
        p=[0.95, 0.03, 0.02]
    )

})

print("Accounts \n ",accounts.head())


########################################
# Create merchants

number_of_merchants=10_000

merchants =pd.DataFrame({
    "merchant_id" : [
        f"MER{i:06d}" for i in range(1,number_of_merchants +1 )
    ],
    "merchant_name" : [
        f"Merchant_{i}" for i in range(1,number_of_merchants +1)
    ],
    "merchant_category" : np.random.choice(
        [
            "E_COMMERCE",
            "GROCERY",
            "TRAVEL",
            "RESTAURANT",
            "FUEL",
            "ENTERTAINMENT"
        ], number_of_merchants
    )
})

print("Merchants \n ",merchants.head())

### Connect transactions to merchants
transactions['merchant_id']=np.random.choice(
    merchants['merchant_id'],len(transactions)
)

print(transactions.head())

#####################
#  Create the Fraud System

fraud_transactions=transactions[transactions['fraud_ground_truth'] ==1 ].copy()

fraud_events=pd.DataFrame({
    "fraud_event_id": [
        f"FRD{i:08d}" for i in range(1, len(fraud_transactions) + 1)
    ],
    "transaction_id":fraud_transactions["transaction_id"].values,
    "risk_score" : np.random.uniform(
        0.89,
        0.99,
        len(fraud_transactions)
    ),
    "risk_reason": np.random.choice(
         [
            "UNUSUAL_AMOUNT",
            "UNUSUAL_TRANSFER",
            "ACCOUNT_ANOMALY",
            "SUSPICIOUS_PATTERN"
        ],
        len(fraud_transactions)
    ),
    "investigation_status": "OPEN"
})

print(fraud_events.head())

print("Transactions:", len(transactions))
print("Customers:", len(customers))
print("Accounts:", len(accounts))
print("Merchants:", len(merchants))
print("Fraud Events:", len(fraud_events))



#---------
# Unique originators and destinations
unique_sources = transactions["source_account_id"].nunique()
unique_destinations = transactions["destination_account_id"].nunique()

# Overlap between source and destination identifiers
source_ids = set(transactions["source_account_id"].dropna())
destination_ids = set(transactions["destination_account_id"].dropna())

print("Unique source IDs:", f"{unique_sources:,}")
print("Unique destination IDs:", f"{unique_destinations:,}")
print("IDs appearing in both columns:", f"{len(source_ids & destination_ids):,}")
print("Unique IDs across both columns:", f"{len(source_ids | destination_ids):,}")

# Validate the account master
print("Account rows:", f"{len(accounts):,}")
print("Unique account IDs:", f"{accounts['account_id'].nunique():,}")
print("Duplicate account IDs:", f"{accounts['account_id'].duplicated().sum():,}")

# Inspect identifier patterns
print(
    transactions["source_account_id"]
    .astype("string")
    .str[0]
    .value_counts(dropna=False)
)

print(
    transactions["destination_account_id"]
    .astype("string")
    .str[0]
    .value_counts(dropna=False)
)
# --------------

#################################
## simulate daily files
#
#transactions["transaction_date"]=transactions["transaction_timestamp"].dt.date
#
#for transaction_date,daily_data_group in transactions.groupby('transaction_date'):
#    # directory path (without the file name)
#    output_dir=f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\transactions\\{transaction_date}"
#
#    os.makedirs(output_dir, exist_ok=True) ## make sure the folder exists
#
#    output_path=f"{output_dir}\\transactions.csv"
#
#    daily_data_group.to_csv(
#        output_path,
#        index=False  ## to eliminate the pandas df index column
#    )
#

########################
# create different formats for all the tables

# creating single transaction file

"""
# to csv

os.makedirs(f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\transactions\\",exist_ok=True)

transactions.to_csv(
    f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\transactions\\transactions.csv",
    index=False
)

#to json 
 # creating folders for the files
os.makedirs(f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\customers\\",exist_ok=True)

customers.to_json(
    f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\customers\\customers.json",
    orient="records",
    lines=True
)

os.makedirs(f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\fraud_events\\",exist_ok=True)

fraud_events.to_json(
    f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\fraud_events\\fraud_events.json",
    orient="records",
    lines=False
)

#to parquet

os.makedirs(f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\accounts\\",exist_ok=True)

accounts.to_parquet(
    f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\accounts\\accounts.parquet",
    index=False
)

# to csv

os.makedirs(f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\merchants\\",exist_ok=True)

merchants.to_csv(
    f"C:\\Users\\Admin\\OneDrive\\Documents\\MyProjects\\data\\generated\\merchants\\merchants.csv",
    index=False
)

"""
