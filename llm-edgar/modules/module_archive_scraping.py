
import time
import random
from selenium import webdriver
from bs4 import BeautifulSoup
from utils.dict_secfile import DICTIONARY_SEC_FILEINFO
import pandas as pd
import os

class SEC_Archive_Scraper:

    def __init__(self, symbol, cik_number, company_name):
        self.symbol = symbol
        self.cik_number = cik_number
        self.company_name = company_name

    def get_webdrive(self):

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")

        driver = webdriver.Chrome(os.getenv('MY_CHROMEDRIVER_PATH'), options=options)

        return driver

    def get_valid_SEC_files(self, curr_df, prev_df):

        if len(curr_df) == 0: 
            return curr_df

        # is interested form
        interested_form = list(DICTIONARY_SEC_FILEINFO.keys())
        curr_df = curr_df[curr_df.iloc[:, 3].isin(interested_form)]
        
        # is previously scraped 
        if len(prev_df) != 0:
            curr_df = curr_df[~curr_df.iloc[:, 5].isin(prev_df.iloc[:, 5])]

        return curr_df

    def scrap(self, target_date, cnt_scrap_files, prev_df):
        
        driver = self.get_webdrive()
        url = f'https://www.sec.gov/edgar/browse/?CIK={self.cik_number}'

        driver.get(url)  
        time.sleep(random.uniform(0.4, 0.8))

        view_button = driver.find_element_by_xpath('//button[@id="btnViewAllFilings"]')
        driver.execute_script("arguments[0].click();", view_button)
        time.sleep(random.uniform(0.4, 0.8))

        table = driver.find_element_by_xpath('//*[@id="filingsTable"]')
        html_data = table.get_attribute('innerHTML')
        soup = BeautifulSoup(html_data, 'html.parser')

        data = []
        # Extract table rows
        for row in soup.find('tbody').find_all('tr')[:cnt_scrap_files]:
            cells = row.find_all('td')
            if (cells[2].text.strip() == target_date) and (cells[0].text.strip() in DICTIONARY_SEC_FILEINFO.keys()):
                row_data = {
                    'cik_number': self.cik_number, 
                    'symbol': self.symbol,
                    'name': self.company_name, 
                    'form': cells[0].text.strip(), # filing form
                    'date': cells[2].text.strip(), # filing date
                    'sec-url': cells[1].find('a', class_='filing-link-all-files')['href'], # htm file,
                    'info': DICTIONARY_SEC_FILEINFO[cells[0].text.strip()][0]
                }
                data.append(row_data)
        driver.quit()
        df = pd.DataFrame.from_records(data)
        curr_df = self.get_valid_SEC_files(df, prev_df)

        return curr_df

