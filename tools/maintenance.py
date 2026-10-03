from __future__ import annotations
import pandas as pd

def load_parts(path_or_buffer):
    return pd.read_csv(path_or_buffer)

def lookup_parts(parts_df, keywords):
    if parts_df is None or parts_df.empty: return []
    text=parts_df.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    hits=[]
    for i,row in parts_df.iterrows():
        blob=text.iloc[i]
        if any(str(k).lower() in blob for k in keywords):
            hits.append(row.to_dict())
    return hits
