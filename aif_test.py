import pandas as pd
import numpy as np
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

def main():

    profile_icon = "https://raw.githubusercontent.com/sjpradhan/aif_test/master/transaction.png"
    st.set_page_config(page_title="Aif-Transactions" , page_icon=profile_icon)
    st.header(":rainbow[Upload Transaction File]")

    col1, col2 = st.columns(2)
    with (col1):
        # File uploader
        uploaded_file = st.file_uploader(":orange[Choose a Text file] 📁", type=["txt"])

        if uploaded_file is not None:
            def read_from_uploaded_file(uploaded_file):
                transaction = pd.read_csv(uploaded_file, delimiter='|', header=None)
                columns = ['CLAIM_START_DATE', 'CLAIM_END_DATE', 'IFSC_CODE', 'ACCOUNT_NUMBER', 'TRANSACTION_DATE',
                           'TRANSACTION_TYPE', 'TRANSACTION_INDICATOR', 'TRANSACTION_AMOUNT', 'OUTSTANDING_AMT',
                           'EFFECTIVE_PRINCP_DUE_AMT']
                transaction.columns = columns
                transaction[['ACCOUNT_NUMBER']] = transaction[['ACCOUNT_NUMBER']].astype(str)
                return transaction

            transaction = read_from_uploaded_file(uploaded_file)
    st.divider()

    try:
        # Initialize a running balance column
        transaction['RUNNING_BALANCE'] = 0

        # Define the initial balance
        initial_balance = 0

        # Define a function to update the running balance
        def update_running_balance(row, previous_balance):
            if row['TRANSACTION_INDICATOR'] == 'O':
                balance = row['TRANSACTION_AMOUNT']
            elif row['TRANSACTION_INDICATOR'] == 'P':
                balance = previous_balance
            elif row['TRANSACTION_INDICATOR'] == 'D':
                balance = previous_balance + row['TRANSACTION_AMOUNT']
            elif row['TRANSACTION_INDICATOR'] == 'C':
                balance = previous_balance - row['TRANSACTION_AMOUNT']
            elif row['TRANSACTION_INDICATOR'] == 'B':
                balance = previous_balance + row['TRANSACTION_AMOUNT']
            elif row['TRANSACTION_INDICATOR'] == 'L':
                balance = previous_balance
            return balance

        # Iterate through the DataFrame and update the running balance
        for i in range(len(transaction)):
            if i == 0:
                transaction.at[i, 'RUNNING_BALANCE'] = update_running_balance(transaction.iloc[i], initial_balance)
            else:
                transaction.at[i, 'RUNNING_BALANCE'] = update_running_balance(transaction.iloc[i],
                                                                              transaction.at[i - 1, 'RUNNING_BALANCE'])

        # Initialize a principle balance column
        transaction['PRINCIPLE_BALANCE'] = 0

        # Define the initial balance
        initial_balance = 0

        # Define a function to update the principle balance
        def update_principle_balance(row, previous_balance):
            if row['TRANSACTION_INDICATOR'] == 'O':
                balance = row['EFFECTIVE_PRINCP_DUE_AMT']
            elif row['TRANSACTION_INDICATOR'] == 'P':
                balance = previous_balance - row['TRANSACTION_AMOUNT']
            elif row['TRANSACTION_INDICATOR'] == 'D':
                balance = previous_balance
            elif row['TRANSACTION_INDICATOR'] == 'C':
                balance = previous_balance
            elif row['TRANSACTION_INDICATOR'] == 'B':
                balance = previous_balance + row['TRANSACTION_AMOUNT']
            elif row['TRANSACTION_INDICATOR'] == 'L':
                balance = previous_balance
            return balance

        # Iterate through the DataFrame and update the running balance
        for i in range(len(transaction)):
            if i == 0:
                transaction.at[i, 'PRINCIPLE_BALANCE'] = update_principle_balance(transaction.iloc[i], initial_balance)
            else:
                transaction.at[i, 'PRINCIPLE_BALANCE'] = update_principle_balance(transaction.iloc[i], transaction.at[
                    i - 1, 'PRINCIPLE_BALANCE'])

        transaction['RUNNING_BALANCE_CHECK'] = transaction['OUTSTANDING_AMT'] - transaction['RUNNING_BALANCE']
        transaction['PRINCIPLE_BALANCE_CHECK'] = transaction['EFFECTIVE_PRINCP_DUE_AMT'] - transaction[
            'PRINCIPLE_BALANCE']

        tolerance = 1e-8
        transaction.loc[
            np.isclose(transaction['RUNNING_BALANCE_CHECK'], 0, atol=tolerance), 'RUNNING_BALANCE_CHECK'] = 0

        tolerance = 1e-8
        transaction.loc[
            np.isclose(transaction['PRINCIPLE_BALANCE_CHECK'], 0, atol=tolerance), 'PRINCIPLE_BALANCE_CHECK'] = 0

        # Filter rows where the RUNNING_BALANCE_CHECK is not zero
        compare_running_balance = transaction[transaction['RUNNING_BALANCE_CHECK'] != 0]
        compare_running_balance =  compare_running_balance[['TRANSACTION_INDICATOR','TRANSACTION_AMOUNT','OUTSTANDING_AMT',
                                                            'RUNNING_BALANCE','RUNNING_BALANCE_CHECK']]

        # Filter rows where the PRINCIPLE_BALANCE_CHECK is not zero
        compare_principle_balance = transaction[transaction['PRINCIPLE_BALANCE_CHECK'] != 0]
        compare_principle_balance =  compare_principle_balance[['TRANSACTION_INDICATOR','TRANSACTION_AMOUNT','EFFECTIVE_PRINCP_DUE_AMT',
                                                            'PRINCIPLE_BALANCE','PRINCIPLE_BALANCE_CHECK']]

        if not compare_running_balance.empty:
            st.write("Error occurred in running balance amount:", compare_running_balance,"Total number of errors",
                     compare_running_balance.shape[0])
            st.divider()

        if not compare_principle_balance.empty:
            st.write("Error occurred in principle balance amount:", compare_principle_balance,"Total number of errors",
                     compare_principle_balance.shape[0])
            st.divider()

        transaction['OUTSTANDING_AMT'].update(transaction['RUNNING_BALANCE'])
        transaction['EFFECTIVE_PRINCP_DUE_AMT'].update(transaction['PRINCIPLE_BALANCE'])

        st.write("Download Rectified Dataset:")
        transaction = transaction.iloc[0:, 0: 10]
        transaction[['TRANSACTION_AMOUNT','OUTSTANDING_AMT','EFFECTIVE_PRINCP_DUE_AMT']] \
                = transaction[['TRANSACTION_AMOUNT','OUTSTANDING_AMT','EFFECTIVE_PRINCP_DUE_AMT']].astype(str)

        st.dataframe(transaction)
    except Exception as e:
        st.error("Please Upload Transaction File to Rectify Data.")


if __name__ == "__main__":
    main()