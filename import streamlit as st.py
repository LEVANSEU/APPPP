import streamlit as st
import pandas as pd
import io
from openpyxl import Workbook
import re

st.set_page_config(layout="wide")
st.title("კომპანიების ანალიზი - ჩარიცხვები")

# Set default page
if 'page' not in st.session_state:
    st.session_state['page'] = 'main'

# File uploads (always shown)
report_file = st.file_uploader("📄 ატვირთე ანგარიშფაქტურების ფაილი", type=["xlsx"])
statement_files = st.file_uploader("📄 ატვირთე საბანკო ამონაწერის ფაილები", type=["xlsx"], accept_multiple_files=True)

# If both files uploaded, read them
if report_file and statement_files:
    purchases_df = pd.read_excel(report_file, sheet_name='Grid')
    purchases_df['დასახელება'] = purchases_df['გამყიდველი'].astype(str).apply(lambda x: re.sub(r'^\(\d+\)\s*', '', x).strip())
    purchases_df['საიდენტიფიკაციო კოდი'] = purchases_df['გამყიდველი'].apply(lambda x: ''.join(re.findall(r'\d', str(x)))[:11])

    bank_dfs = []
    for file in statement_files:
        df = pd.read_excel(file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        bank_dfs.append(df)
    bank_df = pd.concat(bank_dfs, ignore_index=True)

    # PAGE: MAIN
    if st.session_state['page'] == 'main':
        st.subheader("კომპანიები ანგარიშფაქტურის გარეშე")

        bank_ids = set(bank_df['P'])
        invoice_ids = set(purchases_df['საიდენტიფიკაციო კოდი'])
        missing_ids = list(bank_ids - invoice_ids)

        missing_data = []
        for cid in missing_ids:
            rows = bank_df[bank_df['P'] == cid]
            if not rows.empty:
                name = rows.iloc[0]['Name']
                total = rows['Amount'].sum()
                missing_data.append([name, cid, total])

        for name, cid, total in missing_data:
            cols = st.columns([2, 2, 2])
            with cols[0]:
                st.write(name)
            with cols[1]:
                st.write(cid)
            with cols[2]:
                if st.button("ნახვა", key=f"view_{cid}"):
                    st.session_state['selected_missing_company'] = cid
                    st.session_state['page'] = 'missing_company'
                    st.experimental_rerun()

    # PAGE: MISSING COMPANY DETAIL
    elif st.session_state['page'] == 'missing_company':
        cid = st.session_state.get('selected_missing_company')
        rows = bank_df[bank_df['P'] == cid]
        st.subheader(f"ჩარიცხვების ცხრილი - {cid}")
        if not rows.empty:
            st.dataframe(rows, use_container_width=True)
        else:
            st.warning("ჩანაწერი არ მოიძებნა.")
        if st.button("⬅️ დაბრუნება"):
            st.session_state['page'] = 'main'
            st.session_state.pop('selected_missing_company', None)
            st.experimental_rerun()
