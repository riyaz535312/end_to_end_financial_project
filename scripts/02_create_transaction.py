import pandas as pd
import numpy as np


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