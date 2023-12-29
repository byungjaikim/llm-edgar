
import os
import pandas as pd
from .secfile.File_4 import SECRunner_Dashboard_4
from .secfile.File_8K import SECRunner_Dashboard_8K
from .secfile.File_10Q import SECRunner_Dashboard_10Q
from datetime import datetime

class App_SEC_Dashboard:

    def __init__(self, company_name = None, marker_endpage = '-'*80, 
                 db_folder = None, model_name = 'gpt-3.5-turbo-1106', maxlen_llminput = 15000,
                 temperature=0.0, chunk_size_page=5000, chunk_size_text=1000, chunk_overlap_text=100):

        self.company_name = company_name
        self.marker_endpage = marker_endpage
        self.db_folder = db_folder 

        # load database
        self.db_folder = db_folder 
        self.runner_form4 = SECRunner_Dashboard_4(marker_endpage = marker_endpage)
        self.runner_form8K = SECRunner_Dashboard_8K(marker_endpage = marker_endpage, company_name=self.company_name, type_of_summary_source='text',
                                                    model_name = model_name, maxlen_llminput = maxlen_llminput, temperature=temperature)
        self.runner_form10Q = SECRunner_Dashboard_10Q(marker_endpage = marker_endpage, model_name = model_name, temperature=temperature,
                                                      chunk_size_page = chunk_size_page, chunk_size_text = chunk_size_text, chunk_overlap_text = chunk_overlap_text)

        # LLM Model parameters
        self.model_name = model_name
        self.temperature = temperature

    def get_quarter_from_date(self, date):
        # Convert the input date string to a datetime object
        datetime_date = datetime.strptime(date, "%Y-%m-%d")
        
        # Extract the month from the datetime object
        month = datetime_date.month
        
        # Determine the quarter based on the month
        if 1 <= month <= 3:
            return "Q4"
        elif 4 <= month <= 6:
            return "Q1"
        elif 7 <= month <= 9:
            return "Q2"
        elif 10 <= month <= 12:
            return "Q3"
        else:
            return "Invalid Month"

    def run_tasks_form4(self, file_path, sec_url):

        list_info = self.runner_form4.get_data(file_path, sec_url)

        return list_info

    def run_tasks_form8K(self, file_path, accepted_time, items, sec_url):

        info = self.runner_form8K.get_data(file_path)
        info['accepted_time'] = accepted_time
        info['items'] = items
        info['sec_url'] = sec_url

        return [info]

    def run_tasks_form10Q(self, file_path, accepted_time, date, sec_url):

        info = self.runner_form10Q.get_data(file_path, date)
        info['Date'] = date
        info['Quarter'] = self.get_quarter_from_date(date)
        info['sec_url'] = sec_url

        return [info]

    def load_csv(self, path):

        if os.path.isfile(path):
            data = pd.read_csv(path, delimiter='|')
        else:
            data = pd.DataFrame()

        return data

    def update_data(self, form, new_data):

        if form == '4':
            df_path = os.path.join(self.db_folder,'form4.tsv')
            df      = self.load_csv(df_path)
        elif form == '8-K':
            df_path = os.path.join(self.db_folder,'form8K.tsv')
            df      = self.load_csv(df_path)
        elif form == '10-Q':
            df_path = os.path.join(self.db_folder,'form10Q.tsv')
            df      = self.load_csv(df_path)

        new_df = pd.DataFrame.from_records(new_data)
        df = pd.concat([new_df, df], axis=0, ignore_index=True)
        df.to_csv(df_path, sep='|', index=False)

        return

    def run(self, sec_files):
       
        new_data_form4   = []
        new_data_form8K  = []
        new_data_form10Q = []

        for i in range(len(sec_files)):
            form          = sec_files.loc[i,'form'].replace('/A','')
            items         = sec_files.loc[i,'items']
            date          = sec_files.loc[i,'date']
            accepted_time = sec_files.loc[i,'accepted_time']
            file_path     = sec_files.loc[i,'parsed-file']
            sec_url     = 'https://www.sec.gov' + sec_files.loc[i,'sec-url']
            
            if form == '4':      
                data = self.run_tasks_form4(file_path, sec_url)
                new_data_form4.extend(data)
            elif form == '8-K':  
                data = self.run_tasks_form8K(file_path, accepted_time, items, sec_url)
                new_data_form8K.extend(data)
            elif form == '10-Q': 
                data = self.run_tasks_form10Q(file_path, accepted_time, date, sec_url)
                new_data_form10Q.extend(data)
            else:                continue

        if new_data_form4:   self.update_data(form='4', new_data=new_data_form4)
        if new_data_form8K:  self.update_data(form='8-K', new_data=new_data_form8K)
        if new_data_form10Q: self.update_data(form='10-Q', new_data=new_data_form10Q)

        return 



