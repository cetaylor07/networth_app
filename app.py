import streamlit as st
import requests
import pandas as pd
import plotly.express as px

BASE_URL = "http://127.0.0.1:8000"

# --- Section 4: Show Total Net Worth ---
st.subheader("Total Net Worth")

# --- Section 5: Show Net Worth History ---
net_worth_history = requests.get(f"{BASE_URL}/net-worth-history/").json()

if net_worth_history:
    tab1, tab2 = st.tabs(["Chart", "Data"])

    with tab2:
        df_nw = pd.DataFrame(net_worth_history)
        df_nw["date"] = pd.to_datetime(df_nw["date"]).dt.date
        st.dataframe(df_nw, hide_index=True)

    with tab1: 

        time_options = {
            "1 Month": 1,
            "3 Months": 3,
            "6 Months": 6,
            "All": None
        }

        if 'timeframe_toggle' not in st.session_state:
            st.session_state['timeframe_toggle'] = "All"
        
        col1, col2 = st.columns([.55,.45])

        with col2:

        # Create segmented control for selecting time frame
            selected_timeframe = st.segmented_control(
                "Select Time Frame", 
                list(time_options.keys()),
                key="timeframe_toggle",
                label_visibility="hidden")

            # Filter the dataframe based on the selected time frame
        if time_options[selected_timeframe] is not None:
            df_nw["date"] = pd.to_datetime(df_nw["date"])
            df_nw = df_nw.sort_values(by="date").drop_duplicates(subset=["date"])
            cutoff_date = (df_nw["date"].max() - pd.DateOffset(months=time_options[selected_timeframe])).normalize()
            df_filtered = df_nw[df_nw["date"] >= cutoff_date]
        else:
            # If "All" is selected, use the complete dataset
            df_filtered = df_nw.copy().sort_values(by="date").drop_duplicates(subset=["date"])
        
        with col1:
            net_worth = requests.get(f"{BASE_URL}/net-worth/").json()["net_worth"]
            if not df_filtered.empty:
                start_net_worth = df_filtered.iloc[0]["total_net_worth"]  # First entry in filtered data
                net_worth_change = net_worth - start_net_worth  # Difference from start to now
            else:
                net_worth_change = 0
            st.metric(label="Net Worth", value=f"${net_worth:,.0f}",delta=net_worth_change, label_visibility="collapsed")


        # Create the chart with the filtered data
        fig_nw = px.line(df_filtered, x="date", y="total_net_worth")
        fig_nw.update_traces(hovertemplate="%{x}<br>$%{y:,.0f}")
        fig_nw.update_layout(
            xaxis_title="",
            yaxis_title="",
            dragmode=False,
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
            hovermode="closest",
            hoverlabel=dict(
                bgcolor="#5c5683",
                font_size=16,                
                font_color="#819a71",
                bordercolor="#3e999f"
            )
        )
        # Display the chart only once
        st.plotly_chart(fig_nw, use_container_width=True)

else:
    st.warning("No net worth history recorded yet.")

# --- Section 1: Add New Account using a Modal Popover ---
col1, col2, col3, col4 = st.columns([.7,.1,.1,.1], vertical_alignment='bottom')

with col1:
    pass

with col2:
    with st.popover(label="➕", help = 'Create New Account'):  # Popover acts as a dropdown-like container
        account_name = st.text_input("Account Name", key="add_account_popover")
        account_type = st.selectbox("Account Type", ["asset", "debt"], key="account_type_popover")

        if st.button("Create Account", key="create_account_popover"):
            if not account_name.strip():  # Prevent empty account names
                st.error("Account name cannot be empty")
            else:
                res = requests.post(
                    f"{BASE_URL}/add-account/",
                    json={"account_name": account_name, "account_type": account_type},
                )
                if res.status_code == 200:
                    st.success(res.json()["message"])
                    st.rerun()
                else:
                    st.error("Error creating account")

