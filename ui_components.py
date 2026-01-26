"""UI components for displaying tables and store selectors"""
import pandas as pd
import streamlit as st
from table_generation import create_summary_tables


def create_store_selector(platform_name, df, platform_key):
    """Create store selection UI for a platform"""
    with st.expander(f"🔍 {platform_name} Store Selection", expanded=True):
        # Check if dataframe is empty
        if df.empty:
            st.warning(f"⚠️ No {platform_name} data available. Please set Pre and Post date ranges in the sidebar to load stores.")
            st.info(f"**0** stores selected out of **0** total")
            return
        
        # Get all unique store IDs
        if 'Store ID' not in df.columns:
            st.error(f"⚠️ 'Store ID' column not found in {platform_name} data.")
            st.info(f"**0** stores selected out of **0** total")
            return
            
        all_stores = sorted(df['Store ID'].unique().tolist())
        
        if not all_stores:
            st.warning(f"⚠️ No stores found in {platform_name} data. Please check your date ranges and data files.")
            st.info(f"**0** stores selected out of **0** total")
            return
        
        # Initialize session state for selected stores (platform-specific)
        if platform_key not in st.session_state or not st.session_state[platform_key]:
            st.session_state[platform_key] = all_stores.copy()
        
        # Select all / Deselect all buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select All", key=f"select_all_{platform_name}"):
                st.session_state[platform_key] = all_stores.copy()
                st.rerun()
        with col2:
            if st.button("Deselect All", key=f"deselect_all_{platform_name}"):
                st.session_state[platform_key] = []
                st.rerun()
        
        # Multi-select for stores
        selected_stores = st.multiselect(
            f"Choose {platform_name} stores to analyze:",
            options=all_stores,
            default=st.session_state[platform_key],
            key=f"store_selector_{platform_name}"
        )
        
        # Apply button
        if st.button("Apply Selection", type="primary", key=f"apply_{platform_name}"):
            st.session_state[platform_key] = selected_stores
            st.rerun()
        
        # Show selection info
        st.info(f"**{len(st.session_state[platform_key])}** stores selected out of **{len(all_stores)}** total")


def display_store_tables(platform_name, table1_df, table2_df):
    """Display store-level tables"""
    if table1_df is None:
        st.warning(f"No {platform_name} stores selected.")
        return
    
    st.subheader(f"Table 1: Current Year Pre vs Post Analysis")
    table1_display = table1_df.copy()
    # Filter out rows with no data (both Pre and Post are 0 or NaN)
    if 'Pre' in table1_display.columns and 'Post' in table1_display.columns:
        table1_display = table1_display[
            (table1_display['Pre'].fillna(0) != 0) | (table1_display['Post'].fillna(0) != 0)
        ]
    
    if not table1_display.empty:
        table1_display['Pre'] = table1_display['Pre'].apply(lambda x: f"${x:,.1f}")
        table1_display['Post'] = table1_display['Post'].apply(lambda x: f"${x:,.1f}")
        table1_display['PrevsPost'] = table1_display['PrevsPost'].apply(lambda x: f"${x:,.1f}")
        table1_display['LastYear Pre vs Post'] = table1_display['LastYear Pre vs Post'].apply(lambda x: f"${x:,.1f}")
        table1_display['Growth%'] = table1_display['Growth%'].apply(lambda x: f"{x:.1f}%")
        table1_display = table1_display.set_index('Store ID')
        st.dataframe(table1_display, use_container_width=True, height=400)
    else:
        st.info("No data available for Table 1")
    
    # Table 2 (YoY) - Display similar to Summary Analysis
    if table2_df is not None and not table2_df.empty:
        st.subheader(f"Table 2: Year-over-Year Analysis")
        table2_display = table2_df.copy()
        
        # Filter out rows with no data (both last year-post and post are 0 or NaN)
        if 'last year-post' in table2_display.columns and 'post' in table2_display.columns:
            table2_display = table2_display[
                (table2_display['last year-post'].fillna(0) != 0) | (table2_display['post'].fillna(0) != 0)
            ]
        
        if not table2_display.empty:
            # Format dollar columns
            if 'last year-post' in table2_display.columns:
                table2_display['last year-post'] = table2_display['last year-post'].apply(lambda x: f"${x:,.1f}")
            if 'post' in table2_display.columns:
                table2_display['post'] = table2_display['post'].apply(lambda x: f"${x:,.1f}")
            if 'YoY' in table2_display.columns:
                table2_display['YoY'] = table2_display['YoY'].apply(lambda x: f"${x:,.1f}")
            # Format percentage column
            if 'YoY%' in table2_display.columns:
                table2_display['YoY%'] = table2_display['YoY%'].apply(lambda x: f"{x:.1f}%")
            
            if 'Store ID' in table2_display.columns:
                table2_display = table2_display.set_index('Store ID')
            st.dataframe(table2_display, use_container_width=True, height=400)
        else:
            st.info("No data available for Table 2")
    else:
        st.info("No YoY data available for Table 2")


