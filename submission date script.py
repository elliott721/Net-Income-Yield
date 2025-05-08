import requests
import pandas as pd

# Set Delta Air Lines' CIK
DAL_CIK = "0000027904"

def generate_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36"

def get_dal_edgar_filing_links():
    url = f"https://data.sec.gov/submissions/CIK{DAL_CIK.zfill(10)}.json"
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
                edgar_link = f"https://www.sec.gov/Archives/edgar/data/{int(DAL_CIK)}/{accession_clean}/index.html"

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
        print(f"Error fetching SEC data: {e}")
        return pd.DataFrame()

# Run and display
dal_filings_df = get_dal_edgar_filing_links()
print(dal_filings_df)

# Optional: export to CSV
dal_filings_df.to_csv("delta_airlines_10k_10q_filings.csv", index=False)
print("\nSaved to delta_airlines_10k_10q_filings.csv")
