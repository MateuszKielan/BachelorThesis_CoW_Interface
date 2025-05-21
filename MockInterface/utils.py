#-------------------- Import Section --------------------
import pandas as pd
import numpy as np
import typing
import csv
from collections.abc import Iterable
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar
from pathlib import Path
from typing import List
#--------------------------------------------------------
def show_warning(message: str):
        """
        Function show_warning that implements a warning with a custom message.

        Args:
            message (str): message to be displayed
        """
        # Create a Warning display with a custom message
        MDSnackbar(
            MDLabel(
                text=message
            ),
            md_bg_color='#FF0000'
        ).open()


def open_csv(file_path: Path) -> list:
    """
    Function open_reader that handles opening the file and delimeter detection.
    Uses csv Sniffer to detect the delimeter of the file.

    Args:
        file_path (Path): path of the target csv file
    Returns:
        rows (list): list of row data from the csv file 

    """
    with open(str(file_path), newline='', encoding='utf-8') as csvfile:
            sample = csvfile.read(1024)           # Sample small chunk of the file 

            if not sample.strip():                # If empty return []
                return []
            
            dialect = csv.Sniffer().sniff(sample) # Delimeter detection
                
            csvfile.seek(0)                       # Go back to the first index
            reader = csv.reader(csvfile, dialect) 
            rows = list(reader)

            if not rows:
                return
            
            return rows


def extract_statistics(cols: list, rows: list) -> tuple[int, int, int]:
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


def infer_column_type(header: str, file_path: str) -> str:
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
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect = dialect)
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