def display_summary_tables(platform_name, summary_table1, summary_table2):
    """Display summary tables"""
    st.write(f"**{platform_name} Table 1: Current Year Pre vs Post Analysis**")
    summary_table1_display = summary_table1.copy()
    # Convert columns to object type to avoid dtype warnings when assigning formatted strings
    for col in summary_table1_display.columns:
        summary_table1_display[col] = summary_table1_display[col].astype(object)
    
    # Format columns based on metric type
    for idx in summary_table1_display.index:
        metric = idx
        if metric == 'Orders' or metric == 'New Customers':
            # Orders: format as integer string
            summary_table1_display.loc[idx, 'Pre'] = f"{int(round(summary_table1.loc[idx, 'Pre'])):,}"
            summary_table1_display.loc[idx, 'Post'] = f"{int(round(summary_table1.loc[idx, 'Post'])):,}"
            summary_table1_display.loc[idx, 'PrevsPost'] = f"{int(round(summary_table1.loc[idx, 'PrevsPost'])):,}"
            summary_table1_display.loc[idx, 'LastYear Pre vs Post'] = f"{int(round(summary_table1.loc[idx, 'LastYear Pre vs Post'])):,}"
        else:
            # Sales/Payouts: format as dollars
            summary_table1_display.loc[idx, 'Pre'] = f"${summary_table1.loc[idx, 'Pre']:,.1f}"
            summary_table1_display.loc[idx, 'Post'] = f"${summary_table1.loc[idx, 'Post']:,.1f}"
            summary_table1_display.loc[idx, 'PrevsPost'] = f"${summary_table1.loc[idx, 'PrevsPost']:,.1f}"
            summary_table1_display.loc[idx, 'LastYear Pre vs Post'] = f"${summary_table1.loc[idx, 'LastYear Pre vs Post']:,.1f}"
        # Growth% is always a percentage
        summary_table1_display.loc[idx, 'Growth%'] = f"{summary_table1.loc[idx, 'Growth%']:.1f}%"
    
    # Ensure all columns are string type for Arrow compatibility
    for col in summary_table1_display.columns:
        summary_table1_display[col] = summary_table1_display[col].astype(str)
    
    st.dataframe(summary_table1_display, use_container_width=True)
    
    st.write(f"**{platform_name} Table 2: Year-over-Year Analysis**")
    summary_table2_display = summary_table2.copy()
    # Convert columns to object type to avoid dtype warnings when assigning formatted strings
    for col in summary_table2_display.columns:
        summary_table2_display[col] = summary_table2_display[col].astype(object)
    
    # Format columns based on metric type
    for idx in summary_table2_display.index:
        metric = idx
        if metric == 'Orders' or metric == 'New Customers':
            # Orders: format as integer string
            summary_table2_display.loc[idx, 'last year-post'] = f"{int(round(summary_table2.loc[idx, 'last year-post'])):,}"
            summary_table2_display.loc[idx, 'post'] = f"{int(round(summary_table2.loc[idx, 'post'])):,}"
            summary_table2_display.loc[idx, 'YoY'] = f"{int(round(summary_table2.loc[idx, 'YoY'])):,}"
        else:
            # Sales/Payouts: format as dollars
            summary_table2_display.loc[idx, 'last year-post'] = f"${summary_table2.loc[idx, 'last year-post']:,.1f}"
            summary_table2_display.loc[idx, 'post'] = f"${summary_table2.loc[idx, 'post']:,.1f}"
            summary_table2_display.loc[idx, 'YoY'] = f"${summary_table2.loc[idx, 'YoY']:,.1f}"
        # YoY% is always a percentage
        summary_table2_display.loc[idx, 'YoY%'] = f"{summary_table2.loc[idx, 'YoY%']:.1f}%"
    
    # Ensure all columns are string type for Arrow compatibility
    for col in summary_table2_display.columns:
        summary_table2_display[col] = summary_table2_display[col].astype(str)
    
    st.dataframe(summary_table2_display, use_container_width=True)


