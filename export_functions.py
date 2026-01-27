"""Export functions for Excel and date exports"""
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
import zipfile
import io
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from config import ROOT_DIR
from gdrive_utils import get_drive_manager
from utils import normalize_store_id_column, filter_master_file_by_date_range
from table_generation import create_summary_tables
from data_processing import get_last_year_dates


def export_to_excel(dd_table1, dd_table2, ue_table1, ue_table2, 
                     dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df,
                     ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df,
                     dd_selected_stores, ue_selected_stores,
                     combined_summary1, combined_summary2, combined_store_table1, combined_store_table2,
                     corporate_todc_table=None, promotion_table=None, sponsored_table=None):
    """Export all tables to an Excel file with sheets: Summary Tables, Store-Level Tables, and Corporate vs TODC"""
    # Use temp directory for file creation (will be downloaded, not saved to disk)
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    outputs_dir = temp_dir / "streamlit_exports"
    outputs_dir.mkdir(exist_ok=True)
    
    # Create workbook
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    # Get summary tables
    dd_summary1, dd_summary2 = None, None
    ue_summary1, ue_summary2 = None, None
    if dd_sales_df is not None and dd_payouts_df is not None and dd_orders_df is not None:
        dd_summary1, dd_summary2 = create_summary_tables(dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df, dd_selected_stores, is_ue=False)
    if ue_sales_df is not None and ue_payouts_df is not None and ue_orders_df is not None:
        ue_summary1, ue_summary2 = create_summary_tables(ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df, ue_selected_stores, is_ue=True)
    
    # Sheet 1: Summary Tables
    ws_summary = wb.create_sheet("Summary Tables")
    current_row = 1
    
    def add_table_to_sheet(ws, table_name, df, start_row):
        """Add a table with name header to the sheet and format it"""
        if df is None or df.empty:
            return start_row
        # Add table name
        ws.cell(row=start_row, column=1, value=table_name)
        ws.cell(row=start_row, column=1).font = Font(bold=True, size=12)
        start_row += 1
        # Add table data
        # Check if Store ID, Metric, or Is Self Serve Campaign is in index
        if df.index.name in ['Store ID', 'Metric', 'Is Self Serve Campaign'] or (hasattr(df.index, 'name') and df.index.name):
            # Reset index to include it as a column
            df_display = df.reset_index()
        elif 'Store ID' not in df.columns and 'Metric' not in df.columns and 'Is Self Serve Campaign' not in df.columns:
            # Try to reset index if it exists
            try:
                df_display = df.reset_index()
            except:
                df_display = df.copy()
        else:
            df_display = df.copy()
        
        # Write header row
        header_row = start_row
        for col_idx, col_name in enumerate(df_display.columns, start=1):
            cell = ws.cell(row=start_row, column=col_idx, value=col_name)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
        start_row += 1
        
        # Write data rows
        for row_idx, row_data in df_display.iterrows():
            # Check if this row is for Orders or New Customers (for summary tables)
            is_orders_row = False
            is_new_customers_row = False
            if 'Metric' in df_display.columns:
                metric_value = row_data.get('Metric', '')
                if metric_value == 'Orders':
                    is_orders_row = True
                elif metric_value == 'New Customers':
                    is_new_customers_row = True
            
            for col_idx, col_name in enumerate(df_display.columns, start=1):
                value = row_data[col_name]
                cell = ws.cell(row=start_row, column=col_idx, value=value)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Format based on column name and row type
                if 'Growth%' in col_name or 'YoY%' in col_name:
                    # Format as percentage with % symbol
                    if isinstance(value, (int, float)):
                        cell.value = f"{value:.1f}%"
                elif col_name in ['Store ID', 'Metric', 'Is Self Serve Campaign']:
                    # Keep as is (text)
                    pass
                elif col_name == 'Orders':
                    # Orders: format as integer with comma separators
                    if isinstance(value, (int, float)):
                        cell.value = f"{int(round(value)):,}"
                elif col_name in ['Sales', 'Spend', 'Cost per Order']:
                    # Sales, Spend, Cost per Order: format as dollar amount
                    if isinstance(value, (int, float)):
                        cell.value = f"${value:,.2f}"
                elif col_name == 'ROAS':
                    # ROAS: format as decimal
                    if isinstance(value, (int, float)):
                        cell.value = f"{value:.2f}"
                elif is_orders_row or is_new_customers_row:
                    # Orders and New Customers rows: format as integer with comma separators (no decimals, no dollar sign)
                    if isinstance(value, (int, float)):
                        cell.value = f"{int(round(value)):,}"
                elif metric_value == 'Profitability':
                    # Profitability: format as percentage
                    if isinstance(value, (int, float)):
                        cell.value = f"{value:.1f}%"
                elif metric_value == 'AOV':
                    # AOV: format as dollar amount
                    if isinstance(value, (int, float)):
                        cell.value = f"${value:,.1f}"
                else:
                    # Format as dollar amount
                    if isinstance(value, (int, float)):
                        cell.value = f"${value:,.1f}"
            
            start_row += 1
        
        # Auto-adjust column widths
        for col_idx, col_name in enumerate(df_display.columns, start=1):
            max_length = max(
                len(str(col_name)),
                max([len(str(df_display.iloc[row_idx, col_idx-1])) for row_idx in range(len(df_display))], default=0)
            )
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_length + 2, 50)
        
        return start_row + 1  # Add blank row after table
    
    # Add Combined Table 1
    if combined_summary1 is not None:
        current_row = add_table_to_sheet(ws_summary, "Combined Table 1: Current Year Pre vs Post Analysis", combined_summary1, current_row)
    
    # Add Combined Table 2 (YoY) - second position
    if combined_summary2 is not None:
        current_row = add_table_to_sheet(ws_summary, "Combined Table 2: Year-over-Year Analysis", combined_summary2, current_row)
    
    # Add DD Table 1
    if dd_summary1 is not None:
        current_row = add_table_to_sheet(ws_summary, "DoorDash Table 1: Current Year Pre vs Post Analysis", dd_summary1, current_row)
    
    # Add DD Table 2
    if dd_summary2 is not None:
        current_row = add_table_to_sheet(ws_summary, "DoorDash Table 2: Year-over-Year Analysis", dd_summary2, current_row)
    
    # Add UE Table 1
    if ue_summary1 is not None:
        current_row = add_table_to_sheet(ws_summary, "UberEats Table 1: Current Year Pre vs Post Analysis", ue_summary1, current_row)
    
    # Add UE Table 2
    if ue_summary2 is not None:
        current_row = add_table_to_sheet(ws_summary, "UberEats Table 2: Year-over-Year Analysis", ue_summary2, current_row)
    
    # Sheet 2: Store-Level Tables
    ws_store = wb.create_sheet("Store-Level Tables")
    current_row = 1
    
    # Add Combined Store Table 1
    if combined_store_table1 is not None:
        current_row = add_table_to_sheet(ws_store, "Combined Table 1: Current Year Pre vs Post Analysis (Store-Level)", combined_store_table1, current_row)
    
    # Add Combined Store Table 2 (YoY) - second position
    if combined_store_table2 is not None:
        current_row = add_table_to_sheet(ws_store, "Combined Table 2: Year-over-Year Analysis (Store-Level)", combined_store_table2, current_row)
    
    # Add DD Store Table 1
    if dd_table1 is not None:
        current_row = add_table_to_sheet(ws_store, "DoorDash Table 1: Current Year Pre vs Post Analysis (Store-Level)", dd_table1, current_row)
    
    # Add DD Store Table 2
    if dd_table2 is not None:
        current_row = add_table_to_sheet(ws_store, "DoorDash Table 2: Year-over-Year Analysis (Store-Level)", dd_table2, current_row)
    
    # Add UE Store Table 1
    if ue_table1 is not None:
        current_row = add_table_to_sheet(ws_store, "UberEats Table 1: Current Year Pre vs Post Analysis (Store-Level)", ue_table1, current_row)
    
    # Add UE Store Table 2
    if ue_table2 is not None:
        current_row = add_table_to_sheet(ws_store, "UberEats Table 2: Year-over-Year Analysis (Store-Level)", ue_table2, current_row)
    
    # Sheet 3: Corporate vs TODC Tables
    if corporate_todc_table is not None and not corporate_todc_table.empty:
        ws_corporate = wb.create_sheet("Corporate vs TODC")
        current_row = 1
        
        # Add Combined Corporate vs TODC table
        # Prepare the table for export (reset index to include Is Self Serve Campaign as column)
        corporate_export = corporate_todc_table.copy()
        corporate_export.index.name = 'Is Self Serve Campaign'
        corporate_export = corporate_export.reset_index()
        corporate_export['Is Self Serve Campaign'] = corporate_export['Is Self Serve Campaign'].apply(
            lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
        )
        corporate_export = corporate_export.set_index('Is Self Serve Campaign')
        
        current_row = add_table_to_sheet(ws_corporate, "Combined: Corporate vs TODC", corporate_export, current_row)
        
        # Add Promotion table if available
        if promotion_table is not None and not promotion_table.empty:
            promo_export = promotion_table.copy()
            promo_export.index.name = 'Is Self Serve Campaign'
            promo_export = promo_export.reset_index()
            promo_export['Is Self Serve Campaign'] = promo_export['Is Self Serve Campaign'].apply(
                lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
            )
            promo_export = promo_export.set_index('Is Self Serve Campaign')
            current_row = add_table_to_sheet(ws_corporate, "Promotion: Corporate vs TODC", promo_export, current_row)
        
        # Add Sponsored Listing table if available
        if sponsored_table is not None and not sponsored_table.empty:
            sponsored_export = sponsored_table.copy()
            sponsored_export.index.name = 'Is Self Serve Campaign'
            sponsored_export = sponsored_export.reset_index()
            sponsored_export['Is Self Serve Campaign'] = sponsored_export['Is Self Serve Campaign'].apply(
                lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
            )
            sponsored_export = sponsored_export.set_index('Is Self Serve Campaign')
            current_row = add_table_to_sheet(ws_corporate, "Sponsored Listing: Corporate vs TODC", sponsored_export, current_row)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_export_{timestamp}.xlsx"
    filepath = outputs_dir / filename
    
    # Save workbook
    wb.save(filepath)
    
    # Read file as bytes for download
    with open(filepath, 'rb') as f:
        file_bytes = f.read()
    
    # Upload to Google Drive in "cloud-app-uploads" folder
    try:
        drive_manager = get_drive_manager()
        if drive_manager:
            # Upload to "cloud-app-uploads" folder
            upload_result = drive_manager.upload_file_to_subfolder(
                file_path=filepath,
                root_folder_name="cloud-app-uploads",
                subfolder_name="outputs",
                file_name=filename
            )
            st.success(f"✅ **Export successful!** Excel file ready for download and uploaded to Google Drive.")
            st.info(f"📤 File uploaded to Google Drive: [{upload_result['file_name']}]({upload_result['webViewLink']})")
    except Exception as e:
        st.warning(f"⚠️ Google Drive upload failed: {str(e)}")
    
    # Return file bytes and filename for download
    return file_bytes, filename


