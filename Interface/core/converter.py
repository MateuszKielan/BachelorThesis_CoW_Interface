#------IMPORTS SECTION-------

# Python Imports
import logging
import time
from pathlib import Path

# CoW Import
from cow_csvw.converter.csvw import build_schema, CSVWConverter
#-----------------------------


# Set up the logger 
logger = logging.getLogger(__name__)


def convert_with_cow(csv_path: str):
    """
    Converts a CSV file into a JSON metadata file using CoW (CSV on the Web).

    Args:
        csv_path (str): Path to the input CSV file.
    Returns:
        Path: Path to the created metadata file, if not created returning None
    """
    input_path = Path(csv_path)
    output_metadata_path = input_path.parent / f"{input_path.stem}-metadata.json"

    # Check if the file already exists. If yes -> return the path.
    if output_metadata_path.exists():
        logger.info("CoW: Metadata file already exists. Loading data.")
        return output_metadata_path
        
    try:
        start_time = time.time()                                         # Measuring start time
        build_schema(str(input_path), str(output_metadata_path))         # Using CoW method to create schema
        duration = time.time() - start_time                              # Measure time taken to convert the file 
        logger.info(f"CoW: Metadata saved to {output_metadata_path}")    
        logger.info(f"Conversion time: {duration:.2f} seconds")
        return output_metadata_path                                      # Return the file path
        
    except Exception as e:
        logger.error("CoW: Metadata generation failed")
        logger.exception(e)
        return None
            