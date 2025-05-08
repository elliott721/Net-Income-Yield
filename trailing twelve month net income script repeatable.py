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
# Fetch Net Income Data from SEC
# -------------------------------
def get_sec_net_income(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json"
    headers = {'User-Agent': generate_user_agent()}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        facts = data.get('facts', {}).get('us-gaap', {}).get('NetIncomeLoss', {}).get('units', {}).get('USD', [])
        records = []
        for entry in facts:
            if entry.get('form') in ['10-K', '10-Q']:
                records.append({
                    'Date': entry['end'],
                    'Form': entry['form'],
                    'Net Income': float(entry['val'])
                })
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date')
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

# -------------------------------
# Convert 10-K to Q4 Estimate
# -------------------------------
def reduce_10k_to_quarterly(df):
    df = df.sort_values('Date').reset_index(drop=True)
    ten_k = df[df['Form'] == '10-K']
    ten_q = df[df['Form'] == '10-Q']
    synthesized_q4_rows = []

    for _, row in ten_k.iterrows():
        year = row['Date'].year
        annual_val = row['Net Income']
        q1 = ten_q[ten_q['Date'] == pd.Timestamp(f'{year}-03-31')]
        q2 = ten_q[ten_q['Date'] == pd.Timestamp(f'{year}-06-30')]
        q3 = ten_q[ten_q['Date'] == pd.Timestamp(f'{year}-09-30')]
        if not q1.empty and not q2.empty and not q3.empty:
            total = q1.iloc[0]['Net Income'] + q2.iloc[0]['Net Income'] + q3.iloc[0]['Net Income']
            q4_val = annual_val - total
            synthesized_q4_rows.append({
                'Date': pd.Timestamp(f'{year}-12-31'),
                'Form': '10-Q',
                'Net Income': q4_val
            })

    q4_dates = [row['Date'] for row in synthesized_q4_rows]
    df = df[~((df['Form'] == '10-K') | (df['Date'].isin(q4_dates)))]
    df = pd.concat([df, pd.DataFrame(synthesized_q4_rows)], ignore_index=True)
    return df.sort_values('Date').reset_index(drop=True)

# -------------------------------
# Compute TTM Net Income
# -------------------------------
def calculate_ttm_net_income(df):
    df = df.sort_values('Date').reset_index(drop=True).copy()
    df['TTM Net Income'] = None
    for i in range(3, len(df)):
        last_4 = df.loc[i-3:i, 'Net Income']
        df.at[i, 'TTM Net Income'] = last_4.sum()
    return df

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

        print(f"\nFetching net income for {ticker} (CIK: {cik})...")
        df = get_sec_net_income(cik)
        if df.empty:
            print("No data found.")
            continue

        df = reduce_10k_to_quarterly(df)
        df = calculate_ttm_net_income(df)

        print("\nQuarterly Net Income with TTM:")
        print(df[['Date', 'Net Income', 'TTM Net Income']])

        output_file = f"{ticker}_net_income_ttm.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()