def create_date_export(dd_pre_24_path, dd_post_24_path, dd_pre_25_path, dd_post_25_path,
                      ue_pre_24_path, ue_post_24_path, ue_pre_25_path, ue_post_25_path,
                      dd_selected_stores, ue_selected_stores):
    """Create date pivot tables with Store IDs as columns and Sales, Payouts, Orders as values
    Processes only dd-pre/post and ue-pre/post files (8 files total)
    Returns a dictionary with file names as keys and dictionaries of Sales, Payouts, Orders as values
    Each file gets 3 separate pivot tables (Sales, Payouts, Orders)
    """
    
    def process_dd_file_for_date_export(file_path, selected_stores):
        """Process DD file and return data pivoted by date"""
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            
            # Use "Timestamp local date" for DD
            date_col = 'Timestamp local date'
            store_col = 'Merchant store ID'
            sales_col = 'Subtotal'
            
            # Determine payout column
            if '24' in file_path.name:
                payout_col = 'Net total (for historical reference only)'
            else:
                payout_col = 'Net total'
            
            order_col = 'DoorDash order ID'
            
            if date_col not in df.columns or store_col not in df.columns:
                st.warning(f"Missing required columns in {file_path.name}. Looking for '{date_col}' and '{store_col}'. Found: {list(df.columns)[:10]}")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Check for payout column - try both names if needed
            if payout_col not in df.columns:
                # Try the other column name as fallback
                if payout_col == 'Net total':
                    payout_col = 'Net total (for historical reference only)'
                else:
                    payout_col = 'Net total'
                
                if payout_col not in df.columns:
                    st.warning(f"Payout column not found in {file_path.name}. Tried 'Net total' and 'Net total (for historical reference only)'. Available columns: {list(df.columns)[:10]}")
                    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Process ALL data - no filtering by selected stores for date export
            # Convert date
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col, store_col])
            
            if len(df) == 0:
                st.warning(f"No valid data after date conversion in {file_path.name}")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Convert to numeric
            df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
            df[payout_col] = pd.to_numeric(df[payout_col], errors='coerce')
            
            # Aggregate by Date and Store ID
            if len(df) == 0:
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            sales_pivot = df.groupby([date_col, store_col])[sales_col].sum().reset_index()
            payouts_pivot = df.groupby([date_col, store_col])[payout_col].sum().reset_index()
            orders_pivot = df.groupby([date_col, store_col])[order_col].nunique().reset_index()
            
            # Check if we have data to pivot
            if len(sales_pivot) == 0:
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Convert Store ID to string for consistent column names
            sales_pivot[store_col] = sales_pivot[store_col].astype(str)
            payouts_pivot[store_col] = payouts_pivot[store_col].astype(str)
            orders_pivot[store_col] = orders_pivot[store_col].astype(str)
            
            # Pivot: Date as index, Store ID as columns
            sales_pivot_table = sales_pivot.pivot_table(index=date_col, columns=store_col, values=sales_col, aggfunc='sum', fill_value=0)
            payouts_pivot_table = payouts_pivot.pivot_table(index=date_col, columns=store_col, values=payout_col, aggfunc='sum', fill_value=0)
            orders_pivot_table = orders_pivot.pivot_table(index=date_col, columns=store_col, values=order_col, aggfunc='sum', fill_value=0)
            
            return sales_pivot_table, payouts_pivot_table, orders_pivot_table
        except Exception as e:
            st.error(f"Error processing {file_path.name} for date export: {str(e)}")
            import traceback
            with st.expander(f"Error details for {file_path.name}"):
                st.code(traceback.format_exc())
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def process_ue_file_for_date_export(file_path, selected_stores):
        """Process UE file and return data pivoted by date"""
        try:
            df = pd.read_csv(file_path, skiprows=[0], header=0)
            df.columns = df.columns.str.strip()
            
            # Normalize store ID column (check for both 'Store ID' and 'Shop ID')
            df, store_col = normalize_store_id_column(df)
            
            # Find "Order Date" column for UE (case-insensitive matching)
            # Try all common variations: "Order Date", "Order date", "order date", "order Date"
            date_col = None
            preferred_names = ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date']
            
            # First try exact match
            for name in preferred_names:
                if name in df.columns:
                    date_col = name
                    break
            
            # Then try case-insensitive match
            if date_col is None:
                df_cols_lower = {col.lower().strip(): col for col in df.columns}
                for name in preferred_names:
                    name_lower = name.lower().strip()
                    if name_lower in df_cols_lower:
                        date_col = df_cols_lower[name_lower]
                        break
            
            if date_col is None:
                st.warning(f"Date column not found in UE file. Available columns: {list(df.columns)[:10]}")
                date_col = 'Order Date'  # Default fallback (may cause error if not present)
            
            sales_col = 'Sales (excl. tax)'
            payout_col = 'Total payout'
            order_col = 'Order ID'
            
            if date_col not in df.columns or store_col is None or store_col not in df.columns:
                st.warning(f"Missing required columns in {file_path.name}. Looking for '{date_col}' and 'Store ID' or 'Shop ID'. Found: {list(df.columns)[:10]}")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Process ALL data - no filtering by selected stores for date export
            # Convert date
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col, store_col])
            
            if len(df) == 0:
                st.warning(f"No valid data after date conversion in {file_path.name}")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
            # Convert to numeric
            df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
            df[payout_col] = pd.to_numeric(df[payout_col], errors='coerce')
            
            # Aggregate by Date and Store ID
            sales_pivot = df.groupby([date_col, store_col])[sales_col].sum().reset_index()
            payouts_pivot = df.groupby([date_col, store_col])[payout_col].sum().reset_index()
            orders_pivot = df.groupby([date_col, store_col])[order_col].nunique().reset_index()
            
            # Convert Store ID to string for consistent column names
            sales_pivot[store_col] = sales_pivot[store_col].astype(str)
            payouts_pivot[store_col] = payouts_pivot[store_col].astype(str)
            orders_pivot[store_col] = orders_pivot[store_col].astype(str)
            
            # Pivot: Date as index, Store ID as columns
            sales_pivot_table = sales_pivot.pivot_table(index=date_col, columns=store_col, values=sales_col, aggfunc='sum', fill_value=0)
            payouts_pivot_table = payouts_pivot.pivot_table(index=date_col, columns=store_col, values=payout_col, aggfunc='sum', fill_value=0)
            orders_pivot_table = orders_pivot.pivot_table(index=date_col, columns=store_col, values=order_col, aggfunc='sum', fill_value=0)
            
            return sales_pivot_table, payouts_pivot_table, orders_pivot_table
        except Exception as e:
            st.error(f"Error processing {file_path.name} for date export: {str(e)}")
            import traceback
            with st.expander(f"Error details for {file_path.name}"):
                st.code(traceback.format_exc())
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Process all 8 files separately - each file gets its own entry
    result = {}
    
    # Process DD files
    dd_files = [
        (dd_pre_24_path, 'DD_PRE_24', dd_selected_stores),
        (dd_post_24_path, 'DD_POST_24', dd_selected_stores),
        (dd_pre_25_path, 'DD_PRE_25', dd_selected_stores),
        (dd_post_25_path, 'DD_POST_25', dd_selected_stores),
    ]
    
    for file_path, file_key, selected_stores in dd_files:
        if not file_path.exists():
            st.warning(f"File not found: {file_path}")
            continue
        try:
            sales, payouts, orders = process_dd_file_for_date_export(file_path, selected_stores)
            # Always add the file entry if at least one metric has data
            if not sales.empty or not payouts.empty or not orders.empty:
                result[file_key] = {
                    'Sales': sales if not sales.empty else pd.DataFrame(),
                    'Payouts': payouts if not payouts.empty else pd.DataFrame(),
                    'Orders': orders if not orders.empty else pd.DataFrame()
                }
            else:
                st.warning(f"No data extracted from {file_path.name} - all pivot tables are empty")
        except Exception as e:
            st.error(f"Error processing {file_path.name}: {str(e)}")
            import traceback
            with st.expander(f"Error details for {file_path.name}"):
                st.code(traceback.format_exc())
    
    # Process UE files
    ue_files = [
        (ue_pre_24_path, 'UE_PRE_24', ue_selected_stores),
        (ue_post_24_path, 'UE_POST_24', ue_selected_stores),
        (ue_pre_25_path, 'UE_PRE_25', ue_selected_stores),
        (ue_post_25_path, 'UE_POST_25', ue_selected_stores),
    ]
    
    for file_path, file_key, selected_stores in ue_files:
        if not file_path.exists():
            st.warning(f"File not found: {file_path}")
            continue
        try:
            sales, payouts, orders = process_ue_file_for_date_export(file_path, selected_stores)
            # Always add the file entry if at least one metric has data
            if not sales.empty or not payouts.empty or not orders.empty:
                result[file_key] = {
                    'Sales': sales if not sales.empty else pd.DataFrame(),
                    'Payouts': payouts if not payouts.empty else pd.DataFrame(),
                    'Orders': orders if not orders.empty else pd.DataFrame()
                }
            else:
                st.warning(f"No data extracted from {file_path.name} - all pivot tables are empty")
        except Exception as e:
            st.error(f"Error processing {file_path.name}: {str(e)}")
            import traceback
            with st.expander(f"Error details for {file_path.name}"):
                st.code(traceback.format_exc())
    
    return result if result else None


