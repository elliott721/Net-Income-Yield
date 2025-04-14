import requests
import random
import json
import time
from bs4 import BeautifulSoup
import re
from datetime import datetime
from docx import Document
import pandas as pd 


#Header
def generate_user_agent():
    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
    os_systems = ['Windows NT 10.0', 'Macintosh', 'X11']
    versions = [''.join([str(random.randint(0, 9)) for _ in range(2)]) for _ in range(3)]
    
    browser = random.choice(browsers)
    os_system = random.choice(os_systems)
    version = '.'.join(versions)
    
    return f"Mozilla/5.0 ({os_system}) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/{version}"

#Retrieve Net Income Data
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


#CIK to ticker key-value dictionary
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


#File path
file_path = "C:/Users/Admin/Documents/textfile.docx"
extracted_data = extract_dictionary_from_docx(file_path)


#User inputs ticker symbol
ticker = input("Enter the ticker you want to search for: ")
cik = extracted_data.get(ticker, "Key not found")


#Retrieve net income data
print(f"Fetching net income data for {ticker} (CIK: {cik})")
net_income_data = get_sec_net_income(ticker, cik)


#Print net income data
if net_income_data:
    print("Net Income Data:")
    for entry in net_income_data:
        net_income_print = entry['value'] 
        date = datetime.strptime(entry['date'], '%Y-%m-%d').strftime('%Y-%m-%d')
        print(f"Date: {date}, Form: {entry['form']}, Net Income: ${net_income_print:.2f}")
else:
    print("No net income data found")






 
 
 
print("Done")
