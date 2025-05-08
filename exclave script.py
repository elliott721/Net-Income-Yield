import importlib.util
import pandas as pd
import os

# Dynamically import a Python module from a file path
def load_module_from_path(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    ttm_script_enclave = r"C:\Users\Admin\Downloads\trailing twelve month net income script repeatable.py"
    submission_script_enclave = r"C:\Users\Admin\Downloads\submission date script repeatable.py"
    docx_path = r"C:\Users\Admin\Documents\textfile.docx"

    ttm_mod = load_module_from_path(ttm_script_enclave, "ttm_module")
    sub_mod = load_module_from_path(submission_script_enclave, "submission_module")

    cik_dict = ttm_mod.extract_dictionary_from_docx(docx_path)

    ticker = input("Enter a ticker: ").strip().upper()
    cik = cik_dict.get(ticker)

    if not cik:
        print(f"CIK not found for {ticker}")
        return

    # Fetch and process
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
    merged["Ticker"] = ticker
    merged = merged[["Ticker", "Date", "Form", "Net Income", "TTM Net Income", "Filing Date"]]
    merged = merged.reset_index(drop=True)

    print("\nFinal merged data preview:")
    print(merged.tail())

    # Save to master file only
    master_file = "all_combined_data.csv"
    if not os.path.exists(master_file):
        merged.to_csv(master_file, index=False)
        print(f"✅ Created new master file: {os.path.abspath(master_file)}")
    else:
        merged.to_csv(master_file, mode="a", header=False, index=False)
        print(f"✅ Appended to master file: {os.path.abspath(master_file)}")

if __name__ == "__main__":
    main()