def create_date_export_from_master_files(dd_data_path, ue_data_path, pre_start_date, pre_end_date, post_start_date, post_end_date, excluded_dates=None):
    """
    Create date-wise exports of DD and UE financial data.
    Exports sales, payouts, orders store-wise for each date in the date ranges.
    Returns a zip file with CSV files organized by platform and period.
    
    Args:
        dd_data_path: Path to DoorDash master file
        ue_data_path: Path to UberEats master file
        pre_start_date: Pre period start date (MM/DD/YYYY)
        pre_end_date: Pre period end date (MM/DD/YYYY)
        post_start_date: Post period start date (MM/DD/YYYY)
        post_end_date: Post period end date (MM/DD/YYYY)
        excluded_dates: List of dates to exclude
    
    Returns:
        Tuple of (zip_bytes, filename) for download
    """
    try:
        # Calculate last year dates
        pre_24_start, pre_24_end = get_last_year_dates(pre_start_date, pre_end_date)
        post_24_start, post_24_end = get_last_year_dates(post_start_date, post_end_date)
        
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Process DoorDash data
            if dd_data_path and Path(dd_data_path).exists():
                # DD Pre 25
                dd_pre_25 = filter_master_file_by_date_range(
                    Path(dd_data_path), pre_start_date, pre_end_date,
                    ['Timestamp local date', 'Timestamp Local Date', 'Date', 'date'],
                    excluded_dates
                )
                if not dd_pre_25.empty:
                    _add_date_export_to_zip(zip_file, dd_pre_25, 'DD', 'Pre_25', 'Merchant store ID', 'Subtotal', 'Net total', 'DoorDash order ID')
                
                # DD Post 25
                dd_post_25 = filter_master_file_by_date_range(
                    Path(dd_data_path), post_start_date, post_end_date,
                    ['Timestamp local date', 'Timestamp Local Date', 'Date', 'date'],
                    excluded_dates
                )
                if not dd_post_25.empty:
                    _add_date_export_to_zip(zip_file, dd_post_25, 'DD', 'Post_25', 'Merchant store ID', 'Subtotal', 'Net total', 'DoorDash order ID')
                
                # DD Pre 24
                dd_pre_24 = filter_master_file_by_date_range(
                    Path(dd_data_path), pre_24_start, pre_24_end,
                    ['Timestamp local date', 'Timestamp Local Date', 'Date', 'date'],
                    excluded_dates
                )
                if not dd_pre_24.empty:
                    _add_date_export_to_zip(zip_file, dd_pre_24, 'DD', 'Pre_24', 'Merchant store ID', 'Subtotal', 'Net total (for historical reference only)', 'DoorDash order ID')
                
                # DD Post 24
                dd_post_24 = filter_master_file_by_date_range(
                    Path(dd_data_path), post_24_start, post_24_end,
                    ['Timestamp local date', 'Timestamp Local Date', 'Date', 'date'],
                    excluded_dates
                )
                if not dd_post_24.empty:
                    _add_date_export_to_zip(zip_file, dd_post_24, 'DD', 'Post_24', 'Merchant store ID', 'Subtotal', 'Net total (for historical reference only)', 'DoorDash order ID')
            
            # Process UberEats data
            if ue_data_path and Path(ue_data_path).exists():
                # UE Pre 25
                ue_pre_25 = filter_master_file_by_date_range(
                    Path(ue_data_path), pre_start_date, pre_end_date,
                    ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date'],
                    excluded_dates
                )
                if not ue_pre_25.empty:
                    ue_pre_25, store_col = normalize_store_id_column(ue_pre_25)
                    _add_date_export_to_zip(zip_file, ue_pre_25, 'UE', 'Pre_25', store_col, 'Sales (excl. tax)', 'Total payout', 'Order ID')
                
                # UE Post 25
                ue_post_25 = filter_master_file_by_date_range(
                    Path(ue_data_path), post_start_date, post_end_date,
                    ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date'],
                    excluded_dates
                )
                if not ue_post_25.empty:
                    ue_post_25, store_col = normalize_store_id_column(ue_post_25)
                    _add_date_export_to_zip(zip_file, ue_post_25, 'UE', 'Post_25', store_col, 'Sales (excl. tax)', 'Total payout', 'Order ID')
                
                # UE Pre 24
                ue_pre_24 = filter_master_file_by_date_range(
                    Path(ue_data_path), pre_24_start, pre_24_end,
                    ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date'],
                    excluded_dates
                )
                if not ue_pre_24.empty:
                    ue_pre_24, store_col = normalize_store_id_column(ue_pre_24)
                    _add_date_export_to_zip(zip_file, ue_pre_24, 'UE', 'Pre_24', store_col, 'Sales (excl. tax)', 'Total payout', 'Order ID')
                
                # UE Post 24
                ue_post_24 = filter_master_file_by_date_range(
                    Path(ue_data_path), post_24_start, post_24_end,
                    ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date'],
                    excluded_dates
                )
                if not ue_post_24.empty:
                    ue_post_24, store_col = normalize_store_id_column(ue_post_24)
                    _add_date_export_to_zip(zip_file, ue_post_24, 'UE', 'Post_24', store_col, 'Sales (excl. tax)', 'Total payout', 'Order ID')
        
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"date_export_{timestamp}.zip"
        
        return zip_buffer.read(), filename
    
    except Exception as e:
        st.error(f"Error creating date export: {str(e)}")
        import traceback
        with st.expander("Error details"):
            st.code(traceback.format_exc())
        return None, None


