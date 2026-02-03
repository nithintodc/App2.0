"""Slot-based analysis functions for DoorDash data"""
import pandas as pd
import streamlit as st
from pathlib import Path
from utils import filter_master_file_by_date_range, filter_excluded_dates
from data_processing import get_last_year_dates


def get_time_slot(time_str):
    """
    Categorize a time string into a slot.
    
    Slot values:
    - Early morning: 12:00 AM – 4:59 AM
    - Breakfast: 5:00 AM – 10:59 AM
    - Lunch: 11:00 AM – 1:59 PM
    - Afternoon: 2:00 PM – 4:59 PM
    - Dinner: 5:00 PM – 7:59 PM
    - Late night: 8:00 PM – 11:59 PM
    """
    try:
        # Parse time string (format: YYYY-MM-DD HH:MM:SS or similar)
        if pd.isna(time_str) or time_str == '':
            return None
        
        # Try to parse as datetime
        time_obj = pd.to_datetime(time_str, errors='coerce')
        if pd.isna(time_obj):
            return None
        
        hour = time_obj.hour
        minute = time_obj.minute
        
        # Convert to minutes since midnight for easier comparison
        total_minutes = hour * 60 + minute
        
        # Define slot boundaries (in minutes since midnight)
        if total_minutes >= 0 and total_minutes < 300:  # 12:00 AM - 4:59 AM
            return 'Early morning'
        elif total_minutes >= 300 and total_minutes < 659:  # 5:00 AM - 10:59 AM
            return 'Breakfast'
        elif total_minutes >= 659 and total_minutes < 839:  # 11:00 AM - 1:59 PM
            return 'Lunch'
        elif total_minutes >= 839 and total_minutes < 959:  # 2:00 PM - 4:59 PM
            return 'Afternoon'
        elif total_minutes >= 959 and total_minutes < 1159:  # 5:00 PM - 7:59 PM
            return 'Dinner'
        elif total_minutes >= 1159:  # 8:00 PM - 11:59 PM
            return 'Late night'
        else:
            return None
    except Exception as e:
        return None


