from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

def line_plot(df:pd.DataFrame, x:str, y:str, title:str, path:Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12,4)); plt.plot(df[x],df[y]); plt.title(title); plt.tight_layout(); plt.savefig(path); plt.close()
