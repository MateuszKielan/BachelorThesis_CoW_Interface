#-------------------- Import Section --------------------
import pandas as pd
import numpy as np
import typing
import csv
from collections.abc import Iterable
#--------------------------------------------------------

def extract_statistics(cols: list, rows: list):
    """
    Function extract_statistics that takes a dataframe and extracts the follwing:

    Params:
        cols (list): column names of the dataset.
        rows (list): row data of the dataset.

    """
    #
    df = pd.DataFrame(rows, columns=cols)

    null_values = df.isnull().sum()
    num_cols = len(cols)
    num_rows = len(rows)

    return null_values, num_cols, num_rows


def infer_column_type(header, file_path):
    """
    Function infer_column_type that checks the type of data for the column for the corresponding header

    Params:
        header (str): header name 
        file_path (str): path to the file 

    Return:
        type (str): type of the column data
    """

    # Open the file 
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        values = []

        # loop through the rows 
        for row in reader:
            if row[header].strip() != '':
                values.append(row[header])

        # Check for missing values
        if len(values) == 0:
            return "Undefined"
        elif all(v.isdigit() for v in values):
            return "Integer"
        elif all(v.lower() in ("0", "1") for v in values):
            return "Boolean"

        # Check if the values are an iterable (list, dict ...)
        is_iter = False
        for data in values:
            if isinstance(data, Iterable) and type(data) != str:
                is_iter = True
            else:
                is_iter = False
                break

        # If not iterable only string is left 
        if is_iter == True:
            return "Iterable"
        else:
            return "String"
