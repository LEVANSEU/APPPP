import streamlit as st
import pandas as pd
import io
from openpyxl import Workbook
import re

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        body, .main, .block-container {
            background-color: white !important;
            color: #222 !important;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stTextLabelWrapper, label {
            color: #222 !important;
        }
        .stFileUploader, .stTextInput, .stSelectbox, .stRadio, .stButton, .stDataFrame,
        .stTextInput input, .stSelectbox div[data-baseweb="select"],
        .stSelectbox div[data-baseweb="select"] *, .stRadio div[role="radiogroup"] label,
        .stRadio div[role="radiogroup"] label * {
            background-color: #f5f5f5 !important;
            color: #222 !important;
            border-radius: 10px;
            font-size: 14px !important;
        }
        .stFileUploader {
            max-width: 600px !important;
            margin: 0 auto !important;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white !important;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 14px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .summary-header {
            display: flex;
            font-weight: bold;
            margin-top: 1em;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #999;
            text-align: center;
            background-color: #f0f0f0;
            border-radius: 8px;
            color: #222 !important;
        }
        .summary-header div {
            flex: 1;
            padding: 0.5rem;
        }
        .number-cell {
            text-align: right !important;
            font-variant-numeric: tabular-nums;
            padding-right: 1rem;
            font-weight: bold;
            color: #222;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ანგარიში და ჩარიცხვები")

report_file = st.file_uploader("ატვირთე ანგარიშფაქტურების ფაილი (report.xlsx)", type=["xlsx"])
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები (statement.xlsx)", type=["xlsx"], accept_multiple_files=True)

if report_file and statement_files:
    purchases_df = pd.read_excel(report_file, sheet_name='Grid')

    bank_dfs = []
    for statement_file in statement_files:
        df = pd.read_excel(statement_file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        bank_dfs.append(df)

    bank_df = pd.concat(bank_dfs, ignore_index=True) if bank_dfs else pd.DataFrame()

    purchases_df['დასახელება'] = purchases_df['გამყიდველი'].astype(str).apply(lambda x: re.sub(r'^\(\d+\)\s*', '', x).strip())
    purchases_df['საიდენტიფიკაციო კოდი'] = purchases_df['გამყიდველი'].apply(lambda x: ''.join(re.findall(r'\d', str(x)))[:11])

    invoice_company_ids = set(purchases_df['საიდენტიფიკაციო კოდი'].dropna())
    missing_ids = [cid for cid in bank_df['P'].unique() if cid not in invoice_company_ids]

    if 'missing_company_view' in st.session_state:
        selected_id = st.session_state['missing_company_view']
        st.subheader(f"ჩარიცხვები კომპანიისთვის - {selected_id}")
        st.dataframe(bank_df[bank_df['P'] == selected_id], use_container_width=True)
        if st.button("⬅️ დაბრუნება"):
            del st.session_state['missing_company_view']
            st.experimental_rerun()
    else:
        st.subheader("📋 კომპანიები რომლებიც მხოლოდ ჩარიცხვებში გვხვდება")
        for company_id in missing_ids:
            company_data = bank_df[bank_df['P'] == company_id]
            company_name = company_data['Name'].iloc[0] if not company_data.empty else "უცნობი"
            total_amount = company_data['Amount'].sum()
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.markdown(f"**{company_name}**")
            with col2:
                if st.button(str(company_id), key=f"btn_{company_id}"):
                    st.session_state['missing_company_view'] = company_id
                    st.experimental_rerun()
            with col3:
                st.markdown(f"{total_amount:,.2f}")