def _add_date_export_to_zip(zip_file, df, platform, period, store_col, sales_col, payout_col, order_col):
    """
    Helper function to create date-wise pivot tables and add them to zip file.
    
    Args:
        zip_file: ZipFile object
        df: DataFrame with data
        platform: 'DD' or 'UE'
        period: 'Pre_25', 'Post_25', 'Pre_24', 'Post_24'
        store_col: Name of store ID column
        sales_col: Name of sales column
        payout_col: Name of payout column
        order_col: Name of order ID column
    """
    try:
        # Find date column
        date_col = None
        if platform == 'DD':
            for col in ['Timestamp local date', 'Timestamp Local Date', 'Date', 'date']:
                if col in df.columns:
                    date_col = col
                    break
        else:  # UE
            for col in ['Order Date', 'Order date', 'order date', 'order Date', 'Date', 'date']:
                if col in df.columns:
                    date_col = col
                    break
        
        if date_col is None or store_col is None or store_col not in df.columns:
            return
        
        # Convert date column
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col, store_col])
        
        if df.empty:
            return
        
        # Convert to numeric
        if sales_col in df.columns:
            df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)
        if payout_col in df.columns:
            df[payout_col] = pd.to_numeric(df[payout_col], errors='coerce').fillna(0)
        
        # Aggregate by date and store
        sales_agg = df.groupby([date_col, store_col])[sales_col].sum().reset_index() if sales_col in df.columns else pd.DataFrame()
        payouts_agg = df.groupby([date_col, store_col])[payout_col].sum().reset_index() if payout_col in df.columns else pd.DataFrame()
        orders_agg = df.groupby([date_col, store_col])[order_col].nunique().reset_index() if order_col in df.columns else pd.DataFrame()
        
        # Pivot: Date as index, Store ID as columns
        if not sales_agg.empty:
            sales_pivot = sales_agg.pivot_table(index=date_col, columns=store_col, values=sales_col, aggfunc='sum', fill_value=0)
            sales_pivot.index = sales_pivot.index.strftime('%Y-%m-%d')
            sales_csv = sales_pivot.to_csv()
            zip_file.writestr(f"{platform}_{period}_Sales.csv", sales_csv)
        
        if not payouts_agg.empty:
            payouts_pivot = payouts_agg.pivot_table(index=date_col, columns=store_col, values=payout_col, aggfunc='sum', fill_value=0)
            payouts_pivot.index = payouts_pivot.index.strftime('%Y-%m-%d')
            payouts_csv = payouts_pivot.to_csv()
            zip_file.writestr(f"{platform}_{period}_Payouts.csv", payouts_csv)
        
        if not orders_agg.empty:
            orders_pivot = orders_agg.pivot_table(index=date_col, columns=store_col, values=order_col, aggfunc='sum', fill_value=0)
            orders_pivot.index = orders_pivot.index.strftime('%Y-%m-%d')
            orders_csv = orders_pivot.to_csv()
            zip_file.writestr(f"{platform}_{period}_Orders.csv", orders_csv)
    
    except Exception as e:
        st.warning(f"Error processing {platform} {period}: {str(e)}")
