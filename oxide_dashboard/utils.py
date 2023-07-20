import pandas as pd
import numpy as np

def equiatomic(metals):
    return np.ones(len(metals)) / len(metals)

def display_data(df, num_display = None, top_unique = None):
    #pd.set_option("display.max_rows", None, "display.max_columns", None)
    if top_unique is not None:
        new_df = pd.concat([df.iloc[:top_unique], ((df.iloc[top_unique:]).drop_duplicates(subset=['Material ID']))])
    else:
        new_df = df.copy(deep = True)
    if num_display is None or len(df) < num_display:
        return new_df
    else:
        return new_df.head(num_display)



def alloy_composition_to_string(METALS,COMPS):
    compformat = "_".join("{0}({1:.3f})".format(i, round(j, 3)) for i, j in zip(METALS, COMPS))
    return compformat
