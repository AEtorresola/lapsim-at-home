#helper_functions.py 
# This is meant to declutter the main scripts from less necessary scripts 
import pandas as pd
from logger import setup_logger

logger = setup_logger()


import pandas as pd

class TimeSeriesStorage:
    def __init__(self, initial_data: dict, name: str, col_types=None):
        """
        Initialize the TimeSeriesStorage with initial data.

        Args:
            initial_data (dict): A dictionary where keys are column names and values are lists of initial values.
            name (str): Name of the TimeSeriesStorage instance.
            col_types (dict, optional): A dictionary where keys are column names and values are the desired dtypes.
                                       If None, no explicit dtype assignment is performed.
        """
        self.name = name
        self.data = pd.DataFrame(initial_data)

        # Ensure 'time' column is of type int and set it as the index
        self.data['time'] = self.data['time'].astype(int)
        self.data.set_index("time", inplace=True)

        # Apply column dtypes if col_types is provided
        if col_types is not None:
            for col, dtype in col_types.items():
                if col in self.data.columns:
                    self.data[col] = self.data[col].astype(dtype)
                else:
                    raise ValueError(f"Column '{col}' specified in col_types does not exist in the DataFrame.")

    def update(self, new_data: dict, time: int):
        """
        Update the time-series data at a specific time.

        Args:
            time (int): The time at which to update the data.
            new_data (dict): A dictionary where keys are column names and values are the new values to be updated.

        Raises:
            ValueError: If new_data contains columns not present in the DataFrame.
        """
        try:
            # Log the start of the update process
            logger.info(f"Starting data update for {self.name}:{new_data} at time {time}")
            
            # Check if all columns in new_data exist in the DataFrame
            if not all(col in self.data.columns for col in new_data.keys()):
                raise ValueError("New data contains columns not present in the DataFrame")
            
            # Check if time exists in the index
            if time in self.data.index:
                # logger.debug("Updating existing row at time %s", time)
                # Update existing row
                for col, value in new_data.items():
                    if type(value) == tuple:
                        # import pdb; pdb.set_trace()
                        self.data.at[time, col] = value
                    else:
                        self.data.at[time, col] = value
            else:
                # logger.debug("Appending new row at time %s", time)
                # Append new row
                self.data.loc[time] = new_data
            
            # Log successful update
            # logger.info("Successfully updated data at time %s", time)
            
        except Exception as e:
            # Log the error
            logger.error(f"Error updating data at time {time}: {str(e)}")
            # Re-raise the exception if you want the caller to handle it
            raise

    def get_value(self, column: str, time: int):
        """
        Retrieve a specific value from the time-series data.

        Args:
            time (int): The time at which to retrieve the value.
            column (str): The column name from which to retrieve the value.

        Returns:
            The value at the specified time and column, or None if not found.
        """
        try:
            return self.data.at[time, column]
        except KeyError:
            logger.warning(f"Error: Time index '{time}' or column '{column}' not found.")
            return None

    def get_time_series(self, time: int):
        """
        Retrieve a specific row as a Pandas Series.

        Args:
            column (str): The column name to retrieve.

        Returns:
            A Pandas Series representing the specified column.
        """
        try:
            return self.data.loc[time]
        except Exception as e:
            print(e)
            import pdb; pdb.set_trace()
            return None

    def get_dataframe(self):
        """
        Retrieve the entire DataFrame.

        Returns:
            The entire DataFrame.
        """
        return self.data
    
def combine_dataframes(
    list_of_named_dfs: list[tuple[pd.DataFrame, str]],
    time_index: str = "time",
) -> pd.DataFrame:
    """Combines a list of dataframes with a common time index, renaming columns
    to include the dataframe name.

    Args:
        list_of_named_dfs: A list of tuples, where each tuple contains a
            pandas DataFrame and its name (string).
        time_index: The name of the column to use as the time index.  Defaults
            to "time".

    Returns:
        A single pandas DataFrame containing all columns from the input
        DataFrames, with column names modified to include the original
        DataFrame's name.
    """
    
    if all([isinstance(named_df[0], TimeSeriesStorage) for named_df in list_of_named_dfs]):
        list_of_named_dfs = [(named_df[0].data, named_df[1]) for named_df in list_of_named_dfs]
        logger.debug("All objects to combine were TimeSeries")
    elif all([isinstance(named_df[0], pd.DataFrame) for named_df in list_of_named_dfs]):
        logger.debug("All objects to combine were Dataframes")
    else:
        logger.warn(f"Not all objects had the same type, or were not dataframes or Time Series. Recieved; {[(type(named_df[0]), named_df[1]) for named_df in list_of_named_dfs]}")
        return pd.DataFrame()

    if not list_of_named_dfs:
        return pd.DataFrame()

    # Set time index for all dataframes
    # import pdb; pdb.set_trace()
    # for df, _ in list_of_named_dfs:
    #     if time_index not in df.columns:
    # import pdb; pdb.set_trace()
    #
    #         df[time_index] = range(len(df))  # Create a new index column
    #     df.set_index(time_index, inplace=True)

    # Rename columns to include dataframe name
    renamed_dfs = []
    for df, name in list_of_named_dfs:
        renamed_df = df.copy()
        renamed_df.columns = [f"{name}_{col}" for col in df.columns]
        renamed_dfs.append(renamed_df)

    # Concatenate all dataframes
    combined_df = pd.concat(renamed_dfs, axis=1)


    # Reset index
    # combined_df.reset_index(inplace=True)

    return combined_df

def append_new_rows(
    combined_df: pd.DataFrame,
    new_rows: list[tuple[pd.Series, str]],
    time: int,
) -> pd.DataFrame:
    """Appends new rows to the combined DataFrame efficiently.

    Args:
        combined_df: The existing combined DataFrame.
        new_rows: A list of tuples, where each tuple contains a Pandas Series
            representing the new row for a source DataFrame, and the name
            of the source DataFrame.  The index of the series should match
            the column names of the original dataframe
        time_index: The name of the time index column.  Defaults to "time".

    Returns:
        The updated combined DataFrame with the new rows appended.
    """

    new_row_data = {"time":time}
    time_value = None  # Store the time value from the first new row

    # Extract data from new rows and store in a dictionary

    # import pdb; pdb.set_trace()
    for row, name in new_rows:
        if time_value is None:
            time_value = row.index  # Get time value from first row
        for col, value in row.items():
            new_row_data[f"{name}_{col}"] = value

    # Add the time index to the new row data
    # new_row_data[time_index] = time_value

    # Create a new DataFrame from the collected data
    if False:
        new_row_df = pd.DataFrame([new_row_data], index=[time])
        new_row_df.index.name = 'time'
        # Append the new row to the combined DataFrame
        combined_df = pd.concat([combined_df, new_row_df], ignore_index=False)
    
    # Series Method
    new_row_series = pd.Series(new_row_data, name=time)

    combined_df.loc[time] = new_row_series

    return combined_df

