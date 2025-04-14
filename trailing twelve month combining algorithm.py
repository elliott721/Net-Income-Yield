import requests
import random
import json
import time
from bs4 import BeautifulSoup
import re
from datetime import datetime
from docx import Document
import pandas as pd

# Header
def generate_user_agent():
    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
    os_systems = ['Windows NT 10.0', 'Macintosh', 'X11']
    versions = [''.join([str(random.randint(0, 9)) for _ in range(2)]) for _ in range(3)]
    
    browser = random.choice(browsers)
    os_system = random.choice(os_systems)
    version = '.'.join(versions)
    
    return f"Mozilla/5.0 ({os_system}) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/{version}"

# Retrieve Net Income Data
def get_sec_net_income(ticker, cik):
    headers = {'User-Agent': generate_user_agent()}
    base_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json"
    
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        net_income_data = []
        
        if 'facts' in data and 'us-gaap' in data['facts']:
            if 'NetIncomeLoss' in data['facts']['us-gaap']:
                units = data['facts']['us-gaap']['NetIncomeLoss']['units']
                if 'USD' in units:
                    for entry in units['USD']:
                        if 'form' in entry and entry['form'] in ['10-K', '10-Q']:
                            net_income_data.append({
                                'date': entry['end'],
                                'value': entry['val'],
                                'form': entry['form']
                            })
        
        net_income_data.sort(key=lambda x: x['date'])
        return net_income_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {str(e)}")
        return None


# Extract CIK to ticker key-value dictionary from the document
def extract_dictionary_from_docx(file_path):
    doc = Document(file_path)
    extracted_dict = {}
    
    for para in doc.paragraphs:
        match = re.match(r'([a-zA-Z]{1,6})\s{1,13}(\d{1,10})', para.text)
        if match:
            key = match.group(1)
            value = match.group(2)
            extracted_dict[key.strip()] = value.strip()
    
    return extracted_dict


# Main Code Execution

# File path
file_path = "C:/Users/Admin/Documents/textfile.docx"

# Extract CIK dictionary
extracted_data = extract_dictionary_from_docx(file_path)

# User inputs ticker symbol
ticker = input("Enter the ticker you want to search for: ")
cik = extracted_data.get(ticker, None)


# Parse net income data using pandas
if cik:
    # Fetch net income data
    print(f"Fetching net income data for {ticker} (CIK: {cik})")
    net_income_data = get_sec_net_income(ticker, cik)

    if net_income_data:
        print("Net Income Data:")

        # Prepare and print DataFrame from the net income data
        data = []
        for entry in net_income_data:
            net_income_print = entry['value'] 
            date = datetime.strptime(entry['date'], '%Y-%m-%d').strftime('%Y-%m-%d')
            form = entry['form']
            print(f"Date: {date}, Form: {form}, Net Income: ${net_income_print:.2f}")

            # Append each entry as a dictionary for DataFrame
            data.append({'Date': date, 'Form': form, 'Net Income': float(net_income_print)})

        # Create DataFrame (exlcude redundant 10-q data)
        df = pd.DataFrame(data)
        df_unique_last = df.drop_duplicates(subset=['Date', 'Form'], keep='last')  #Exclude 10-q filing data that isn't quarterly
        df_filtered = df[~df.duplicated(subset=['Date', 'Form'], keep=False)]      #Exclude all duplicate data
        final_df = pd.concat([df_unique_last, df_filtered]).drop_duplicates(subset=['Date', 'Form'], keep='last')  #Concatenate data
        final_df['Date'] = pd.to_datetime(final_df['Date'])     
        final_df = final_df.sort_values(by='Date', ascending=True)  #Sort by date

        # Convert 10-K Annual Data into Q4 Data
        def convert_10k_to_q4(final_df):
            annual_data = final_df[final_df['Form'] == '10-K'] 
            quarterly_data = final_df[final_df['Form'] == '10-Q'] 

            for _, annual_row in annual_data.iterrows():
                matching_quarters = quarterly_data[quarterly_data['Date'] <= annual_row['Date']] 
                matching_quarters = matching_quarters.sort_values(by='Date', ascending=False)  


                 # If there are at least 3 quarters, take the most recent 3
                if len(matching_quarters) >= 3:
                    prev_quarters = matching_quarters.head(3)
                    q4_value = annual_row['Net Income'] - prev_quarters['Net Income'].sum()
            
                    # Update the Net Income for the annual (Q4) entry
                    final_df.loc[final_df['Date'] == annual_row['Date'], 'Net Income'] = q4_value
                    print(final_df)

            return final_df



            





        # Display the DataFrame
        print("\nNet Income DataFrame:")
        print(final_df)

    else:
        print("No net income data found")

else:
    print(f"Ticker {ticker} not found in the extracted dictionary")

print("Done")
