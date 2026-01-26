"""Export functions for Excel and date exports"""
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from config import ROOT_DIR
from gdrive_utils import get_drive_manager
from utils import normalize_store_id_column
from table_generation import create_summary_tables


def export_to_excel(dd_table1, dd_table2, ue_table1, ue_table2, 
                     dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df,
                     ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df,
                     dd_selected_stores, ue_selected_stores,
                     combined_summary1, combined_summary2, combined_store_table1, combined_store_table2):
    """Export all tables to an Excel file with 2 sheets: Summary Tables and Store-Level Tables"""
    # Create outputs folder if it doesn't exist
    outputs_dir = ROOT_DIR / "outputs"
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
        # Check if Store ID or Metric is in index
        if df.index.name in ['Store ID', 'Metric'] or (hasattr(df.index, 'name') and df.index.name):
            # Reset index to include it as a column
            df_display = df.reset_index()
        elif 'Store ID' not in df.columns and 'Metric' not in df.columns:
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
                elif col_name in ['Store ID', 'Metric']:
                    # Keep as is (text)
                    pass
                elif is_orders_row or is_new_customers_row:
                    # Orders and New Customers rows: format as integer with comma separators (no decimals, no dollar sign)
                    if isinstance(value, (int, float)):
                        cell.value = f"{int(round(value)):,}"
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
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_export_{timestamp}.xlsx"
    filepath = outputs_dir / filename
    
    # Save workbook
    wb.save(filepath)
    
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
            st.success(f"✅ **Export successful!** Excel file saved locally and uploaded to Google Drive.")
            st.info(f"📤 File uploaded to Google Drive: [{upload_result['file_name']}]({upload_result['webViewLink']})")
            st.info(f"📁 Local file saved to: `{filepath}`")
    except Exception as e:
        st.warning(f"⚠️ Local file saved, but Google Drive upload failed: {str(e)}")
        st.info(f"📁 Local file saved to: `{filepath}`")
    
    return filepath


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
            
            # Use "Order Date" for UE (capital 'D')
            # Try both case variations for robustness
            date_col = None
            for col in df.columns:
                if col.lower() == 'order date':
                    date_col = col
                    break
            
            if date_col is None:
                date_col = 'Order Date'  # Default fallback
            
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