def process_slot_analysis(file_path, pre_start_date, pre_end_date, post_start_date, post_end_date, excluded_dates=None):
    """
    Process DoorDash financial file and create slot-based analysis tables.
    
    Returns:
        Tuple of (sales_pre_post_table, sales_yoy_table, payouts_pre_post_table, payouts_yoy_table)
        
    Table 1 (Sales Pre/Post): Slots as rows, columns: Pre, Post, Pre vs Post, Growth%
    Table 2 (Sales YoY): Slots as rows, columns: Last year post, Post, YoY, Growth%
    Table 3 (Payouts Pre/Post): Same as Table 1 for Payouts
    Table 4 (Payouts YoY): Same as Table 2 for Payouts
    """
    try:
        # Define slot order
        slot_order = ['Early morning', 'Breakfast', 'Lunch', 'Afternoon', 'Dinner', 'Late night']
        
        # Load and process Pre period data
        date_col_variations = ['Timestamp local date', 'Timestamp Local Date', 'Timestamp Local date', 
                              'timestamp local date', 'Date', 'date', 'Timestamp', 'timestamp']
        
        pre_df = filter_master_file_by_date_range(file_path, pre_start_date, pre_end_date, date_col_variations, excluded_dates)
        post_df = filter_master_file_by_date_range(file_path, post_start_date, post_end_date, date_col_variations, excluded_dates)
        
        # Calculate last year's post dates for YoY analysis
        post_24_start, post_24_end = get_last_year_dates(post_start_date, post_end_date)
        post_24_df = filter_master_file_by_date_range(file_path, post_24_start, post_24_end, date_col_variations, excluded_dates)
        
        # Check for required columns
        time_col = 'Timestamp local time'
        if time_col not in pre_df.columns and not pre_df.empty:
            # Try variations
            time_col_variations = ['Timestamp local time', 'Timestamp Local Time', 'timestamp local time', 
                                  'Order received local time', 'Order Received Local Time']
            time_col = None
            for col in time_col_variations:
                if col in pre_df.columns:
                    time_col = col
                    break
            
            if time_col is None:
                st.error(f"Time column not found. Available columns: {list(pre_df.columns)[:10]}")
                empty_table = pd.DataFrame({
                    'Slot': slot_order,
                    'Pre': [0.0] * len(slot_order),
                    'Post': [0.0] * len(slot_order),
                    'Pre vs Post': [0.0] * len(slot_order),
                    'Growth%': ['0.0%'] * len(slot_order)
                })
                return empty_table, empty_table.copy(), empty_table.copy(), empty_table.copy()
        
        sales_col = 'Subtotal'
        payout_col = None
        if not pre_df.empty:
            if 'Net total' in pre_df.columns:
                payout_col = 'Net total'
            elif 'Net total (for historical reference only)' in pre_df.columns:
                payout_col = 'Net total (for historical reference only)'
        
        if (pre_df.empty and post_df.empty) or (sales_col not in pre_df.columns if not pre_df.empty else False) or payout_col is None:
            empty_table = pd.DataFrame({
                'Slot': slot_order,
                'Pre': [0.0] * len(slot_order),
                'Post': [0.0] * len(slot_order),
                'Pre vs Post': [0.0] * len(slot_order),
                'Growth%': ['0.0%'] * len(slot_order)
            })
            return empty_table, empty_table.copy(), empty_table.copy(), empty_table.copy()
        
        # Process Pre period
        pre_slot_sales = {}
        pre_slot_payouts = {}
        if not pre_df.empty:
            pre_df = pre_df.copy()
            pre_df['Slot'] = pre_df[time_col].apply(get_time_slot)
            pre_df = pre_df.dropna(subset=['Slot'])
            pre_df[sales_col] = pd.to_numeric(pre_df[sales_col], errors='coerce')
            pre_df[payout_col] = pd.to_numeric(pre_df[payout_col], errors='coerce')
            
            pre_slot_agg = pre_df.groupby('Slot').agg({
                sales_col: 'sum',
                payout_col: 'sum'
            }).reset_index()
            
            for slot in slot_order:
                slot_data = pre_slot_agg[pre_slot_agg['Slot'] == slot]
                pre_slot_sales[slot] = slot_data[sales_col].sum() if len(slot_data) > 0 else 0.0
                pre_slot_payouts[slot] = slot_data[payout_col].sum() if len(slot_data) > 0 else 0.0
        else:
            pre_slot_sales = {slot: 0.0 for slot in slot_order}
            pre_slot_payouts = {slot: 0.0 for slot in slot_order}
        
        # Process Post period
        post_slot_sales = {}
        post_slot_payouts = {}
        if not post_df.empty:
            post_df = post_df.copy()
            post_df['Slot'] = post_df[time_col].apply(get_time_slot)
            post_df = post_df.dropna(subset=['Slot'])
            post_df[sales_col] = pd.to_numeric(post_df[sales_col], errors='coerce')
            post_df[payout_col] = pd.to_numeric(post_df[payout_col], errors='coerce')
            
            post_slot_agg = post_df.groupby('Slot').agg({
                sales_col: 'sum',
                payout_col: 'sum'
            }).reset_index()
            
            for slot in slot_order:
                slot_data = post_slot_agg[post_slot_agg['Slot'] == slot]
                post_slot_sales[slot] = slot_data[sales_col].sum() if len(slot_data) > 0 else 0.0
                post_slot_payouts[slot] = slot_data[payout_col].sum() if len(slot_data) > 0 else 0.0
        else:
            post_slot_sales = {slot: 0.0 for slot in slot_order}
            post_slot_payouts = {slot: 0.0 for slot in slot_order}
        
        # Process Last Year Post period (post_24)
        post_24_slot_sales = {}
        post_24_slot_payouts = {}
        if not post_24_df.empty:
            post_24_df = post_24_df.copy()
            post_24_df['Slot'] = post_24_df[time_col].apply(get_time_slot)
            post_24_df = post_24_df.dropna(subset=['Slot'])
            post_24_df[sales_col] = pd.to_numeric(post_24_df[sales_col], errors='coerce')
            post_24_df[payout_col] = pd.to_numeric(post_24_df[payout_col], errors='coerce')
            
            post_24_slot_agg = post_24_df.groupby('Slot').agg({
                sales_col: 'sum',
                payout_col: 'sum'
            }).reset_index()
            
            for slot in slot_order:
                slot_data = post_24_slot_agg[post_24_slot_agg['Slot'] == slot]
                post_24_slot_sales[slot] = slot_data[sales_col].sum() if len(slot_data) > 0 else 0.0
                post_24_slot_payouts[slot] = slot_data[payout_col].sum() if len(slot_data) > 0 else 0.0
        else:
            post_24_slot_sales = {slot: 0.0 for slot in slot_order}
            post_24_slot_payouts = {slot: 0.0 for slot in slot_order}
        
        # Create Table 1: Sales Pre/Post (Pre, Post, Pre vs Post, Growth%)
        sales_pre_post_data = []
        for slot in slot_order:
            pre_val = pre_slot_sales[slot]
            post_val = post_slot_sales[slot]
            pre_vs_post = post_val - pre_val
            growth_pct = f"{((post_val - pre_val) / pre_val * 100):.1f}%" if pre_val != 0 else "0.0%"
            
            sales_pre_post_data.append({
                'Slot': slot,
                'Pre': pre_val,
                'Post': post_val,
                'Pre vs Post': pre_vs_post,
                'Growth%': growth_pct
            })
        sales_pre_post_table = pd.DataFrame(sales_pre_post_data)
        
        # Create Table 2: Sales YoY (Last year post, Post, YoY, Growth%)
        sales_yoy_data = []
        for slot in slot_order:
            last_year_post = post_24_slot_sales[slot]
            post_val = post_slot_sales[slot]
            yoy = post_val - last_year_post
            growth_pct = f"{((post_val - last_year_post) / last_year_post * 100):.1f}%" if last_year_post != 0 else "0.0%"
            
            sales_yoy_data.append({
                'Slot': slot,
                'Last year post': last_year_post,
                'Post': post_val,
                'YoY': yoy,
                'Growth%': growth_pct
            })
        sales_yoy_table = pd.DataFrame(sales_yoy_data)
        
        # Create Table 3: Payouts Pre/Post (Pre, Post, Pre vs Post, Growth%)
        payouts_pre_post_data = []
        for slot in slot_order:
            pre_val = pre_slot_payouts[slot]
            post_val = post_slot_payouts[slot]
            pre_vs_post = post_val - pre_val
            growth_pct = f"{((post_val - pre_val) / pre_val * 100):.1f}%" if pre_val != 0 else "0.0%"
            
            payouts_pre_post_data.append({
                'Slot': slot,
                'Pre': pre_val,
                'Post': post_val,
                'Pre vs Post': pre_vs_post,
                'Growth%': growth_pct
            })
        payouts_pre_post_table = pd.DataFrame(payouts_pre_post_data)
        
        # Create Table 4: Payouts YoY (Last year post, Post, YoY, Growth%)
        payouts_yoy_data = []
        for slot in slot_order:
            last_year_post = post_24_slot_payouts[slot]
            post_val = post_slot_payouts[slot]
            yoy = post_val - last_year_post
            growth_pct = f"{((post_val - last_year_post) / last_year_post * 100):.1f}%" if last_year_post != 0 else "0.0%"
            
            payouts_yoy_data.append({
                'Slot': slot,
                'Last year post': last_year_post,
                'Post': post_val,
                'YoY': yoy,
                'Growth%': growth_pct
            })
        payouts_yoy_table = pd.DataFrame(payouts_yoy_data)
        
        return sales_pre_post_table, sales_yoy_table, payouts_pre_post_table, payouts_yoy_table
        
    except Exception as e:
        st.error(f"Error processing slot analysis: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        slot_order = ['Early morning', 'Breakfast', 'Lunch', 'Afternoon', 'Dinner', 'Late night']
        empty_table = pd.DataFrame({
            'Slot': slot_order,
            'Pre': [0.0] * len(slot_order),
            'Post': [0.0] * len(slot_order),
            'Pre vs Post': [0.0] * len(slot_order),
            'Growth%': ['0.0%'] * len(slot_order)
        })
        return empty_table, empty_table.copy(), empty_table.copy(), empty_table.copy()
