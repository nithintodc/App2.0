"""Utility functions for data processing"""
import pandas as pd
import streamlit as st


def normalize_store_id_column(df):
    """
    Normalize store ID column name.
    Checks for both 'Store ID' and 'Shop ID' and standardizes to 'Store ID'.
    
    Returns:
        Tuple of (df, store_col_name)
    """
    if 'Store ID' in df.columns:
        return df, 'Store ID'
    elif 'Shop ID' in df.columns:
        df = df.rename(columns={'Shop ID': 'Store ID'})
        return df, 'Store ID'
    else:
        return df, None


def filter_excluded_dates(df, date_col, excluded_dates):
    """
    Filter out excluded dates from a DataFrame.
    
    Args:
        df: DataFrame to filter
        date_col: Name of the date column
        excluded_dates: List of dates to exclude (can be strings in MM/DD/YYYY format or date objects)
    
    Returns:
        Filtered DataFrame
    """
    if not excluded_dates or date_col not in df.columns or df.empty:
        return df
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Convert date column to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Drop rows where date conversion failed
    df = df.dropna(subset=[date_col])
    
    if df.empty:
        return df
    
    # Convert excluded dates to date objects
    excluded_date_objects = []
    for date in excluded_dates:
        if isinstance(date, str):
            try:
                # Try MM/DD/YYYY format first
                dt = pd.to_datetime(date, format='%m/%d/%Y')
            except:
                # Try other formats
                dt = pd.to_datetime(date, errors='coerce')
            if pd.notna(dt):
                excluded_date_objects.append(dt.date())
        elif hasattr(date, 'date'):
            excluded_date_objects.append(date.date())
        elif isinstance(date, pd.Timestamp):
            excluded_date_objects.append(date.date())
        else:
            try:
                dt = pd.to_datetime(date)
                if pd.notna(dt):
                    excluded_date_objects.append(dt.date())
            except:
                pass
    
    if not excluded_date_objects:
        return df
    
    # Filter out excluded dates (compare at date level)
    df['_date_only'] = df[date_col].dt.date
    df = df[~df['_date_only'].isin(excluded_date_objects)]
    df = df.drop(columns=['_date_only'])
    
    return df


def find_date_column(df, preferred_names):
    """
    Find a date column in DataFrame by case-insensitive matching.
    
    Args:
        df: DataFrame to search
        preferred_names: List of preferred column names (will be matched case-insensitively)
    
    Returns:
        Actual column name found, or None if not found
    """
    # First try exact match
    for name in preferred_names:
        if name in df.columns:
            return name
    
    # Then try case-insensitive match
    df_cols_lower = {col.lower(): col for col in df.columns}
    for name in preferred_names:
        name_lower = name.lower()
        if name_lower in df_cols_lower:
            return df_cols_lower[name_lower]
    
    return None


def filter_master_file_by_date_range(file_path, start_date, end_date, date_col_name, excluded_dates=None):
    """
    Filter a master CSV file by date range and excluded dates.
    
    Args:
        file_path: Path to the CSV file
        start_date: Start date (MM/DD/YYYY format string or date object)
        end_date: End date (MM/DD/YYYY format string or date object)
        date_col_name: Name of the date column in the CSV (or list of preferred names for case-insensitive matching)
        excluded_dates: Optional list of dates to exclude
    
    Returns:
        Filtered DataFrame
    """
    try:
        # UE files have headers in row 2 (0-indexed row 1), DD files have headers in row 1
        if 'ue' in file_path.name.lower():
            df = pd.read_csv(file_path, skiprows=[0], header=0)
        else:
            df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        
        # Handle case-insensitive date column matching
        if isinstance(date_col_name, str):
            # If single string, try to find it case-insensitively
            preferred_names = [date_col_name]
            # For UE files, also try common variations
            if 'ue' in file_path.name.lower():
                preferred_names = ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date']
        else:
            preferred_names = date_col_name
        
        # Find the actual column name
        actual_date_col = find_date_column(df, preferred_names)
        
        if actual_date_col is None:
            st.warning(f"Date column not found in {file_path.name}. Tried: {preferred_names}. Available columns: {list(df.columns)[:10]}")
            return pd.DataFrame()
        
        # Convert date column to datetime - try common formats first
        try:
            # Try MM/DD/YYYY format first (most common)
            df[actual_date_col] = pd.to_datetime(df[actual_date_col], format='%m/%d/%Y', errors='coerce')
        except:
            # Fall back to automatic parsing if format doesn't match
            df[actual_date_col] = pd.to_datetime(df[actual_date_col], errors='coerce')
        df = df.dropna(subset=[actual_date_col])
        
        # Parse start and end dates
        if isinstance(start_date, str):
            start_dt = pd.to_datetime(start_date, format='%m/%d/%Y')
        else:
            start_dt = pd.to_datetime(start_date)
        
        if isinstance(end_date, str):
            end_dt = pd.to_datetime(end_date, format='%m/%d/%Y')
        else:
            end_dt = pd.to_datetime(end_date)
        
        # Filter by date range
        df = df[(df[actual_date_col] >= start_dt) & (df[actual_date_col] <= end_dt)]
        
        # Apply excluded dates filter
        if excluded_dates:
            df = filter_excluded_dates(df, actual_date_col, excluded_dates)
        
        return df
    except Exception as e:
        st.error(f"Error loading file {file_path.name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()
