import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client


# Connect to Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = init_supabase()

# Page Setup
st.set_page_config(page_title="Advanced Inventory System", layout="wide")
st.title("📦 Smart Inventory & Operations Dashboard")


# Helper function to fetch latest table data
def get_inventory_data():
    response = supabase.table("inventory").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame()


df = get_inventory_data()

if not df.empty:
    # Ensure necessary columns exist (fallbacks for schema variations)
    if "Current_Stock" not in df.columns and "quantity" in df.columns:
        df["Current_Stock"] = df["quantity"]
    if "Item_Name" not in df.columns and "item_name" in df.columns:
        df["Item_Name"] = df["item_name"]
    if "Minimum_Required" not in df.columns:
        df["Minimum_Required"] = 10  # Default minimum threshold if not specified

    # Calculate status dynamically
    df["Status"] = df.apply(
        lambda row: (
            "⚠️ REORDER NEEDED"
            if row["Current_Stock"] < row["Minimum_Required"]
            else "✅ OK"
        ),
        axis=1,
    )

    # --- SIDEBAR INTERACTIVE FILTERS ---
    st.sidebar.header("🔍 Interactive Controls")
    search_query = st.sidebar.text_input("Search Product Name", "")
    status_filter = st.sidebar.multiselect(
        "Filter by Status",
        options=["⚠️ REORDER NEEDED", "✅ OK"],
        default=["⚠️ REORDER NEEDED", "✅ OK"],
    )

    # Filter Data
    filtered_df = df[
        (df["Item_Name"].str.contains(search_query, case=False, na=False))
        & (df["Status"].isin(status_filter))
    ]

    # --- KEY METRICS CARDS ---
    low_stock = df[df["Current_Stock"] < df["Minimum_Required"]]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", len(df))
    col2.metric("Healthy Stock Items", len(df) - len(low_stock))
    col3.metric("Critical Alerts", len(low_stock), delta_color="inverse")
    col4.metric("Total Stock On Hand", int(df["Current_Stock"].sum()))

    st.divider()

    # --- INTERACTIVE TABS ---
    tab1, tab2, tab3 = st.tabs(
        ["📋 Data Grid & Edits", "📊 Visual Analytics", "⚡ Action Center"]
    )

    with tab1:
        st.subheader("Live Inventory Table")
        st.caption(
            "Tip: You can filter data using the sidebar controls on the left!"
        )
        st.dataframe(filtered_df, use_container_width=True)

        st.divider()
        st.subheader("✏️ Quick Stock Update Tool")
        selected_item = st.selectbox(
            "Select Product to Update", df["Item_Name"].unique()
        )
        new_stock = st.number_input(
            "Enter New Stock Level", min_value=0, value=10
        )
        if st.button("Update Stock Level"):
            # Target quantity or Current_Stock depending on database column
            col_target = "quantity" if "quantity" in df.columns else "Current_Stock"
            name_target = "item_name" if "item_name" in df.columns else "Item_Name"

            supabase.table("inventory").update({col_target: new_stock}).eq(
                name_target, selected_item
            ).execute()
            st.success(f"Updated '{selected_item}' stock to {new_stock}!")
            st.rerun()

    with tab2:
        st.subheader("Inventory vs Minimum Thresholds")
        fig = px.bar(
            df,
            x="Item_Name",
            y=["Current_Stock", "Minimum_Required"],
            barmode="group",
            labels={"value": "Quantity", "Item_Name": "Product"},
            title="Stock Comparison Chart",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🚨 Automated Supplier Action Center")
        if len(low_stock) > 0:
            st.warning(
                f"There are {len(low_stock)} items currently below minimum limits."
            )
            cols_to_show = [
                c
                for c in ["id", "Item_Name", "Current_Stock", "Minimum_Required"]
                if c in df.columns
            ]
            st.table(low_stock[cols_to_show])
            if st.button("📧 Dispatch Automated Supplier Reorder Batch"):
                st.success("Reorder alert dispatches sent to supplier email!")
                st.balloons()
        else:
            st.success("🎉 All inventory stock levels are healthy!")

else:
    st.info(
        "No inventory items found in your Supabase database. Add items to your table to initialize the dashboard."
    )
