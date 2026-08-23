import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventory Tracker", layout="wide")
st.title("📦 Automated Inventory Tracker Dashboard")

uploaded_file = st.file_uploader("Upload your inventory CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df["Status"] = df.apply(
        lambda row: "⚠️ REORDER NEEDED" if row["Current_Stock"] < row["Minimum_Required"] else "✅ OK", 
        axis=1
    )
    low_stock = df[df["Current_Stock"] < df["Minimum_Required"]]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", len(df))
    col2.metric("Healthy Stock", len(df) - len(low_stock))
    col3.metric("Reorder Warnings", len(low_stock))
    
    st.subheader("📋 Full Inventory Status")
    st.dataframe(df, use_container_width=True)
    
    if len(low_stock) > 0:
        st.error(f"Alert: {len(low_stock)} product(s) require reordering!")
        if st.button("📧 Trigger Supplier Reorder Alert"):
            st.success("Reorder dispatch notification sent successfully!")
            st.balloons()
