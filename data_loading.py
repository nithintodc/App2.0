"""Data loading functions for DoorDash and UberEats files"""
import pandas as pd
import streamlit as st
from pathlib import Path
from config import DD_DATA_MASTER, UE_DATA_MASTER, ROOT_DIR
from utils import filter_master_file_by_date_range, normalize_store_id_column, find_date_column


def process_master_file_for_dd(file_path, start_date, end_date, excluded_dates=None):
    """
    Process dd-data.csv master file and return aggregated data by Store ID.
    
    Args:
        file_path: Path to the dd-data.csv file
        start_date: Start date for filtering (MM/DD/YYYY format)
        end_date: End date for filtering (MM/DD/YYYY format)
        excluded_dates: List of dates to exclude
    
    Returns:
        Tuple of (sales_agg, payout_agg, orders_agg) DataFrames
    """
    try:
        # Debug: Show file path and date range
        st.info(f"🔍 DEBUG: Processing DoorDash file: {file_path.name}")
        st.info(f"🔍 DEBUG: File absolute path: {file_path.resolve()}")
        st.info(f"🔍 DEBUG: Date range: {start_date} to {end_date}")
        
        # Check if file exists and show size
        if file_path.exists():
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            st.info(f"🔍 DEBUG: File size: {file_size_mb:.2f} MB")
        else:
            st.error(f"❌ DEBUG: File does not exist at: {file_path.resolve()}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Load and filter by date range using "Timestamp local date" column variations
        # Try multiple variations: "Timestamp local date", "Timestamp Local Date", "Date", etc.
        date_col_variations = ['Timestamp local date', 'Timestamp Local Date', 'Timestamp Local date', 
                              'timestamp local date', 'Date', 'date', 'Timestamp', 'timestamp']
        df = filter_master_file_by_date_range(file_path, start_date, end_date, date_col_variations, excluded_dates)
        
        # Debug: Show filtering results
        if df.empty:
            st.warning(f"⚠️ DEBUG: No data found after filtering. File: {file_path.name}, Date range: {start_date} to {end_date}")
            # Try to load the file without filtering to see what's available
            try:
                df_raw = pd.read_csv(file_path)
                df_raw.columns = df_raw.columns.str.strip()
                st.info(f"🔍 DEBUG: Raw file has {len(df_raw)} rows and columns: {list(df_raw.columns)[:10]}")
                # Check if date column exists
                found_col = find_date_column(df_raw, date_col_variations)
                if found_col:
                    st.info(f"🔍 DEBUG: Found date column: '{found_col}'")
                    # Show sample dates
                    if found_col in df_raw.columns:
                        df_raw[found_col] = pd.to_datetime(df_raw[found_col], errors='coerce')
                        df_with_dates = df_raw.dropna(subset=[found_col])
                        if len(df_with_dates) > 0:
                            min_date = df_with_dates[found_col].min()
                            max_date = df_with_dates[found_col].max()
                            st.info(f"🔍 DEBUG: Date range in file: {min_date.date()} to {max_date.date()}")
                else:
                    st.error(f"❌ DEBUG: Date column not found! Tried: {date_col_variations}")
            except Exception as e:
                st.error(f"❌ DEBUG: Error loading raw file: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            st.success(f"✅ DEBUG: Found {len(df)} rows after filtering")
        
        # The columns should be "Merchant store ID" (or "Store ID") and "Subtotal"
        store_col = 'Merchant store ID'
        if store_col not in df.columns:
            store_col = 'Store ID'
        
        sales_col = 'Subtotal'
        
        # Determine payout column - try both names
        payout_col = None
        if 'Net total' in df.columns:
            payout_col = 'Net total'
        elif 'Net total (for historical reference only)' in df.columns:
            payout_col = 'Net total (for historical reference only)'
        
        # Verify columns exist
        if store_col not in df.columns:
            st.error(f"Column 'Merchant store ID' or 'Store ID' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        if sales_col not in df.columns:
            st.error(f"Column 'Subtotal' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        if payout_col is None:
            st.error(f"Payout column not found in {file_path.name}. Available columns: {list(df.columns)[:10]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Convert to numeric, handling any non-numeric values
        df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
        df[payout_col] = pd.to_numeric(df[payout_col], errors='coerce')
        
        # Remove rows where Store ID is NaN
        df = df.dropna(subset=[store_col])
        
        # Get DoorDash Order ID column
        order_col = 'DoorDash order ID'
        if order_col not in df.columns:
            st.error(f"Column 'DoorDash order ID' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Group by Store ID and aggregate
        sales_agg = df.groupby(store_col)[sales_col].sum().reset_index()
        sales_agg.columns = ['Store ID', 'Sales']
        
        payout_agg = df.groupby(store_col)[payout_col].sum().reset_index()
        payout_agg.columns = ['Store ID', 'Payouts']
        
        # Count distinct DoorDash Order IDs by Store ID
        orders_agg = df.groupby(store_col)[order_col].nunique().reset_index()
        orders_agg.columns = ['Store ID', 'Orders']
        
        return sales_agg, payout_agg, orders_agg
    except Exception as e:
        st.error(f"Error processing master file {file_path.name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def process_master_file_for_ue(file_path, start_date, end_date, excluded_dates=None):
    """
    Process ue-data.csv master file and return aggregated data by Store ID.
    
    Args:
        file_path: Path to the ue-data.csv file
        start_date: Start date for filtering (MM/DD/YYYY format)
        end_date: End date for filtering (MM/DD/YYYY format)
        excluded_dates: List of dates to exclude
    
    Returns:
        Tuple of (sales_agg, payout_agg, orders_agg) DataFrames
    """
    try:
        # Debug: Show file path and date range
        st.info(f"🔍 DEBUG: Processing UberEats file: {file_path.name}")
        st.info(f"🔍 DEBUG: File absolute path: {file_path.resolve()}")
        st.info(f"🔍 DEBUG: Date range: {start_date} to {end_date}")
        
        # Check if file exists and show size
        if file_path.exists():
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            st.info(f"🔍 DEBUG: File size: {file_size_mb:.2f} MB")
        else:
            st.error(f"❌ DEBUG: File does not exist at: {file_path.resolve()}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Load and filter by date range using "Order date" column (case-insensitive matching)
        # Try all common variations: "Order Date", "Order date", "order date", "order Date"
        df = filter_master_file_by_date_range(file_path, start_date, end_date, 
                                               ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date'], 
                                               excluded_dates)
        
        # Debug: Show filtering results
        if df.empty:
            st.warning(f"⚠️ DEBUG: No data found after filtering. File: {file_path.name}, Date range: {start_date} to {end_date}")
            # Try to load the file without filtering to see what's available
            try:
                df_raw = pd.read_csv(file_path, skiprows=[0], header=0)
                df_raw.columns = df_raw.columns.str.strip()
                st.info(f"🔍 DEBUG: Raw file has {len(df_raw)} rows and columns: {list(df_raw.columns)[:10]}")
                # Check if date column exists
                found_col = find_date_column(df_raw, ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date'])
                if found_col:
                    st.info(f"🔍 DEBUG: Found date column: '{found_col}'")
                    # Show sample dates
                    if found_col in df_raw.columns:
                        df_raw[found_col] = pd.to_datetime(df_raw[found_col], errors='coerce')
                        df_with_dates = df_raw.dropna(subset=[found_col])
                        if len(df_with_dates) > 0:
                            min_date = df_with_dates[found_col].min()
                            max_date = df_with_dates[found_col].max()
                            st.info(f"🔍 DEBUG: Date range in file: {min_date.date()} to {max_date.date()}")
                else:
                    st.error(f"❌ DEBUG: Date column not found! Tried: ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date']")
            except Exception as e:
                st.error(f"❌ DEBUG: Error loading raw file: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            st.success(f"✅ DEBUG: Found {len(df)} rows after filtering")
        
        # Normalize store ID column (check for both 'Store ID' and 'Shop ID')
        df, store_col = normalize_store_id_column(df)
        
        # The columns should be "Store ID" (or "Shop ID"), "Sales (excl. tax)", and "Total payout"
        sales_col = 'Sales (excl. tax)'
        payout_col = 'Total payout'
        
        # Verify columns exist
        if store_col is None or store_col not in df.columns:
            st.error(f"Column 'Store ID' or 'Shop ID' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        if sales_col not in df.columns:
            st.error(f"Column 'Sales (excl. tax)' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        if payout_col not in df.columns:
            st.error(f"Column 'Total payout' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Convert to numeric, handling any non-numeric values
        df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
        df[payout_col] = pd.to_numeric(df[payout_col], errors='coerce')
        
        # Remove rows where Store ID is NaN
        df = df.dropna(subset=[store_col])
        
        # Get Order ID column
        order_col = 'Order ID'
        if order_col not in df.columns:
            st.error(f"Column 'Order ID' not found in {file_path.name}. Available columns: {list(df.columns)[:5]}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Group by Store ID and aggregate
        sales_agg = df.groupby(store_col)[sales_col].sum().reset_index()
        sales_agg.columns = ['Store ID', 'Sales']
        
        payout_agg = df.groupby(store_col)[payout_col].sum().reset_index()
        payout_agg.columns = ['Store ID', 'Payouts']
        
        # Count distinct Order IDs by Store ID
        orders_agg = df.groupby(store_col)[order_col].nunique().reset_index()
        orders_agg.columns = ['Store ID', 'Orders']
        
        return sales_agg, payout_agg, orders_agg
    except Exception as e:
        st.error(f"Error processing master file {file_path.name}: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
