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
from export_functions import export_to_excel, create_date_export, create_date_export_from_master_files
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
            if st.button("📤 Upload Files", key="nav_upload"):
                st.session_state["current_screen"] = "upload"
                st.rerun()
        
        if current_screen == "dashboard":
            st.markdown("**📊 Dashboard** (Current)")
        else:
            if st.button("📊 Dashboard", key="nav_dashboard"):
                # Allow navigation to dashboard if date ranges are set, even without all files
                pre_start = st.session_state.get("pre_start_date", "")
                pre_end = st.session_state.get("pre_end_date", "")
                post_start = st.session_state.get("post_start_date", "")
                post_end = st.session_state.get("post_end_date", "")
                dates_set = bool(pre_start and pre_end and post_start and post_end)
                
                if dates_set:
                    st.session_state["current_screen"] = "dashboard"
                    st.rerun()
                else:
                    st.warning("⚠️ Please set date ranges first (use 'Start Analysis' button after entering dates)")
    
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
    # Also check root folder for files if not uploaded
    from pathlib import Path
    
    dd_data_path = st.session_state.get("uploaded_dd_data")
    if dd_data_path is None:
        # Check if dd-data.csv exists in root
        if DD_DATA_MASTER.exists():
            dd_data_path = DD_DATA_MASTER
        else:
            # Try to find any CSV file that might be DoorDash data in root folder
            root_csvs = list(ROOT_DIR.glob("*.csv"))
            # Look for files that might be DoorDash (contain "FINANCIAL" or "dd" or "doordash")
            dd_candidates = [f for f in root_csvs if any(keyword in f.name.upper() for keyword in ['FINANCIAL', 'DD', 'DOORDASH'])]
            if dd_candidates:
                dd_data_path = dd_candidates[0]  # Use first match
                st.info(f"📁 Auto-detected DoorDash file: {dd_data_path.name}")
            else:
                dd_data_path = DD_DATA_MASTER
    
    ue_data_path = st.session_state.get("uploaded_ue_data")
    if ue_data_path is None:
        # Check if ue-data.csv exists in root
        if UE_DATA_MASTER.exists():
            ue_data_path = UE_DATA_MASTER
        else:
            # Try to find any CSV file that might be UberEats data in root folder
            root_csvs = list(ROOT_DIR.glob("*.csv"))
            # Look for files that might be UberEats (contain "ue" or "ubereats")
            ue_candidates = [f for f in root_csvs if any(keyword in f.name.upper() for keyword in ['UE', 'UBEREATS', 'ORDER'])]
            if ue_candidates:
                ue_data_path = ue_candidates[0]  # Use first match
                st.info(f"📁 Auto-detected UberEats file: {ue_data_path.name}")
            else:
                ue_data_path = UE_DATA_MASTER
    
    marketing_folder_path = st.session_state.get("uploaded_marketing_folder")
    if marketing_folder_path is None:
        # Check if marketing folder exists in root
        marketing_candidates = list(ROOT_DIR.glob("marketing*"))
        if marketing_candidates and marketing_candidates[0].is_dir():
            marketing_folder_path = marketing_candidates[0]
            st.info(f"📁 Auto-detected marketing folder: {marketing_folder_path.name}")
        else:
            marketing_folder_path = ROOT_DIR
    
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
    
    # Sidebar for store selection, date ranges, and date exclusion
    with st.sidebar:
        # Date Range Selection for Master Files
        st.header("📆 Date Range Selection")
        with st.expander("📅 Pre/Post Date Ranges (Required)", expanded=True):
            st.info("**⚠️ Date ranges are required!** Enter Pre and Post date ranges in format: MM/DD/YYYY-MM/DD/YYYY")
            
            # Initialize session state for date ranges and operator name
            if "pre_date_range" not in st.session_state:
                st.session_state["pre_date_range"] = ""
            if "post_date_range" not in st.session_state:
                st.session_state["post_date_range"] = ""
            if "operator_name" not in st.session_state:
                st.session_state["operator_name"] = ""
            
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
            
            # Operator name (for export filenames)
            operator_name_sidebar = st.text_input(
                "Operator name (for exports):",
                value=st.session_state.get("operator_name", ""),
                key="operator_name_sidebar",
                help="e.g. alpha → alpha_analysis_export_.... Leave blank for default.",
                placeholder="e.g. alpha"
            )
            if operator_name_sidebar is not None and str(operator_name_sidebar).strip():
                st.session_state["operator_name"] = str(operator_name_sidebar).strip()
            else:
                st.session_state["operator_name"] = ""
            
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
        
        # Date Exclusion (in side panel)
        st.header("📅 Date Exclusion")
        with st.expander("🚫 Exclude Dates from Analysis", expanded=False):
            if "excluded_dates" not in st.session_state:
                st.session_state["excluded_dates"] = []
            st.subheader("Enter Dates to Exclude")
            date_input_text = st.text_input(
                "Dates (MM/DD/YYYY, comma-separated):",
                key="date_text_input",
                help="Example: 11/30/2024, 12/01/2024",
                placeholder="11/30/2024, 12/01/2024"
            )
            new_date = st.date_input("Or add via date picker:", key="date_picker_exclude")
            text_dates = []
            if date_input_text:
                for date_str in [d.strip() for d in date_input_text.split(',') if d.strip()]:
                    try:
                        text_dates.append(pd.to_datetime(date_str, format='%m/%d/%Y').date())
                    except Exception:
                        st.warning(f"Invalid date: {date_str}. Use MM/DD/YYYY.")
            current_excluded = st.session_state["excluded_dates"].copy() if st.session_state["excluded_dates"] else []
            all_excluded_dates = list(set(current_excluded + text_dates))
            if all_excluded_dates:
                st.info(f"**{len(all_excluded_dates)}** date(s) excluded")
                for d in sorted(all_excluded_dates):
                    st.caption(f"  • {d.strftime('%m/%d/%Y')}")
            else:
                st.info("No dates excluded")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Add Date", key="add_date_picker"):
                    if new_date not in all_excluded_dates:
                        all_excluded_dates.append(new_date)
                        st.session_state["excluded_dates"] = all_excluded_dates
                        st.rerun()
                    else:
                        st.warning("Date already in list")
            with c2:
                if st.button("Apply Exclusion", type="primary", key="apply_date_exclusion"):
                    st.session_state["excluded_dates"] = all_excluded_dates
                    st.rerun()
            with c3:
                if st.button("Clear All", key="clear_date_exclusion"):
                    st.session_state["excluded_dates"] = []
                    st.rerun()
    
    # Store selection is already initialized above (after data loading, before sidebar)
    
    # Get all table data first (needed for exports and top summary)
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
    
    # Top summary table (at top of dashboard)
    linear_growth = combined_summary1.loc['Sales', 'Growth%'] if combined_summary1 is not None and not combined_summary1.empty and 'Sales' in combined_summary1.index and 'Growth%' in combined_summary1.columns else 0
    yoy_growth = combined_summary2.loc['Sales', 'YoY%'] if combined_summary2 is not None and not combined_summary2.empty and 'Sales' in combined_summary2.index and 'YoY%' in combined_summary2.columns else 0
    dgc = combined_summary1.loc['Orders', 'Growth%'] if combined_summary1 is not None and not combined_summary1.empty and 'Orders' in combined_summary1.index and 'Growth%' in combined_summary1.columns else 0
    nc_growth = combined_summary1.loc['New Customers', 'Growth%'] if combined_summary1 is not None and not combined_summary1.empty and 'New Customers' in combined_summary1.index and 'Growth%' in combined_summary1.columns else 0
    dd_store_count = max(1, len(st.session_state.get("selected_stores_DoorDash", [])))
    payouts_prevs_post = combined_summary1.loc['Payouts', 'PrevsPost'] if combined_summary1 is not None and not combined_summary1.empty and 'Payouts' in combined_summary1.index and 'PrevsPost' in combined_summary1.columns else 0
    payouts_per_store = payouts_prevs_post / dd_store_count if dd_store_count else 0
    st.subheader("📈 Summary Metrics")
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.metric("Linear Growth", f"{linear_growth:.1f}%", "Combined pre vs post sales growth%")
    with s2:
        st.metric("YoY Growth", f"{yoy_growth:.1f}%", "Combined YoY sales growth%")
    with s3:
        st.metric("DGC", f"{dgc:.1f}%", "Combined pre vs post orders growth%")
    with s4:
        st.metric("New Customers", f"{nc_growth:.1f}%", "Combined new customers growth%")
    with s5:
        st.metric("Payouts Increase per store", f"${payouts_per_store:,.1f}", f"Payout pre vs post / {dd_store_count} DD stores")
    
    # Summary Metrics Table
    # Get date ranges from session state
    pre_start_date = st.session_state.get("pre_start_date", "")
    pre_end_date = st.session_state.get("pre_end_date", "")
    post_start_date = st.session_state.get("post_start_date", "")
    post_end_date = st.session_state.get("post_end_date", "")
    
    pre_date_range = f"{pre_start_date} - {pre_end_date}" if pre_start_date and pre_end_date else ""
    post_date_range = f"{post_start_date} - {post_end_date}" if post_start_date and post_end_date else ""
    
    # Get store counts
    dd_stores = st.session_state.get("selected_stores_DoorDash", [])
    ue_stores = st.session_state.get("selected_stores_UberEats", [])
    dd_store_count = len(dd_stores) if dd_stores else 0
    ue_store_count = len(ue_stores) if ue_stores else 0
    
    summary_metrics_data = {
        'Metric': [
            'Stores',
            'Pre',
            'Post',
            'Linear Growth',
            'YoY Growth',
            'DGC',
            'New Customers',
            'Payouts Increase per store',
            'Average Markup',
            'Pre TODC Growth YoY'
        ],
        'Value': [
            f"DD: {dd_store_count}, UE: {ue_store_count}",
            pre_date_range,
            post_date_range,
            f"{linear_growth:.1f}%",
            f"{yoy_growth:.1f}%",
            f"{dgc:.1f}%",
            f"{nc_growth:.1f}%",
            f"${payouts_per_store:,.1f}",
            "",  # Average Markup - empty value
            ""   # Pre TODC Growth YoY - empty value
        ]
    }
    summary_metrics_df = pd.DataFrame(summary_metrics_data)
    st.dataframe(summary_metrics_df, use_container_width=True, hide_index=True)
    
    # Build Merchant Store IDs / Markups table (export only, not shown in Streamlit)
    dd_stores_list = st.session_state.get("selected_stores_DoorDash", []) or []
    ue_stores_list = st.session_state.get("selected_stores_UberEats", []) or []
    all_store_ids = list(dict.fromkeys([str(s) for s in dd_stores_list] + [str(s) for s in ue_stores_list]))
    store_ids_markups_df = pd.DataFrame({
        "Merchant Store IDs": all_store_ids,
        "Markups": [""] * len(all_store_ids)
    }) if all_store_ids else pd.DataFrame(columns=["Merchant Store IDs", "Markups"])
    
    st.divider()
    
    # Store selection summary
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
    
    # Export buttons
    st.subheader("📥 Export Data")
    col1, col2 = st.columns(2)
    with col1:
        export_clicked = st.button("📊 Export All Tables to Excel", type="primary", key="export_excel")
    with col2:
        date_export_clicked = st.button("📅 Date Export", type="primary", key="export_date")
    st.divider()
    
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
    # Date Export functionality
    if date_export_clicked:
        if not (pre_start and pre_end and post_start and post_end):
            st.error("❌ **Date ranges required!** Please set Pre and Post date ranges in the sidebar.")
        else:
            try:
                with st.spinner("🔄 Creating date-wise export..."):
                    excel_bytes, excel_filename = create_date_export_from_master_files(
                        dd_data_path=dd_data_path,
                        ue_data_path=ue_data_path,
                        pre_start_date=pre_start,
                        pre_end_date=pre_end,
                        post_start_date=post_start,
                        post_end_date=post_end,
                        excluded_dates=excluded_dates,
                        operator_name=st.session_state.get("operator_name") or None
                    )
                    if excel_bytes and excel_filename:
                        st.success(f"✅ **Date Export successful!** Excel file ready for download and uploaded to Google Drive.")
                        st.download_button(
                            label="📥 Download Date Export (Excel)",
                            data=excel_bytes,
                            file_name=excel_filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                        # Upload to Google Drive (same as Export All Tables)
                        tmp_path = None
                        try:
                            import os
                            import tempfile
                            from gdrive_utils import get_drive_manager
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                                tmp.write(excel_bytes)
                                tmp_path = tmp.name
                            drive_manager = get_drive_manager()
                            if drive_manager:
                                upload_result = drive_manager.upload_file_to_subfolder(
                                    file_path=tmp_path,
                                    root_folder_name="cloud-app-uploads",
                                    subfolder_name="date-exports",
                                    file_name=excel_filename
                                )
                                link = upload_result.get('webViewLink') or f"https://drive.google.com/file/d/{upload_result.get('file_id', '')}/view"
                                st.info(f"📤 File uploaded to Google Drive: [{upload_result['file_name']}]({link})")
                        except Exception as e:
                            st.warning(f"⚠️ Google Drive upload failed: {str(e)}")
                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                try:
                                    os.unlink(tmp_path)
                                except Exception:
                                    pass
                    else:
                        st.error("❌ **Date Export failed!** Please check your data files and date ranges.")
            except Exception as e:
                st.error(f"❌ **Date Export failed!** Error: {str(e)}")
                import traceback
                with st.expander("🔍 View Error Details"):
                    st.code(traceback.format_exc())
    
    # Initialize slot table variables (needed for export)
    sales_pre_post_table = None
    sales_yoy_table = None
    payouts_pre_post_table = None
    payouts_yoy_table = None
    
    # Process slot analysis if DD data is available (needed for export)
    if dd_data_path and Path(dd_data_path).exists():
        from slot_analysis import process_slot_analysis
        try:
            sales_pre_post_table, sales_yoy_table, payouts_pre_post_table, payouts_yoy_table = process_slot_analysis(
                dd_data_path,
                pre_start_date=pre_start,
                pre_end_date=pre_end,
                post_start_date=post_start,
                post_end_date=post_end,
                excluded_dates=excluded_dates
            )
        except Exception as e:
            # Silently fail here - will be handled in display section
            pass
    
    # Export All Tables to Excel - Direct download
    if export_clicked:
        try:
            with st.spinner("🔄 Exporting all tables to Excel..."):
                pre_date_range_str = f"{pre_start_date} - {pre_end_date}" if pre_start_date and pre_end_date else ""
                post_date_range_str = f"{post_start_date} - {post_end_date}" if post_start_date and post_end_date else ""
                file_bytes, filename = export_to_excel(
                    dd_table1, dd_table2, ue_table1, ue_table2,
                    dd_sales_df, dd_payouts_df, dd_orders_df, dd_new_customers_df,
                    ue_sales_df, ue_payouts_df, ue_orders_df, ue_new_customers_df,
                    st.session_state.get("selected_stores_DoorDash", []),
                    st.session_state.get("selected_stores_UberEats", []),
                    combined_summary1, combined_summary2, combined_store_table1, combined_store_table2,
                    corporate_todc_table=corporate_todc_table,
                    promotion_table=promotion_table,
                    sponsored_table=sponsored_table,
                    summary_metrics_table=summary_metrics_df,
                    store_ids_markups_table=store_ids_markups_df,
                    operator_name=st.session_state.get("operator_name") or None,
                    sales_pre_post_table=sales_pre_post_table,
                    sales_yoy_table=sales_yoy_table,
                    payouts_pre_post_table=payouts_pre_post_table,
                    payouts_yoy_table=payouts_yoy_table
                )
                st.success(f"✅ **Export successful!** Downloading file...")
                st.download_button(
                    label="📥 Download Excel File",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
        except Exception as e:
            st.error(f"❌ **Export failed!** Error: {str(e)}")
            import traceback
            with st.expander("🔍 View Error Details"):
                st.code(traceback.format_exc())
    
    # 1. Combined Store-Level Tables
    st.header("🔗 Combined Store-Level Analysis (DoorDash + UberEats)")
    st.caption("💡 Values are summed for stores that appear in both platforms")
    if combined_store_table1 is not None and not combined_store_table1.empty:
        st.subheader("Combined Table 1: Current Year Pre vs Post Analysis (Store-Level)")
        combined_store1_display = combined_store_table1.reset_index() if combined_store_table1.index.name == 'Store ID' else combined_store_table1.copy()
        # Filter out rows with no data (both Pre and Post are 0 or NaN) or empty Store ID
        if 'Pre' in combined_store1_display.columns and 'Post' in combined_store1_display.columns:
            combined_store1_display = combined_store1_display[
                (combined_store1_display['Store ID'].notna() if 'Store ID' in combined_store1_display.columns else True) &
                (combined_store1_display['Store ID'] != '' if 'Store ID' in combined_store1_display.columns else True) &
                ((combined_store1_display['Pre'].fillna(0) != 0) | (combined_store1_display['Post'].fillna(0) != 0))
            ].copy()  # Use .copy() to ensure we have a clean dataframe
        # Only display if there's data after filtering
        if not combined_store1_display.empty and 'Pre' in combined_store1_display.columns:
            # Reset index to ensure clean row numbers
            if 'Store ID' in combined_store1_display.columns:
                combined_store1_display = combined_store1_display.reset_index(drop=True)
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
        
        # Filter out rows with no data (both last year-post and post are 0 or NaN) or empty Store ID
        if 'last year-post' in combined_store2_display.columns and 'post' in combined_store2_display.columns:
            combined_store2_display = combined_store2_display[
                (combined_store2_display['Store ID'].notna() if 'Store ID' in combined_store2_display.columns else True) &
                (combined_store2_display['Store ID'] != '' if 'Store ID' in combined_store2_display.columns else True) &
                ((combined_store2_display['last year-post'].fillna(0) != 0) | (combined_store2_display['post'].fillna(0) != 0))
            ].copy()  # Use .copy() to ensure we have a clean dataframe
        
        # Only display if there's data after filtering
        if not combined_store2_display.empty:
            # Reset index to ensure clean row numbers
            combined_store2_display = combined_store2_display.reset_index(drop=True) if 'Store ID' in combined_store2_display.columns else combined_store2_display
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
        elif metric == 'Profitability':
            # Profitability: format as percentage
            combined_summary1_display.loc[idx, 'Pre'] = f"{combined_summary1.loc[idx, 'Pre']:.1f}%"
            combined_summary1_display.loc[idx, 'Post'] = f"{combined_summary1.loc[idx, 'Post']:.1f}%"
            combined_summary1_display.loc[idx, 'PrevsPost'] = f"{combined_summary1.loc[idx, 'PrevsPost']:.1f}%"
            combined_summary1_display.loc[idx, 'LastYear Pre vs Post'] = f"{combined_summary1.loc[idx, 'LastYear Pre vs Post']:.1f}%"
        elif metric == 'AOV':
            # AOV: format as dollars
            combined_summary1_display.loc[idx, 'Pre'] = f"${combined_summary1.loc[idx, 'Pre']:,.1f}"
            combined_summary1_display.loc[idx, 'Post'] = f"${combined_summary1.loc[idx, 'Post']:,.1f}"
            combined_summary1_display.loc[idx, 'PrevsPost'] = f"${combined_summary1.loc[idx, 'PrevsPost']:,.1f}"
            combined_summary1_display.loc[idx, 'LastYear Pre vs Post'] = f"${combined_summary1.loc[idx, 'LastYear Pre vs Post']:,.1f}"
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
        elif metric == 'Profitability':
            # Profitability: format as percentage
            combined_summary2_display.loc[idx, 'last year-post'] = f"{combined_summary2.loc[idx, 'last year-post']:.1f}%"
            combined_summary2_display.loc[idx, 'post'] = f"{combined_summary2.loc[idx, 'post']:.1f}%"
            combined_summary2_display.loc[idx, 'YoY'] = f"{combined_summary2.loc[idx, 'YoY']:.1f}%"
        elif metric == 'AOV':
            # AOV: format as dollars
            combined_summary2_display.loc[idx, 'last year-post'] = f"${combined_summary2.loc[idx, 'last year-post']:,.1f}"
            combined_summary2_display.loc[idx, 'post'] = f"${combined_summary2.loc[idx, 'post']:,.1f}"
            combined_summary2_display.loc[idx, 'YoY'] = f"${combined_summary2.loc[idx, 'YoY']:,.1f}"
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
        corporate_display.index.name = 'Campaign'
        corporate_display = corporate_display.reset_index()
        corporate_display['Campaign'] = corporate_display['Campaign'].apply(
            lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
        )
        corporate_display = corporate_display.set_index('Campaign')
        
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
                promo_display.index.name = 'Campaign'
                promo_display = promo_display.reset_index()
                promo_display['Campaign'] = promo_display['Campaign'].apply(
                    lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
                )
                promo_display = promo_display.set_index('Campaign')
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
                sponsored_display.index.name = 'Campaign'
                sponsored_display = sponsored_display.reset_index()
                sponsored_display['Campaign'] = sponsored_display['Campaign'].apply(
                    lambda x: 'Corporate' if x == False else ('TODC' if x == True else str(x))
                )
                sponsored_display = sponsored_display.set_index('Campaign')
                st.dataframe(sponsored_display, width='stretch')
            else:
                st.info("No sponsored listing data available")
    else:
        st.info("No marketing data available. Please ensure marketing_* folders exist with MARKETING_PROMOTION and MARKETING_SPONSORED_LISTING files.")
    
    st.divider()
    
    # 8. Slot-based Analysis Tables
    st.header("⏰ Slot-based Analysis")
    
    # Slot tables are already processed above for export, now just display them
    if sales_pre_post_table is not None and sales_yoy_table is not None and payouts_pre_post_table is not None and payouts_yoy_table is not None:
        # Display Table 1: Sales Pre/Post
        st.subheader("Table 1: Sales - Pre vs Post")
        sales_pre_post_display = sales_pre_post_table.copy()
        sales_pre_post_display['Pre'] = sales_pre_post_display['Pre'].apply(lambda x: f"${x:,.2f}")
        sales_pre_post_display['Post'] = sales_pre_post_display['Post'].apply(lambda x: f"${x:,.2f}")
        sales_pre_post_display['Pre vs Post'] = sales_pre_post_display['Pre vs Post'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(sales_pre_post_display, use_container_width=True, hide_index=True)
        
        # Display Table 2: Sales YoY
        st.subheader("Table 2: Sales - Year over Year")
        sales_yoy_display = sales_yoy_table.copy()
        sales_yoy_display['Last year post'] = sales_yoy_display['Last year post'].apply(lambda x: f"${x:,.2f}")
        sales_yoy_display['Post'] = sales_yoy_display['Post'].apply(lambda x: f"${x:,.2f}")
        sales_yoy_display['YoY'] = sales_yoy_display['YoY'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(sales_yoy_display, use_container_width=True, hide_index=True)
        
        # Display Table 3: Payouts Pre/Post
        st.subheader("Table 3: Payouts - Pre vs Post")
        payouts_pre_post_display = payouts_pre_post_table.copy()
        payouts_pre_post_display['Pre'] = payouts_pre_post_display['Pre'].apply(lambda x: f"${x:,.2f}")
        payouts_pre_post_display['Post'] = payouts_pre_post_display['Post'].apply(lambda x: f"${x:,.2f}")
        payouts_pre_post_display['Pre vs Post'] = payouts_pre_post_display['Pre vs Post'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(payouts_pre_post_display, use_container_width=True, hide_index=True)
        
        # Display Table 4: Payouts YoY
        st.subheader("Table 4: Payouts - Year over Year")
        payouts_yoy_display = payouts_yoy_table.copy()
        payouts_yoy_display['Last year post'] = payouts_yoy_display['Last year post'].apply(lambda x: f"${x:,.2f}")
        payouts_yoy_display['Post'] = payouts_yoy_display['Post'].apply(lambda x: f"${x:,.2f}")
        payouts_yoy_display['YoY'] = payouts_yoy_display['YoY'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(payouts_yoy_display, use_container_width=True, hide_index=True)
    else:
        st.info("DoorDash financial file not available for slot-based analysis.")

if __name__ == "__main__":
    main()

