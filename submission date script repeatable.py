import requests
import pandas as pd
import re
from docx import Document

# ----------- User Agent Generator -----------
def generate_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36"

# ----------- Extract CIK Dictionary from .docx File -----------
def extract_dictionary_from_docx(file_path):
    doc = Document(file_path)
    extracted_dict = {}

    for para in doc.paragraphs:
        match = re.match(r'([a-zA-Z]{1,6})\s{1,13}(\d{1,10})', para.text)
        if match:
            key = match.group(1).strip().upper()
            value = match.group(2).strip()
            extracted_dict[key] = value
    return extracted_dict

# ----------- Retrieve Filing Links from SEC -----------
def get_edgar_filing_links(ticker, cik):
    url = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
    headers = {'User-Agent': generate_user_agent()}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accession_numbers = filings.get("accessionNumber", [])
        report_dates = filings.get("reportDate", [])
        filing_dates = filings.get("filingDate", [])

        results = []
        for form, accession, report_date, filing_date in zip(forms, accession_numbers, report_dates, filing_dates):
            if form in ['10-K', '10-Q'] and report_date and filing_date:
                accession_clean = accession.replace('-', '')
                edgar_link = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/index.html"

                results.append({
                    'Form': form,
                    'Period End': report_date,
                    'Filing Date': filing_date,
                    'EDGAR Link': edgar_link
                })

        df = pd.DataFrame(results)
        df = df.sort_values('Period End').reset_index(drop=True)
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching SEC data for {ticker}: {e}")
        return pd.DataFrame()

# ----------- Main Execution Loop -----------
if __name__ == "__main__":
    file_path = "C:/Users/Admin/Documents/textfile.docx"
    cik_dict = extract_dictionary_from_docx(file_path)

    while True:
        ticker = input("\nEnter a ticker symbol (or type 'exit' to quit): ").strip().upper()
        if ticker == "EXIT":
            print("Exiting.")
            break

        cik = cik_dict.get(ticker)
        if cik:
            print(f"Fetching EDGAR filings for {ticker} (CIK: {cik})...\n")
            filings_df = get_edgar_filing_links(ticker, cik)

            if not filings_df.empty:
                print(filings_df)
            else:
                print("No 10-K or 10-Q filings found.")
        else:
            print(f"CIK for ticker '{ticker}' not found in the dictionary.")
