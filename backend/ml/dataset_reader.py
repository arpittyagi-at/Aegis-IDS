"""Dataset readers for streaming real data samples."""

import pandas as pd
import numpy as np
from pathlib import Path


class DatasetReader:
    """Streams real dataset samples row by row."""
    
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.current_row = 0
        self.df = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load the dataset for streaming."""
        base_path = Path(__file__).parent.parent.parent / "datasets"
        
        try:
            if self.dataset_name == "ciciot":
                files = sorted((base_path / "ciciot").glob("**/*.csv"))
                if not files:
                    self.df = pd.DataFrame()
                    return
                self.df = pd.concat(
                    [pd.read_csv(path, nrows=4000) for path in files[:3]],
                    ignore_index=True,
                )
                # Drop non-numeric columns
                for col in ["Dst IP", "Src IP", "Timestamp"]:
                    if col in self.df.columns:
                        self.df = self.df.drop(columns=[col])
                # Convert to numeric
                self.df = self.df.apply(pd.to_numeric, errors="coerce").fillna(0)
                
            elif self.dataset_name == "nslkdd":
                # Load both train and test
                train_path = base_path / "nslkdd" / "KDDTrain+.txt"
                test_path = base_path / "nslkdd" / "KDDTest+.txt"
                if not train_path.exists() or not test_path.exists():
                    self.df = pd.DataFrame()
                    return
                NSL_KDD_COLS = [
                    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
                    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
                    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
                    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
                    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
                    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
                    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
                    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
                    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
                    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty_level"
                ]
                df_train = pd.read_csv(train_path, header=None, names=NSL_KDD_COLS)
                df_test = pd.read_csv(test_path, header=None, names=NSL_KDD_COLS)
                self.df = pd.concat([df_train, df_test], ignore_index=True)
                # Encode categoricals
                for col in ["protocol_type", "service", "flag"]:
                    self.df[col] = pd.factorize(self.df[col])[0]
                # Drop non-numeric
                self.df = self.df.select_dtypes(include=[np.number])
                
            elif self.dataset_name == "unswnb15":
                # Load UNSW files
                dfs = []
                for i in range(1, 5):
                    path = base_path / "unswnb15" / f"UNSW-NB15_{i}.csv"
                    if path.exists():
                        df = pd.read_csv(path, nrows=5000)  # Limit per file
                        dfs.append(df)
                self.df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                # Convert to numeric
                self.df = self.df.apply(pd.to_numeric, errors="coerce").fillna(0)
                
            elif self.dataset_name == "cicids2017":
                # Load CIC-IDS 2017 files
                dfs = []
                for path in sorted((base_path / "cicids2017").glob("*.csv")):
                    df = pd.read_csv(path, nrows=5000)  # Limit per file
                    dfs.append(df)
                self.df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                # Convert to numeric
                self.df = self.df.apply(pd.to_numeric, errors="coerce").fillna(0)
        except Exception:
            self.df = pd.DataFrame()
            return
        
        if self.df is not None and len(self.df) > 0:
            # Drop label column if present (we'll handle labels separately)
            label_col = None
            for col in self.df.columns:
                if 'label' in col.lower():
                    label_col = col
                    break
            if label_col and label_col in self.df.columns:
                self.df = self.df.drop(columns=[label_col])
    
    def next_sample(self) -> dict:
        """Get next sample as a feature dict."""
        if self.df is None or len(self.df) == 0:
            return {}
        
        # Wrap around if at end
        if self.current_row >= len(self.df):
            self.current_row = 0
        
        row = self.df.iloc[self.current_row].to_dict()
        self.current_row += 1
        return row
    
    def reset(self):
        """Reset to start of dataset."""
        self.current_row = 0
