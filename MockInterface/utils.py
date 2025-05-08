import pandas as pd
import numpy as np
import typing
import csv
from collections.abc import Iterable

def extract_statistics(cols: list, rows: list):
    """
    Function extract_statistics that takes a dataframe and extracts the follwing:

    Params:
        cols (list): column names of the dataset.
        rows (list): row data of the dataset.

    """
    df = pd.DataFrame(rows, columns=cols)

    null_values = df.isnull().sum()
    num_cols = len(cols)
    num_rows = len(rows)

    return null_values, num_cols, num_rows


def get_unique_count(header, file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return len(set(row[header] for row in reader if row[header].strip() != ''))

def infer_column_type(header, file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        values = []

        for row in reader:
            if row[header].strip() != '':
                values.append(row[header])

        if len(values) == 0:
            return "Undefined"
        elif all(v.isdigit() for v in values):
            return "Integer"
        elif all(v.lower() in ("0", "1") for v in values):
            return "Boolean"
    
        is_iter = False
        for data in values:
            if isinstance(data, Iterable) and type(data) != str:
                is_iter = True
            else:
                is_iter = False
                break
        
        if is_iter == True:
            return "Iterable"
        else:
            return "String"
