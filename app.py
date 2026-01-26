import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from gdrive_utils import get_drive_manager

# Import from modules
from config import ROOT_DIR, DD_DATA_MASTER, UE_DATA_MASTER, DD_MKT_PRE_24, DD_MKT_POST_24, DD_MKT_PRE_25, DD_MKT_POST_25, UE_MKT_PRE_24, UE_MKT_POST_24, UE_MKT_PRE_25, UE_MKT_POST_25
from utils import normalize_store_id_column, filter_excluded_dates, filter_master_file_by_date_range
from data_loading import process_master_file_for_dd, process_master_file_for_ue
from data_processing import load_and_aggregate_ue_data, load_and_aggregate_dd_data, load_and_aggregate_new_customers, process_data, process_new_customers_data
from marketing_analysis import create_corporate_vs_todc_table
from table_generation import create_summary_tables, create_combined_summary_tables, create_combined_store_tables, get_platform_store_tables, get_platform_summary_tables
from ui_components import create_store_selector, display_store_tables, display_summary_tables, display_platform_data
from export_functions import export_to_excel, create_date_export
from file_upload_screen import display_file_upload_screen

# Set page config - Ensure sidebar is expanded by default
st.set_page_config(
    page_title="Delivery Platform Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global CSS for SaaS-like styling - Theme-aware
st.markdown("""
<style>
    /* Hide Streamlit branding but keep sidebar toggle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Don't hide header completely - it contains the sidebar toggle button */
    header {visibility: visible !important;}
    
    /* Ensure sidebar toggle button is visible */
    header button[kind="header"],
    header [data-testid="stHeader"] button,
    button[kind="header"] {
        visibility: visible !important;
        display: inline-block !important;
        z-index: 1000 !important;
    }
    
    /* Custom styling - Theme-aware */
    .stApp {
        background: var(--background-color);
        color: var(--text-color);
    }
    
    /* Sidebar styling - Theme-aware - Ensure visibility in production */
    section[data-testid="stSidebar"] {
        background: var(--secondary-background-color) !important;
        border-right: 1px solid rgba(0, 0, 0, 0.1) !important;
        visibility: visible !important;
    }
    
    /* Sidebar content container */
    section[data-testid="stSidebar"] > div {
        visibility: visible !important;
    }
    
    /* Sidebar navigation elements */
    section[data-testid="stSidebar"] .css-1d391kg,
    section[data-testid="stSidebar"] .css-1lcbmhc {
        visibility: visible !important;
    }
    
    /* Ensure sidebar is not hidden by any CSS */
    section[data-testid="stSidebar"][aria-expanded="true"] {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Sidebar when collapsed - still ensure toggle is visible */
    section[data-testid="stSidebar"][aria-expanded="false"] {
        display: none !important;
    }
    
    /* Sidebar toggle button - ensure it's always visible */
    button[kind="header"][data-testid="baseButton-header"] {
        visibility: visible !important;
        display: inline-block !important;
        z-index: 1000 !important;
    }
    
    /* Button styling - Dark text on light background for visibility */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
        background-color: #f0f2f6 !important; /* Light background */
        color: #262730 !important; /* Dark/black text */
        border: 1px solid #d1d5db !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        background-color: #e5e7eb !important; /* Slightly darker on hover */
        color: #262730 !important; /* Keep dark text */
    }
    
    /* Download button styling - Dark text on light background */
    .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
        background-color: #f0f2f6 !important; /* Light background */
        color: #262730 !important; /* Dark/black text */
        border: 1px solid #d1d5db !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        background-color: #e5e7eb !important; /* Slightly darker on hover */
        color: #262730 !important; /* Keep dark text */
    }
    
    /* Ensure all button text is dark and visible */
    .stButton > button,
    .stDownloadButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        color: #262730 !important; /* Force dark text */
    }
    
    /* File uploader styling */
    .uploadedFile {
        border-radius: 8px;
        background: var(--secondary-background-color);
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }
</style>
""", unsafe_allow_html=True)

# Initialize screen navigation
if "current_screen" not in st.session_state:
    st.session_state["current_screen"] = "upload"

# All functions have been moved to their respective modules:
# - marketing_analysis.py: find_marketing_folders, get_marketing_file_path, process_marketing_promotion_files, 
#   process_marketing_sponsored_files, create_corporate_vs_todc_table
# - utils.py: normalize_store_id_column, filter_excluded_dates, filter_master_file_by_date_range
# - data_loading.py: process_master_file_for_dd, process_master_file_for_ue
# - data_processing.py: load_and_aggregate_ue_data, load_and_aggregate_dd_data, load_and_aggregate_new_customers,
#   process_data, process_new_customers_data
# - table_generation.py: create_summary_tables, create_combined_summary_tables, create_combined_store_tables,
#   get_platform_store_tables, get_platform_summary_tables
# - ui_components.py: create_store_selector, display_store_tables, display_summary_tables, display_platform_data
# - export_functions.py: export_to_excel, create_date_export

def main():
    # Screen navigation
    current_screen = st.session_state.get("current_screen", "upload")
    
    # Navigation sidebar
    with st.sidebar:
        st.markdown("""
        <style>
        .sidebar-nav {
            padding: 1rem 0;
        }
        .nav-button {
            width: 100%;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            border: none;
            background: var(--secondary-background-color);
            cursor: pointer;
            transition: all 0.3s;
            color: var(--text-color);
        }
        .nav-button:hover {
            background: var(--background-color);
            opacity: 0.8;
        }
        .nav-button.active {
            background: var(--primary-color);
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🧭 Navigation")
        st.markdown("---")
        
        if current_screen == "upload":
            st.markdown("**📤 Upload Files** (Current)")
        else:
            if st.button("📤 Upload Files", width='stretch', key="nav_upload"):
                st.session_state["current_screen"] = "upload"
                st.rerun()
        
        if current_screen == "dashboard":
            st.markdown("**📊 Dashboard** (Current)")
        else:
            if st.button("📊 Dashboard", width='stretch', key="nav_dashboard"):
                if st.session_state.get("uploaded_dd_data") and st.session_state.get("uploaded_ue_data"):
                    st.session_state["current_screen"] = "dashboard"
                    st.rerun()
                else:
                    st.warning("⚠️ Please upload files first")
    
    # Display appropriate screen
    if current_screen == "upload":
        display_file_upload_screen()
        return
    
    # Dashboard screen
    st.title("📊 Delivery Platform Data Analysis Dashboard")
    
    # Get excluded dates from session state
    excluded_dates = st.session_state.get("excluded_dates", [])
    
    # Get date ranges from session state
    pre_start_date = st.session_state.get("pre_start_date", "")
    pre_end_date = st.session_state.get("pre_end_date", "")
    post_start_date = st.session_state.get("post_start_date", "")
    post_end_date = st.session_state.get("post_end_date", "")
    
    # Convert date strings to proper format for function calls
    pre_start = pre_start_date if pre_start_date else None
    pre_end = pre_end_date if pre_end_date else None
    post_start = post_start_date if post_start_date else None
    post_end = post_end_date if post_end_date else None
    
    # Get uploaded file paths (use uploaded files if available, otherwise fall back to config paths)
    dd_data_path = st.session_state.get("uploaded_dd_data", DD_DATA_MASTER)
    ue_data_path = st.session_state.get("uploaded_ue_data", UE_DATA_MASTER)
    marketing_folder_path = st.session_state.get("uploaded_marketing_folder", ROOT_DIR)
    
    # Load both platforms' data
    with st.spinner("Loading data for both platforms..."):
        # Load UberEats data (using master file if date ranges provided)
        (ue_pre_24_sales, ue_pre_24_payouts, ue_pre_24_orders, ue_post_24_sales, ue_post_24_payouts, ue_post_24_orders,
         ue_pre_25_sales, ue_pre_25_payouts, ue_pre_25_orders, ue_post_25_sales, ue_post_25_payouts, ue_post_25_orders) = load_and_aggregate_ue_data(
            excluded_dates=excluded_dates,
            pre_start_date=pre_start,
            pre_end_date=pre_end,
            post_start_date=post_start,
            post_end_date=post_end,
            ue_data_path=ue_data_path
        )
        ue_sales_df, ue_payouts_df, ue_orders_df = process_data(ue_pre_24_sales, ue_pre_24_payouts, ue_pre_24_orders, ue_post_24_sales, ue_post_24_payouts, ue_post_24_orders,
                                                                  ue_pre_25_sales, ue_pre_25_payouts, ue_pre_25_orders, ue_post_25_sales, ue_post_25_payouts, ue_post_25_orders)
        
        # Load DoorDash data (using financial files if date ranges provided)
        (dd_pre_24_sales, dd_pre_24_payouts, dd_pre_24_orders, dd_post_24_sales, dd_post_24_payouts, dd_post_24_orders,
         dd_pre_25_sales, dd_pre_25_payouts, dd_pre_25_orders, dd_post_25_sales, dd_post_25_payouts, dd_post_25_orders) = load_and_aggregate_dd_data(
            excluded_dates=excluded_dates,
            pre_start_date=pre_start,
            pre_end_date=pre_end,
            post_start_date=post_start,
            post_end_date=post_end,
            dd_data_path=dd_data_path
        )
        dd_sales_df, dd_payouts_df, dd_orders_df = process_data(dd_pre_24_sales, dd_pre_24_payouts, dd_pre_24_orders, dd_post_24_sales, dd_post_24_payouts, dd_post_24_orders,
                                                                  dd_pre_25_sales, dd_pre_25_payouts, dd_pre_25_orders, dd_post_25_sales, dd_post_25_payouts, dd_post_25_orders)
        
        # Load New Customers data - For DoorDash, aggregate from marketing_promotion* files
        (dd_pre_24_nc, dd_post_24_nc, dd_pre_25_nc, dd_post_25_nc,
         ue_pre_24_total, ue_post_24_total, ue_pre_25_total, ue_post_25_total) = load_and_aggregate_new_customers(
            excluded_dates=excluded_dates,
            pre_start_date=pre_start,
            pre_end_date=pre_end,
            post_start_date=post_start,
            post_end_date=post_end,
            marketing_folder_path=marketing_folder_path
        )
        dd_new_customers_df = process_new_customers_data(dd_pre_24_nc, dd_post_24_nc, dd_pre_25_nc, dd_post_25_nc, is_ue=False)
        # For UE, we'll handle platform totals in create_summary_tables
        ue_new_customers_df = pd.DataFrame(columns=['Store ID', 'pre_24', 'post_24', 'pre_25', 'post_25', 'PrevsPost', 'LastYear_Pre_vs_Post', 'YoY'])
        # Store UE platform totals in session state for use in summary tables
        st.session_state['ue_new_customers_totals'] = {
            'pre_24': ue_pre_24_total,
            'post_24': ue_post_24_total,
            'pre_25': ue_pre_25_total,
            'post_25': ue_post_25_total
        }
    
    # Initialize store selection with all stores by default (before sidebar)
    if not dd_sales_df.empty:
        all_dd_stores = sorted(dd_sales_df['Store ID'].unique().tolist())
        if "selected_stores_DoorDash" not in st.session_state or len(st.session_state.get("selected_stores_DoorDash", [])) == 0:
            st.session_state["selected_stores_DoorDash"] = all_dd_stores.copy()
    
    if not ue_sales_df.empty:
        all_ue_stores = sorted(ue_sales_df['Store ID'].unique().tolist())
        if "selected_stores_UberEats" not in st.session_state or len(st.session_state.get("selected_stores_UberEats", [])) == 0:
            st.session_state["selected_stores_UberEats"] = all_ue_stores.copy()
    
    # Sidebar for store selection and date exclusion
    with st.sidebar:
        # Date Range Selection for Master Files
        st.header("📆 Date Range Selection")
        with st.expander("📅 Pre/Post Date Ranges (Required)", expanded=True):
            st.info("**⚠️ Date ranges are required!** Enter Pre and Post date ranges in format: MM/DD/YYYY-MM/DD/YYYY (e.g., 11/1/2025-11/30/2025)")
            
            # Initialize session state for date ranges
            if "pre_date_range" not in st.session_state:
                st.session_state["pre_date_range"] = ""
            if "post_date_range" not in st.session_state:
                st.session_state["post_date_range"] = ""
            
            # Pre period date range
            st.subheader("Pre Period")
            pre_range = st.text_input(
                "Pre Date Range (MM/DD/YYYY-MM/DD/YYYY):",
                value=st.session_state["pre_date_range"],
                key="pre_range_input",
                help="Enter date range as: start-end, e.g., 11/1/2025-11/30/2025",
                placeholder="11/1/2025-11/30/2025"
            )
            
            # Post period date range
            st.subheader("Post Period")
            post_range = st.text_input(
                "Post Date Range (MM/DD/YYYY-MM/DD/YYYY):",
                value=st.session_state["post_date_range"],
                key="post_range_input",
                help="Enter date range as: start-end, e.g., 12/1/2025-12/31/2025",
                placeholder="12/1/2025-12/31/2025"
            )
            
            # Validate and apply button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Apply Date Ranges", type="primary", key="apply_date_ranges"):
                    # Parse and validate dates
                    valid = True
                    pre_start_date = None
                    pre_end_date = None
                    post_start_date = None
                    post_end_date = None
                    
                    # Parse Pre date range
                    if pre_range:
                        try:
                            if '-' in pre_range:
                                pre_parts = pre_range.split('-', 1)
                                pre_start_str = pre_parts[0].strip()
                                pre_end_str = pre_parts[1].strip()
                                
                                pre_start_date = pd.to_datetime(pre_start_str, format='%m/%d/%Y')
                                pre_end_date = pd.to_datetime(pre_end_str, format='%m/%d/%Y')
                                
                                if pre_start_date > pre_end_date:
                                    st.error("Pre Start Date must be before Pre End Date")
                                    valid = False
                                else:
                                    st.session_state["pre_date_range"] = pre_range
                                    st.session_state["pre_start_date"] = pre_start_str
                                    st.session_state["pre_end_date"] = pre_end_str
                            else:
                                st.error(f"Invalid Pre date range format. Use: MM/DD/YYYY-MM/DD/YYYY")
                                valid = False
                        except Exception as e:
                            st.error(f"Invalid Pre date range format: {pre_range}. Use: MM/DD/YYYY-MM/DD/YYYY")
                            valid = False
                    
                    # Parse Post date range
                    if post_range:
                        try:
                            if '-' in post_range:
                                post_parts = post_range.split('-', 1)
                                post_start_str = post_parts[0].strip()
                                post_end_str = post_parts[1].strip()
                                
                                post_start_date = pd.to_datetime(post_start_str, format='%m/%d/%Y')
                                post_end_date = pd.to_datetime(post_end_str, format='%m/%d/%Y')
                                
                                if post_start_date > post_end_date:
                                    st.error("Post Start Date must be before Post End Date")
                                    valid = False
                                else:
                                    st.session_state["post_date_range"] = post_range
                                    st.session_state["post_start_date"] = post_start_str
                                    st.session_state["post_end_date"] = post_end_str
                            else:
                                st.error(f"Invalid Post date range format. Use: MM/DD/YYYY-MM/DD/YYYY")
                                valid = False
                        except Exception as e:
                            st.error(f"Invalid Post date range format: {post_range}. Use: MM/DD/YYYY-MM/DD/YYYY")
                            valid = False
                    
                    if valid and (pre_range or post_range):
                        st.success("Date ranges applied! Reloading data...")
                        st.rerun()
                    elif not pre_range and not post_range:
                        st.warning("Please enter at least one date range")
            
            with col2:
                if st.button("Clear Date Ranges", key="clear_date_ranges"):
                    st.session_state["pre_date_range"] = ""
                    st.session_state["post_date_range"] = ""
                    st.session_state["pre_start_date"] = ""
                    st.session_state["pre_end_date"] = ""
                    st.session_state["post_start_date"] = ""
                    st.session_state["post_end_date"] = ""
                    st.rerun()
            
            # Show current date ranges
            if st.session_state.get("pre_date_range"):
                st.info(f"**Pre:** {st.session_state['pre_date_range']}")
            if st.session_state.get("post_date_range"):
                st.info(f"**Post:** {st.session_state['post_date_range']}")
        
        st.divider()
        
        st.header("🔍 Store Selection")
        
        # Check if files are uploaded and exist
        from pathlib import Path
        dd_file_path = st.session_state.get("uploaded_dd_data")
        ue_file_path = st.session_state.get("uploaded_ue_data")
        
        # Handle both Path objects and strings
        if dd_file_path:
            dd_file_path = Path(dd_file_path) if not isinstance(dd_file_path, Path) else dd_file_path
            dd_file_uploaded = dd_file_path.exists()
        else:
            dd_file_uploaded = False
            
        if ue_file_path:
            ue_file_path = Path(ue_file_path) if not isinstance(ue_file_path, Path) else ue_file_path
            ue_file_uploaded = ue_file_path.exists()
        else:
            ue_file_uploaded = False
        
        # Also check if date ranges are set
        date_ranges_set = bool(pre_start_date and pre_end_date and post_start_date and post_end_date)
        
        # DoorDash store selection
        create_store_selector("DoorDash", dd_sales_df, "selected_stores_DoorDash", 
                             file_uploaded=dd_file_uploaded, date_ranges_set=date_ranges_set)
        
        st.divider()
        
        # UberEats store selection
        create_store_selector("UberEats", ue_sales_df, "selected_stores_UberEats", 
                             file_uploaded=ue_file_uploaded, date_ranges_set=date_ranges_set)
    
    st.divider()
    
    # Date Exclusion Section
    st.header("📅 Date Exclusion")
    with st.expander("🚫 Exclude Dates from Analysis", expanded=False):
            # Initialize session state for excluded dates
            if "excluded_dates" not in st.session_state:
                st.session_state["excluded_dates"] = []
            
            # Text input for manual date entry (MM/DD/YYYY format) - primary method
            st.subheader("Enter Dates to Exclude")
            date_input_text = st.text_input(
                "Enter dates in MM/DD/YYYY format (comma-separated):",
                key="date_text_input",
                help="Example: 11/30/2024, 12/01/2024, 12/25/2024",
                placeholder="11/30/2024, 12/01/2024"
            )
            
            # Date picker for adding individual dates
            st.subheader("Or Add Date via Date Picker")
            new_date = st.date_input(
                "Select a date to add:",
                key="date_picker_exclude",
                help="Select a date and click 'Add Date' to add it to the exclusion list."
            )
            
            # Parse text input dates
            text_dates = []
            if date_input_text:
                date_strings = [d.strip() for d in date_input_text.split(',')]
                for date_str in date_strings:
                    if date_str:  # Skip empty strings
                        try:
                            # Parse MM/DD/YYYY format
                            parsed_date = pd.to_datetime(date_str, format='%m/%d/%Y')
                            text_dates.append(parsed_date.date())
                        except:
                            st.warning(f"Invalid date format: {date_str}. Please use MM/DD/YYYY format.")
            
            # Get current excluded dates from session state
            current_excluded = st.session_state["excluded_dates"].copy() if st.session_state["excluded_dates"] else []
            
            # Combine current excluded dates with text input dates
            all_excluded_dates = list(set(current_excluded + text_dates))
            
            # Display current excluded dates
            if all_excluded_dates:
                st.info(f"**{len(all_excluded_dates)}** date(s) will be excluded:")
                for date in sorted(all_excluded_dates):
                    st.text(f"  • {date.strftime('%m/%d/%Y')}")
            else:
                st.info("No dates excluded")
            
            # Buttons for managing dates
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Add Date", key="add_date_picker"):
                    if new_date not in all_excluded_dates:
                        all_excluded_dates.append(new_date)
                        st.session_state["excluded_dates"] = all_excluded_dates
                        st.rerun()
                    else:
                        st.warning("Date already in exclusion list")
            with col2:
                if st.button("Apply Exclusion", type="primary", key="apply_date_exclusion"):
                    st.session_state["excluded_dates"] = all_excluded_dates
                    st.rerun()
            with col3:
                if st.button("Clear All", key="clear_date_exclusion"):
                    st.session_state["excluded_dates"] = []
                    st.rerun()
        
    # Store selection is already initialized above (after data loading, before sidebar)
    
    # Store selection summary at the top
    st.subheader("📊 Store Selection Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        dd_total = len(dd_sales_df['Store ID'].unique()) if not dd_sales_df.empty else 0
        dd_selected = len(st.session_state.get("selected_stores_DoorDash", []))
        st.metric("DoorDash Stores", f"{dd_selected} / {dd_total}")
    
    with col2:
        ue_total = len(ue_sales_df['Store ID'].unique()) if not ue_sales_df.empty else 0
        ue_selected = len(st.session_state.get("selected_stores_UberEats", []))
        st.metric("UberEats Stores", f"{ue_selected} / {ue_total}")
    
    st.divider()
    
    # Export buttons at the top
    st.subheader("📥 Export Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        export_clicked = st.button("📊 Export All Tables to Excel", type="primary", width='stretch', key="export_excel")
    with col2:
        date_export_clicked = st.button("📅 Date Export", type="primary", width='stretch', key="export_date")
    with col3:
        dataset_export_clicked = st.button("📦 Export Dataset", type="primary", width='stretch', key="export_dataset")
    
    st.divider()
    
    # Get all table data first (needed for exports)
    dd_table1, dd_table2 = get_platform_store_tables(dd_sales_df, "selected_stores_DoorDash") if not dd_sales_df.empty else (None, None)
    ue_table1, ue_table2 = get_platform_store_tables(ue_sales_df, "selected_stores_UberEats") if not ue_sales_df.empty else (None, None)
    dd_summary1, dd_summary2 = get_platform_summary_tables(dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df, "selected_stores_DoorDash", is_ue=False) if not dd_sales_df.empty else (None, None)
    ue_summary1, ue_summary2 = get_platform_summary_tables(ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df, "selected_stores_UberEats", is_ue=True) if not ue_sales_df.empty else (None, None)
    combined_summary1, combined_summary2 = create_combined_summary_tables(
        dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df,
        ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df,
        st.session_state.get("selected_stores_DoorDash", []),
        st.session_state.get("selected_stores_UberEats", [])
    )
    combined_store_table1, combined_store_table2 = create_combined_store_tables(dd_table1, dd_table2, ue_table1, ue_table2)
    
    # Get Corporate vs TODC tables
    promotion_table, sponsored_table, corporate_todc_table = create_corporate_vs_todc_table(
        excluded_dates=excluded_dates,
        pre_start_date=pre_start,
        pre_end_date=pre_end,
        post_start_date=post_start,
        post_end_date=post_end,
        marketing_folder_path=marketing_folder_path
    )
    
    # Handle exports immediately after data is ready
    # Date Export functionality - DISABLED: Legacy file paths no longer exist
    # We now use master files (dd-data.csv, ue-data.csv) with date range filtering
    if date_export_clicked:
        st.warning("⚠️ Date Export functionality is currently disabled. We now use master files with date range filtering instead of legacy pre/post files.")
        # TODO: Re-implement date export using master files if needed
    
    # Export All Tables to Excel
    if export_clicked:
        try:
            with st.spinner("🔄 Exporting all tables to Excel..."):
                file_bytes, filename = export_to_excel(
                    dd_table1, dd_table2, ue_table1, ue_table2,
                    dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df,
                    ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df,
                    st.session_state.get("selected_stores_DoorDash", []),
                    st.session_state.get("selected_stores_UberEats", []),
                    combined_summary1, combined_summary2, combined_store_table1, combined_store_table2,
                    corporate_todc_table=corporate_todc_table,
                    promotion_table=promotion_table,
                    sponsored_table=sponsored_table
                )
                st.success(f"✅ **Export successful!** Click the button below to download the file.")
                st.download_button(
                    label="📥 Download Excel File",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    width='stretch'
                )
        except Exception as e:
            st.error(f"❌ **Export failed!** Error: {str(e)}")
            import traceback
            with st.expander("🔍 View Error Details"):
                st.code(traceback.format_exc())
    
    # Export Dataset (all root folder files except app)
    if dataset_export_clicked:
        try:
            with st.spinner("🔄 Exporting dataset to Google Drive..."):
                drive_manager = get_drive_manager()
                if not drive_manager:
                    st.error("❌ **Google Drive not initialized!** Please check your service account credentials.")
                else:
                    root_folder_name = ROOT_DIR.name  # Get root folder name (e.g., "BigGee-Jan")
                    
                    # Upload all files from root directory (excluding app folder)
                    result = drive_manager.upload_directory(
                        directory_path=ROOT_DIR,
                        root_folder_name=root_folder_name,
                        subfolder_name="datasets",
                        exclude_dirs=["app"]
                    )
                    
                    # Display results
                    if result['success_count'] > 0:
                        st.success(f"✅ **Dataset Export successful!** Uploaded {result['success_count']} out of {result['total_count']} files to Google Drive.")
                        
                        # Show uploaded files in an expander
                        with st.expander(f"📋 View {result['success_count']} Uploaded Files"):
                            for file_info in result['uploaded_files'][:50]:  # Show first 50 files
                                st.markdown(f"- [{file_info['name']}]({file_info['webViewLink']})")
                            if len(result['uploaded_files']) > 50:
                                st.info(f"... and {len(result['uploaded_files']) - 50} more files")
                        
                        # Show failed files if any
                        if result['failed_count'] > 0:
                            st.warning(f"⚠️ **{result['failed_count']} files failed to upload:**")
                            with st.expander("🔍 View Failed Files"):
                                for file_info in result['failed_files']:
                                    st.error(f"❌ {file_info['name']}: {file_info['error']}")
                    else:
                        st.warning("⚠️ **No files were uploaded.** Please check if there are files in the root directory.")
                    
                    # Show folder location
                    st.info(f"📁 Files uploaded to: `{root_folder_name}/datasets/` in Google Drive")
                    
        except Exception as e:
            st.error(f"❌ **Dataset Export failed!** Error: {str(e)}")
            import traceback
            with st.expander("🔍 View Error Details"):
                st.code(traceback.format_exc())
    
    # 1. Combined Store-Level Tables
    st.header("🔗 Combined Store-Level Analysis (DoorDash + UberEats)")
    st.caption("💡 Values are summed for stores that appear in both platforms")
    if combined_store_table1 is not None and not combined_store_table1.empty:
        st.subheader("Combined Table 1: Current Year Pre vs Post Analysis (Store-Level)")
        combined_store1_display = combined_store_table1.reset_index() if combined_store_table1.index.name == 'Store ID' else combined_store_table1.copy()
        # Filter out rows with no data (both Pre and Post are 0 or NaN)
        if 'Pre' in combined_store1_display.columns and 'Post' in combined_store1_display.columns:
            combined_store1_display = combined_store1_display[
                (combined_store1_display['Pre'].fillna(0) != 0) | (combined_store1_display['Post'].fillna(0) != 0)
            ]
        # Only display if there's data after filtering
        if not combined_store1_display.empty and 'Pre' in combined_store1_display.columns:
            if 'Pre' in combined_store1_display.columns:
                combined_store1_display['Pre'] = combined_store1_display['Pre'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            if 'Post' in combined_store1_display.columns:
                combined_store1_display['Post'] = combined_store1_display['Post'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            if 'PrevsPost' in combined_store1_display.columns:
                combined_store1_display['PrevsPost'] = combined_store1_display['PrevsPost'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            if 'LastYear Pre vs Post' in combined_store1_display.columns:
                combined_store1_display['LastYear Pre vs Post'] = combined_store1_display['LastYear Pre vs Post'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            if 'Growth%' in combined_store1_display.columns:
                combined_store1_display['Growth%'] = combined_store1_display['Growth%'].apply(lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x)
            if 'Store ID' in combined_store1_display.columns:
                combined_store1_display = combined_store1_display.set_index('Store ID')
            st.dataframe(combined_store1_display, width='stretch', height=400)
        else:
            st.info("No data available for Combined Table 1")
    
    # Combined Table 2 (YoY) - Store-Level
    if combined_store_table2 is not None and not combined_store_table2.empty:
        st.subheader("Combined Table 2: Year-over-Year Analysis (Store-Level)")
        combined_store2_display = combined_store_table2.reset_index() if combined_store_table2.index.name == 'Store ID' else combined_store_table2.copy()
        
        # Filter out rows with no data (both last year-post and post are 0 or NaN)
        if 'last year-post' in combined_store2_display.columns and 'post' in combined_store2_display.columns:
            combined_store2_display = combined_store2_display[
                (combined_store2_display['last year-post'].fillna(0) != 0) | (combined_store2_display['post'].fillna(0) != 0)
            ]
        
        # Only display if there's data after filtering
        if not combined_store2_display.empty:
            # Format dollar columns
            if 'last year-post' in combined_store2_display.columns:
                combined_store2_display['last year-post'] = combined_store2_display['last year-post'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            if 'post' in combined_store2_display.columns:
                combined_store2_display['post'] = combined_store2_display['post'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            if 'YoY' in combined_store2_display.columns:
                combined_store2_display['YoY'] = combined_store2_display['YoY'].apply(lambda x: f"${x:,.1f}" if isinstance(x, (int, float)) else x)
            # Format percentage column
            if 'YoY%' in combined_store2_display.columns:
                combined_store2_display['YoY%'] = combined_store2_display['YoY%'].apply(lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x)
            
            if 'Store ID' in combined_store2_display.columns:
                combined_store2_display = combined_store2_display.set_index('Store ID')
            st.dataframe(combined_store2_display, width='stretch', height=400)
        else:
            st.info("No data available for Combined Table 2")
    
    st.divider()
    
    # 2. DoorDash Store-Level Tables
    st.header("🚪 DoorDash Store-Level Analysis")
    if dd_table1 is not None:
        display_store_tables("DoorDash", dd_table1, dd_table2)
    
    st.divider()
    
    # 3. UberEats Store-Level Tables
    st.header("🚗 UberEats Store-Level Analysis")
    if ue_table1 is not None:
        display_store_tables("UberEats", ue_table1, ue_table2)
    
    st.divider()
    
    # 4. Combined Summary Tables
    st.header("🔗 Combined Summary Analysis (DoorDash + UberEats)")
    st.subheader("📊 Combined Summary Tables")
    
    # Format Table 1
    combined_summary1_display = combined_summary1.copy()
    # Convert columns to object type to avoid dtype warnings when assigning formatted strings
    for col in combined_summary1_display.columns:
        combined_summary1_display[col] = combined_summary1_display[col].astype(object)
    
    for idx in combined_summary1_display.index:
        metric = idx
        if metric == 'Orders' or metric == 'New Customers':
            # Orders: format as integer string
            combined_summary1_display.loc[idx, 'Pre'] = f"{int(round(combined_summary1.loc[idx, 'Pre'])):,}"
            combined_summary1_display.loc[idx, 'Post'] = f"{int(round(combined_summary1.loc[idx, 'Post'])):,}"
            combined_summary1_display.loc[idx, 'PrevsPost'] = f"{int(round(combined_summary1.loc[idx, 'PrevsPost'])):,}"
            combined_summary1_display.loc[idx, 'LastYear Pre vs Post'] = f"{int(round(combined_summary1.loc[idx, 'LastYear Pre vs Post'])):,}"
        else:
            combined_summary1_display.loc[idx, 'Pre'] = f"${combined_summary1.loc[idx, 'Pre']:,.1f}"
            combined_summary1_display.loc[idx, 'Post'] = f"${combined_summary1.loc[idx, 'Post']:,.1f}"
            combined_summary1_display.loc[idx, 'PrevsPost'] = f"${combined_summary1.loc[idx, 'PrevsPost']:,.1f}"
            combined_summary1_display.loc[idx, 'LastYear Pre vs Post'] = f"${combined_summary1.loc[idx, 'LastYear Pre vs Post']:,.1f}"
        combined_summary1_display.loc[idx, 'Growth%'] = f"{combined_summary1.loc[idx, 'Growth%']:.1f}%"
    
    # Ensure all columns are string type for Arrow compatibility
    for col in combined_summary1_display.columns:
        combined_summary1_display[col] = combined_summary1_display[col].astype(str)
    
    st.write("**Combined Table 1: Current Year Pre vs Post Analysis**")
    st.dataframe(combined_summary1_display, width='stretch')
    
    # Format Table 2
    combined_summary2_display = combined_summary2.copy()
    # Convert columns to object type to avoid dtype warnings when assigning formatted strings
    for col in combined_summary2_display.columns:
        combined_summary2_display[col] = combined_summary2_display[col].astype(object)
    
    for idx in combined_summary2_display.index:
        metric = idx
        if metric == 'Orders' or metric == 'New Customers':
            # Orders: format as integer string
            combined_summary2_display.loc[idx, 'last year-post'] = f"{int(round(combined_summary2.loc[idx, 'last year-post'])):,}"
            combined_summary2_display.loc[idx, 'post'] = f"{int(round(combined_summary2.loc[idx, 'post'])):,}"
            combined_summary2_display.loc[idx, 'YoY'] = f"{int(round(combined_summary2.loc[idx, 'YoY'])):,}"
        else:
            combined_summary2_display.loc[idx, 'last year-post'] = f"${combined_summary2.loc[idx, 'last year-post']:,.1f}"
            combined_summary2_display.loc[idx, 'post'] = f"${combined_summary2.loc[idx, 'post']:,.1f}"
            combined_summary2_display.loc[idx, 'YoY'] = f"${combined_summary2.loc[idx, 'YoY']:,.1f}"
        combined_summary2_display.loc[idx, 'YoY%'] = f"{combined_summary2.loc[idx, 'YoY%']:.1f}%"
    
    # Ensure all columns are string type for Arrow compatibility
    for col in combined_summary2_display.columns:
        combined_summary2_display[col] = combined_summary2_display[col].astype(str)
    
    st.write("**Combined Table 2: Year-over-Year Analysis**")
    st.dataframe(combined_summary2_display, width='stretch')
    
    st.divider()
    
    # 5. DoorDash Summary Tables
    st.header("🚪 DoorDash Summary Analysis")
    st.subheader("📊 DoorDash Summary Tables")
    if dd_summary1 is not None and dd_summary2 is not None:
        display_summary_tables("DoorDash", dd_summary1, dd_summary2)
    
    st.divider()
    
    # 6. UberEats Summary Tables
    st.header("🚗 UberEats Summary Analysis")
    st.subheader("📊 UberEats Summary Tables")
    if ue_summary1 is not None and ue_summary2 is not None:
        display_summary_tables("UberEats", ue_summary1, ue_summary2)
    
    st.divider()
    
    # 7. Corporate vs TODC Table
    st.header("🏢 Corporate vs TODC Analysis")
    if corporate_todc_table is not None and not corporate_todc_table.empty:
        st.subheader("Combined: Corporate vs TODC")
        corporate_display = corporate_todc_table.copy()
        
        # Format the display
        corporate_display['Orders'] = corporate_display['Orders'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        corporate_display['Sales'] = corporate_display['Sales'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
        corporate_display['Spend'] = corporate_display['Spend'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
        corporate_display['ROAS'] = corporate_display['ROAS'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
        corporate_display['Cost per Order'] = corporate_display['Cost per Order'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
        
        # Rename index for display (False = Corporate, True = TODC)
        corporate_display.index.name = 'Is Self Serve Campaign'
        corporate_display = corporate_display.reset_index()
        corporate_display['Is Self Serve Campaign'] = corporate_display['Is Self Serve Campaign'].apply(
            lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
        )
        corporate_display = corporate_display.set_index('Is Self Serve Campaign')
        
        st.dataframe(corporate_display, width='stretch', height=200)
        
        # Show individual tables in expanders
        with st.expander("📊 Promotion Table Details", expanded=False):
            if not promotion_table.empty:
                promo_display = promotion_table.copy()
                promo_display['Orders'] = promo_display['Orders'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
                promo_display['Sales'] = promo_display['Sales'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
                promo_display['Spend'] = promo_display['Spend'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
                promo_display['ROAS'] = promo_display['ROAS'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
                promo_display['Cost per Order'] = promo_display['Cost per Order'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
                promo_display.index.name = 'Is Self Serve Campaign'
                promo_display = promo_display.reset_index()
                promo_display['Is Self Serve Campaign'] = promo_display['Is Self Serve Campaign'].apply(
                    lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
                )
                promo_display = promo_display.set_index('Is Self Serve Campaign')
                st.dataframe(promo_display, width='stretch')
            else:
                st.info("No promotion data available")
        
        with st.expander("📊 Sponsored Listing Table Details", expanded=False):
            if not sponsored_table.empty:
                sponsored_display = sponsored_table.copy()
                sponsored_display['Orders'] = sponsored_display['Orders'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
                sponsored_display['Sales'] = sponsored_display['Sales'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
                sponsored_display['Spend'] = sponsored_display['Spend'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
                sponsored_display['ROAS'] = sponsored_display['ROAS'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
                sponsored_display['Cost per Order'] = sponsored_display['Cost per Order'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
                sponsored_display.index.name = 'Is Self Serve Campaign'
                sponsored_display = sponsored_display.reset_index()
                sponsored_display['Is Self Serve Campaign'] = sponsored_display['Is Self Serve Campaign'].apply(
                    lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
                )
                sponsored_display = sponsored_display.set_index('Is Self Serve Campaign')
                st.dataframe(sponsored_display, width='stretch')
            else:
                st.info("No sponsored listing data available")
    else:
        st.info("No marketing data available. Please ensure marketing_* folders exist with MARKETING_PROMOTION and MARKETING_SPONSORED_LISTING files.")

if __name__ == "__main__":
    main()

