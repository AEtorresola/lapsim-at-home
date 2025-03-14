#helper_functions.py 
# This is meant to declutter the main scripts from less necessary scripts 
import pandas as pd




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

    if not list_of_named_dfs:
        return pd.DataFrame()

    # Set time index for all dataframes
    for df, _ in list_of_named_dfs:
        df.set_index(time_index, inplace=True)

    # Rename columns to include dataframe name
    renamed_dfs = []
    for df, name in list_of_named_dfs:
        renamed_df = df.copy()
        renamed_df.columns = [f"{name}_{col}" for col in df.columns]
        renamed_dfs.append(renamed_df)

    # Concatenate all dataframes
    combined_df = pd.concat(renamed_dfs, axis=1)

    # Reset index
    combined_df.reset_index(inplace=True)

    return combined_df

def append_new_rows(
    combined_df: pd.DataFrame,
    new_rows: list[tuple[pd.Series, str]],
    time_index: str = "time",
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

    new_row_data = {}
    time_value = None  # Store the time value from the first new row

    # Extract data from new rows and store in a dictionary
    for row, name in new_rows:
        if time_value is None:
            time_value = row.get(time_index)  # Get time value from first row
        for col, value in row.items():
            new_row_data[f"{name}_{col}"] = value

    # Add the time index to the new row data
    new_row_data[time_index] = time_value

    # Create a new DataFrame from the collected data
    new_row_df = pd.DataFrame([new_row_data])

    # Append the new row to the combined DataFrame
    combined_df = pd.concat([combined_df, new_row_df], ignore_index=True)

    return combined_df

class TimeSeriesStorage:
    def __init__(self, initial_data: dict):
        """
        Initialize the TimeSeriesStorage with initial data.

        Args:
            initial_data (dict): A dictionary where keys are column names and values are lists of initial values.
        """
        self.data = pd.DataFrame(initial_data)
        self.data.set_index("time", inplace=True)

    def update(self, time: float, new_data: dict):
        """
        Update the time-series data at a specific time.

        Args:
            time (float): The time at which to update the data.
            new_data (dict): A dictionary where keys are column names and values are the new values to be updated.
        """
        if time in self.data.index:
            # Update existing row
            for col, value in new_data.items():
                self.data.loc[time, col] = value
        else:
            # Append new row
            self.data.loc[time] = new_data

    def get_value(self, time: float, column: str):
        """
        Retrieve a specific value from the time-series data.

        Args:
            time (float): The time at which to retrieve the value.
            column (str): The column name from which to retrieve the value.

        Returns:
            The value at the specified time and column, or None if not found.
        """
        try:
            return self.data.at[time, column]
        except KeyError:
            print(f"Error: Time index '{time}' or column '{column}' not found.")
            return None

    def get_series(self, column: str):
        """
        Retrieve a specific column as a Pandas Series.

        Args:
            column (str): The column name to retrieve.

        Returns:
            A Pandas Series representing the specified column.
        """
        return self.data[column]

    def get_dataframe(self):
        """
        Retrieve the entire DataFrame.

        Returns:
            The entire DataFrame.
        """
        return self.data