def display_platform_data(platform_name, sales_df, payouts_df, sales_label, platform_key):
    """Display analysis tables for a platform"""
    # Get selected stores from session state, default to all stores if not set
    selected_stores = st.session_state.get(platform_key, sorted(sales_df['Store ID'].unique().tolist()))
    
    # Filter data based on selected stores
    filtered_sales_df = sales_df[sales_df['Store ID'].isin(selected_stores)].copy()
    filtered_payouts_df = payouts_df[payouts_df['Store ID'].isin(selected_stores)].copy()
    
    if filtered_sales_df.empty:
        st.warning(f"No {platform_name} stores selected. Please select at least one store from the sidebar.")
        return None, None
    
    # Display the analysis tables
    st.header(f"📈 {platform_name} Performance Analysis")
    st.caption(f"💡 All values represent aggregated sums of **{sales_label}** by Store ID")
    
    # Summary Tables (above store-level)
    st.subheader("📊 Summary Tables (Aggregated Across Selected Stores)")
    summary_table1, summary_table2 = create_summary_tables(sales_df, payouts_df, selected_stores)
    
    # Format and display Summary Table 1
    summary_table1_display = summary_table1.copy()
    summary_table1_display['Pre'] = summary_table1_display['Pre'].apply(lambda x: f"${x:,.1f}")
    summary_table1_display['Post'] = summary_table1_display['Post'].apply(lambda x: f"${x:,.1f}")
    summary_table1_display['PrevsPost'] = summary_table1_display['PrevsPost'].apply(lambda x: f"${x:,.1f}")
    summary_table1_display['LastYear Pre vs Post'] = summary_table1_display['LastYear Pre vs Post'].apply(lambda x: f"${x:,.1f}")
    summary_table1_display['Growth%'] = summary_table1_display['Growth%'].apply(lambda x: f"{x:.1f}%")
    
    st.write("**Table 1: Current Year Pre vs Post Analysis**")
    st.dataframe(summary_table1_display, use_container_width=True)
    
    # Format and display Summary Table 2
    summary_table2_display = summary_table2.copy()
    summary_table2_display['last year-post'] = summary_table2_display['last year-post'].apply(lambda x: f"${x:,.1f}")
    summary_table2_display['post'] = summary_table2_display['post'].apply(lambda x: f"${x:,.1f}")
    summary_table2_display['YoY'] = summary_table2_display['YoY'].apply(lambda x: f"${x:,.1f}")
    summary_table2_display['YoY%'] = summary_table2_display['YoY%'].apply(lambda x: f"{x:.1f}%")
    
    st.write("**Table 2: Year-over-Year Analysis**")
    st.dataframe(summary_table2_display, use_container_width=True)
    
    st.divider()
    st.subheader("🏪 Store-Level Analysis")
    
    # First Table: Store ID, Pre, Post, PrevsPost, LastYear Pre vs Post, Growth%
    st.subheader("Table 1: Current Year Pre vs Post Analysis")
    # Create table for CSV (keep numeric values)
    table1_df = filtered_sales_df[['Store ID', 'pre_25', 'post_25', 'PrevsPost', 'LastYear_Pre_vs_Post', 'Growth%']].copy()
    table1_df = table1_df.rename(columns={
        'pre_25': 'Pre',
        'post_25': 'Post',
        'PrevsPost': 'PrevsPost',
        'LastYear_Pre_vs_Post': 'LastYear Pre vs Post',
        'Growth%': 'Growth%'
    })
    # Create display version with dollar and % formatting
    table1_display = table1_df.copy()
    # Format dollar columns
    table1_display['Pre'] = table1_display['Pre'].apply(lambda x: f"${x:,.1f}")
    table1_display['Post'] = table1_display['Post'].apply(lambda x: f"${x:,.1f}")
    table1_display['PrevsPost'] = table1_display['PrevsPost'].apply(lambda x: f"${x:,.1f}")
    table1_display['LastYear Pre vs Post'] = table1_display['LastYear Pre vs Post'].apply(lambda x: f"${x:,.1f}")
    # Format percentage column
    table1_display['Growth%'] = table1_display['Growth%'].apply(lambda x: f"{x:.1f}%")
    table1_display = table1_display.set_index('Store ID')
    st.dataframe(
        table1_display,
        use_container_width=True,
        height=400
    )
    
    # Second Table: Store ID, last year-post, post, YoY, YoY%
    st.subheader("Table 2: Year-over-Year Analysis")
    # Create table for CSV (keep numeric values)
    table2_df = filtered_sales_df[['Store ID', 'post_24', 'post_25', 'YoY', 'YoY%']].copy()
    table2_df = table2_df.rename(columns={
        'post_24': 'last year-post',
        'post_25': 'post',
        'YoY': 'YoY',
        'YoY%': 'YoY%'
    })
    # Create display version with dollar and % formatting
    table2_display = table2_df.copy()
    # Format dollar columns
    table2_display['last year-post'] = table2_display['last year-post'].apply(lambda x: f"${x:,.1f}")
    table2_display['post'] = table2_display['post'].apply(lambda x: f"${x:,.1f}")
    table2_display['YoY'] = table2_display['YoY'].apply(lambda x: f"${x:,.1f}")
    # Format percentage column
    table2_display['YoY%'] = table2_display['YoY%'].apply(lambda x: f"{x:.1f}%")
    table2_display = table2_display.set_index('Store ID')
    st.dataframe(
        table2_display,
        use_container_width=True,
        height=400
    )
    
    return table1_df, table2_df