with col3:
    with st.popover(label="🗑️", help="Delete an Account"):  
        account_names = [acc["account_name"] for acc in requests.get(f"{BASE_URL}/accounts/").json()]

        if account_names:
            selected_account = st.selectbox("Select Account", account_names, key="delete_account_popover")

            if st.button("Delete Account", key="delete_account_button"):
                res = requests.delete(f"{BASE_URL}/delete-account/{selected_account}")
                if res.status_code == 200:
                    st.success(f"{selected_account} deleted successfully!")
                    st.rerun()  # Refresh the page
                else:
                    st.error("Error deleting account")
        else:
            st.warning("No accounts available to delete.")


# --- Section 2: Update Account Balance ---
with col4:
    accounts = requests.get(f"{BASE_URL}/accounts/").json()
    account_names = [acc["account_name"] for acc in accounts]

    if account_names:
        with st.popover(label="✏️", help='Update Account'):
            selected_account = st.selectbox("Select Account", account_names, key="update_balance_account")
            new_balance = st.number_input("New Balance", step=1, key="balance_update")
            update_date = st.date_input("Date", key="balance_date")

            if st.button("Update Balance", key="update_balance_btn"):
                res = requests.post(
                    f"{BASE_URL}/update-balance/{selected_account}",
                    json={"date": str(update_date), "balance": new_balance}
                )
                st.success(res.json()["message"])
                st.rerun()
    else:
        st.warning("No accounts available. Please add an account first.")

# --- Section 3: Accounts DataFrame ---

accounts = requests.get(f"{BASE_URL}/accounts/").json()

if accounts:
    # Convert accounts data into a DataFrame
    df_accounts = pd.DataFrame(accounts)

    # Ensure balance is properly formatted as a whole number
    df_accounts["balance"] = df_accounts["balance"].astype(int)

    # Rename columns for better readability
    df_accounts.rename(columns={"account_name": "Account Name", "account_type": "Account Type", "balance": "Balance ($)"}, inplace=True)

    # Split data into assets and debts
    df_assets = df_accounts[df_accounts["Account Type"] == "asset"].drop(columns=["Account Type"])
    df_debts = df_accounts[df_accounts["Account Type"] == "debt"].drop(columns=["Account Type"])

    # Display Assets Table
    st.subheader("💰 Asset Accounts")
    if not df_assets.empty:
        st.dataframe(df_assets, hide_index=True)
    else:
        st.warning("No asset accounts available.")

    # Display Debts Table
    st.subheader("💳 Debt Accounts")
    if not df_debts.empty:
        st.dataframe(df_debts, hide_index=True)
    else:
        st.warning("No debt accounts available.")

else:
    st.warning("No accounts available.")

# --- Section 4: Show Account Balance History ---
if account_names:
    with st.expander("📊 Account Balance History", expanded=False):
        selected_account_history = st.selectbox("Select Account for History", account_names, key="history_account")
        balance_history = requests.get(f"{BASE_URL}/balances/{selected_account_history}").json()

        if balance_history and "error" not in balance_history:
            tab1, tab2 = st.tabs(["Chart", "Data"])

            with tab2:

                df = pd.DataFrame(balance_history)
                df["date"] = pd.to_datetime(df["date"]).dt.date
                st.dataframe(df, hide_index=True)

                # Get account type from the fetched accounts data
                account_type = next(acc['account_type'] for acc in accounts if acc['account_name'] == selected_account_history)
            with tab1:

                if account_type == "asset":
                    # For assets: values are positive; Y-axis from 0 to max_balance.
                    fig = px.line(df, x="date", y="balance",
                                  markers=True)
                elif account_type == "debt":
                    # For debts: values are negative; Y-axis from max_balance (least negative) to min_balance (most negative).
                    fig = px.line(df, x="date", y="balance",
                                  markers=True)
                    fig.update_layout(yaxis=dict(autorange='reversed'))
                fig.update_traces(hovertemplate="%{x}<br>$%{y:,.0f}")
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="",
                    dragmode=False,
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True)
                )


                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No balance history found for this account.")







