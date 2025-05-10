import importlib.util
import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Load submodules dynamically ---
def load_module_from_path(enclave, module_name):
    spec = importlib.util.spec_from_file_location(module_name, enclave)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# --- Upload to Google Sheets ---
def upload_to_google_sheet(df, sheet_name="All Combined Data"):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        r"C:\Users\Admin\Downloads\arctic-plate-459211-v7-befbd43919a2.json",
        scope
    )
    client = gspread.authorize(creds)

    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(sheet_name).sheet1

    headers = sheet.row_values(1)
    if len(headers) != len(set(headers)):
        print("❌ Duplicate column names found in header. Clearing and starting fresh.")
        sheet.clear()
        existing_data = pd.DataFrame(columns=df.columns)
    else:
        existing_data = pd.DataFrame(sheet.get_all_records(expected_headers=headers))

    combined_df = pd.concat([existing_data, df], ignore_index=True)
    combined_df.drop_duplicates(subset=["Ticker", "Date"], keep="last", inplace=True)
    combined_df = combined_df.replace([float("inf"), float("-inf"), pd.NA, None], "")
    combined_df = combined_df.fillna("").astype(str)

    sheet.clear()
    sheet.update([combined_df.columns.tolist()] + combined_df.values.tolist())
    print(f"✅ Uploaded to Google Sheet: {sheet_name}")

# --- Main logic ---
def main():
    ttm_enclave = r"C:\Users\Admin\Downloads\trailing twelve month net income script repeatable.py"
    submission_enclave = r"C:\Users\Admin\Downloads\submission date script repeatable.py"
    shares_outstanding_enclave = r"C:\Users\Admin\Downloads\shares outstanding repeatable.py"
    key_value_enclave = r"C:\Users\Admin\Documents\textfile.docx"

    ttm_mod = load_module_from_path(ttm_enclave, "ttm_module")
    sub_mod = load_module_from_path(submission_enclave, "submission_module")
    shares_mod = load_module_from_path(shares_outstanding_enclave, "shares_module")

    cik_dict = ttm_mod.extract_dictionary_from_docx(key_value_enclave)
    ticker = input("Enter a ticker: ").strip().upper()
    cik = cik_dict.get(ticker)

    if not cik:
        print(f"CIK not found for {ticker}")
        return

    net_df = ttm_mod.get_sec_net_income(cik)
    if net_df.empty:
        print("No net income data.")
        return

    net_df = ttm_mod.reduce_10k_to_quarterly(net_df)
    net_df = ttm_mod.calculate_ttm_net_income(net_df)

    filing_df = sub_mod.get_edgar_filing_links(ticker, cik)
    filing_df.rename(columns={"Period End": "Date"}, inplace=True)
    filing_df["Date"] = pd.to_datetime(filing_df["Date"])

    merged = pd.merge(net_df, filing_df[["Date", "Filing Date"]], on="Date", how="left")

    # Add Shares Outstanding
    shares_df = shares_mod.get_shares_outstanding(cik)
    shares_df["Date"] = pd.to_datetime(shares_df["Date"], errors="coerce")
    merged = pd.merge(merged, shares_df[["Date", "Shares Outstanding"]], on="Date", how="left")

    merged["Ticker"] = ticker
    merged = merged[["Ticker", "Date", "Form", "Net Income", "TTM Net Income", "Filing Date", "Shares Outstanding"]]
    merged = merged.reset_index(drop=True)

    # Label quarters
    merged["Date"] = pd.to_datetime(merged["Date"], errors="coerce")
    quarter_map = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}
    merged["Quarter"] = merged["Date"].dt.month.map(quarter_map)
    merged.drop("Form", axis=1, inplace=True)

    # Format dates and clean data
    merged["Date"] = merged["Date"].dt.strftime("%Y-%m-%d")
    merged["Filing Date"] = pd.to_datetime(merged["Filing Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    merged = merged.replace([float("inf"), float("-inf")], pd.NA).fillna("")

    print("\nFinal merged data preview:")
    print(merged.tail())

    upload_to_google_sheet(merged)

if __name__ == "__main__":
    main()
