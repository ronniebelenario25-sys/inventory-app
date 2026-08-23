import streamlit as st
import pandas as pd
import plotly.express as px

# Page Setup
st.set_page_config(page_title="Advanced Inventory System", layout="wide")
st.title("📦 Smart Inventory & Operations Dashboard")

# File Upload
uploaded_file = st.file_uploader("Upload Inventory CSV File", type=["csv"])

if uploaded_file is not None:
    # Load session state data so edits persist
    if "df" not in st.session_state:
        st.session_state.df = pd.read_csv(uploaded_file)
    
    df = st.session_state.df
    
    # Calculate status dynamically
    df["Status"] = df.apply(
        lambda row: "⚠️ REORDER NEEDED" if row["Current_Stock"] < row["Minimum_Required"] else "✅ OK", 
        axis=1
    )
    
    # --- SIDEBAR INTERACTIVE FILTERS ---
    st.sidebar.header("🔍 Interactive Controls")
    search_query = st.sidebar.text_input("Search Product Name", "")
    status_filter = st.sidebar.multiselect(
        "Filter by Status", 
        options=["⚠️ REORDER NEEDED", "✅ OK"], 
        default=["⚠️ REORDER NEEDED", "✅ OK"]
    )
    
    # Filter Data
    filtered_df = df[
        (df["Item_Name"].str.contains(search_query, case=False, na=False)) & 
        (df["Status"].isin(status_filter))
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
    tab1, tab2, tab3 = st.tabs(["📋 Data Grid & Edits", "📊 Visual Analytics", "⚡ Action Center"])
    
    with tab1:
        st.subheader("Live Inventory Table")
        st.caption("Tip: You can filter data using the sidebar controls on the left!")
        st.dataframe(filtered_df, use_container_width=True)
        
        st.divider()
        st.subheader("✏️ Quick Stock Update Tool")
        selected_item = st.selectbox("Select Product to Update", df["Item_Name"].unique())
        new_stock = st.number_input("Enter New Stock Level", min_value=0, value=10)
        if st.button("Update Stock Level"):
            st.session_state.df.loc[st.session_state.df["Item_Name"] == selected_item, "Current_Stock"] = new_stock
            st.success(f"Updated {selected_item} stock to {new_stock}!")
            st.rerun()

    with tab2:
        st.subheader("Inventory vs Minimum Thresholds")
        # Visual Chart comparing Current vs Minimum Stock
        fig = px.bar(
            df, 
            x="Item_Name", 
            y=["Current_Stock", "Minimum_Required"], 
            barmode="group",
            labels={"value": "Quantity", "Item_Name": "Product"},
            title="Stock Comparison Chart"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🚨 Automated Supplier Action Center")
        if len(low_stock) > 0:
            st.warning(f"There are {len(low_stock)} items currently below minimum limits.")
            st.table(low_stock[["Item_ID", "Item_Name", "Current_Stock", "Minimum_Required"]])
            if st.button("📧 Dispatch Automated Supplier Reorder Batch"):
                st.success("Reorder alert dispatches sent to supplier email!")
                st.balloons()
        else:
            st.success("🎉 All inventory stock levels are healthy!")

else:
    st.info("Please upload your `inventory.csv` file above to initialize the dashboard.")
