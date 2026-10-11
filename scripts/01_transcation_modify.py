import pandas as pd

file_path=r"C:\\MyProjects\\data\\raw\\PS_20174392719_log.csv"
#file_path="C:/Users/Admin/OneDrive/Documents/MyProjects/data/raw/PS_20174392719_log.csv"

df=pd.read_csv(file_path)

#print("rows",len(df))
#print("columns",len(df.columns))
print("rows",df.shape[0])
print("columns",df.shape[1])
print("\n column names")
print(df.columns.tolist())
print(df.dtypes)
print(df.isnull().sum())
print("\n Is fraud column")
print(df['isFraud'].value_counts())
print("\n Type(transactions) column")
print(df.type.value_counts())
print(df.step.value_counts())

# to load data into chunks
for chunk in pd.read_csv(file_path, chunksize=100000):
    print(len(chunk))
