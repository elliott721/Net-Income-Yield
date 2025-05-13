import requests
import random
import re
from datetime import datetime
from docx import Document
import pandas as pd

# -------------------------------
# Generate a random User-Agent
# -------------------------------
def generate_user_agent():
    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
    os_list = ['Windows NT 10.0', 'Macintosh', 'X11']
    version = '.'.join([str(random.randint(0, 9)) for _ in range(3)])
    return f"Mozilla/5.0 ({random.choice(os_list)}) AppleWebKit/537.36 (KHTML, like Gecko) {random.choice(browsers)}/{version}"

# -------------------------------
# Extract ticker → CIK from DOCX
# -------------------------------
def extract_dictionary_from_docx(file_path):
    doc = Document(file_path)
    extracted_dict = {}
    for para in doc.paragraphs:
        match = re.match(r'([a-zA-Z]{1,6})\s{1,13}(\d{1,10})', para.text.strip())
        if match:
            key = match.group(1).strip().upper()
            value = match.group(2).strip()
            extracted_dict[key] = value
    return extracted_dict

# -------------------------------
# Fetch Shares Outstanding Data
# -------------------------------
def get_shares_outstanding(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json"
    headers = {'User-Agent': generate_user_agent()}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        shares_data = data.get('facts', {}).get('dei', {}).get('EntityCommonStockSharesOutstanding', {}).get('units', {}).get('shares', [])
        records = []
        for item in shares_data:
            if item.get('form') in ['10-K', '10-Q']:
                records.append({
                    'Date': item['end'],
                    'Form': item['form'],
                    'Shares Outstanding': int(item['val'])
                })
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except Exception as e:
        print(f"Error fetching shares outstanding: {e}")
        return pd.DataFrame()

# -------------------------------
# Main Program Loop
# -------------------------------
def main():
    file_path = "C:/Users/Admin/Documents/textfile.docx"
    cik_dict = extract_dictionary_from_docx(file_path)

    while True:
        ticker = input("\nEnter a ticker (or type 'exit' to quit): ").strip().upper()
        if ticker == "EXIT":
            print("Goodbye.")
            break

        cik = cik_dict.get(ticker)
        if not cik:
            print(f"Ticker '{ticker}' not found.")
            continue

        print(f"\nFetching shares outstanding for {ticker} (CIK: {cik})...")
        df = get_shares_outstanding(cik)
        if df.empty:
            print("No data found.")
            continue

        print("\nQuarterly Shares Outstanding:")
        print(df)

if __name__ == "__main__":
    main()
