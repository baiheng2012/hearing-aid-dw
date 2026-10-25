from pathlib import Path 
import pandas as pd 
RAW_DIR = Path("data/raw")


def extract(raw_dir:Path) -> pd.DataFrame:
    """read all raw sources and return one combined dataframe with a sourcefiel column"""
    df_csv = pd.read_csv(raw_dir / "test_records.csv", dtype=str)
    df_csv["source_file"] = "test_records.csv"
    df_json = pd.read_json(raw_dir / "test_records.json", dtype=False)
    
    df_json = df_json.astype("string")
    #df_json = pd.read_json(raw_dir / "test_records.json", dtype=str, convert_dates=False)
    df_json["source_file"] = "test_records.json"
    #print((df_json["gain_db"] == "nan").sum(), (df_json["gain_db"] == "None").sum())
    df = pd.concat([df_csv, df_json], ignore_index=True)
    return df


if __name__ == "__main__":
    df = extract(RAW_DIR)
  #  print(df.shape)
   # print(df["source_file"].value_counts())
    #print(df.dtypes)
    #print(df.isna().sum())
    #print((df["gain_db"] == "nan").sum())
    #print(df["test_time"].map(type).value_counts())
    #print((df["defect_code"] == "").sum(), df["defect_code"].isna().sum())
    print(df["test_time"].map(type).value_counts())   # 只应有 str 一类
    print((df["gain_db"] == "nan").sum())             # 0
    print(df["gain_db"].isna().sum())                 # 114