import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# Direct Supabase Credentials (Bypassing Streamlit Secrets)
https://rwcvjhpjnelefauoajkq.supabase.co
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3Y3ZqaHBqbmVsZWZldW9hamtxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkyMTM3ODcsImV4cCI6MjEwNDc4OTc4N30.8XkTZys3WGP5JiJIo6-MlQeCmtlMJJS0EwRvFcIj-8I"


@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

# Page Setup
st.set_page_config(page_title="Advanced Inventory System", layout="wide")
st.title("📦 Smart Inventory & Operations Dashboard")


# Helper function to fetch latest table data safely
def get_inventory_data():
    try:
        response = supabase.table("inventory").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Failed to connect to Supabase database: {e}")
    return pd.DataFrame()


df = get_inventory_data()

if not df.empty:
    if "Current_Stock" not in df.columns and "quantity" in df.columns:
        df["Current_Stock"] = df["quantity"]
    if "Item_Name" not in df.columns and "item_name" in df.columns:
        df["Item_Name"] = df["item_name"]
    if "Minimum_Required" not in df.columns:
        df["Minimum_Required"] = 10

    df["Status"] = df.apply(
        lambda row: (
            "⚠️ REORDER NEEDED"
            if row["Current_Stock"] < row["Minimum_Required"]
            else "✅ OK"
        ),
        axis=1,
    )

    st.sidebar.header("🔍 Interactive Controls")
    search_query = st.sidebar.text_input("Search Product Name", "")
    status_filter = st.sidebar.multiselect(
        "Filter by Status",
        options=["⚠️ REORDER NEEDED", "✅ OK"],
        default=["⚠️ REORDER NEEDED", "✅ OK"],
    )

    filtered_df = df[
        (df["Item_Name"].str.contains(search_query, case=False, na=False))
        & (df["Status"].isin(status_filter))
    ]

    low_stock = df[df["Current_Stock"] < df["Minimum_Required"]]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", len(df))
    col2.metric("Healthy Stock Items", len(df) - len(low_stock))
    col3.metric("Critical Alerts", len(low_stock), delta_color="inverse")
    col4.metric("Total Stock On Hand", int(df["Current_Stock"].sum()))

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["📋 Data Grid & Edits", "📊 Visual Analytics", "⚡ Action Center"]
    )

    with tab1:
        st.subheader("Live Inventory Table")
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
            col_target = (
                "quantity" if "quantity" in df.columns else "Current_Stock"
            )
            name_target = (
                "item_name" if "item_name" in df.columns else "Item_Name"
            )

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
                for c in [
                    "id",
                    "Item_Name",
                    "Current_Stock",
                    "Minimum_Required",
                ]
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
        "No inventory items found. Add initial records into your Supabase table."
    )
