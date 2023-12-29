
import requests
import bs4
from bs4 import BeautifulSoup
import os
from. table_reformatter import Table_HTML_to_MD
import json

class SEC_HTML_Parser:

    def __init__(self, db_folder, marker_endpage = '-'*80):

        self.base_url = 'https://www.sec.gov'
        self.db_folder = db_folder
        # self.max_cnt_parsedFile = {'4': 0, '10-Q': 1, '8-K': 10}
        self.marker_endpage = marker_endpage
        self.table_reformatter = Table_HTML_to_MD(html_format=True)
        
    def request_to_secarchive(self, url):

        url = self.base_url + url
        headers = {'User-Agent': os.getenv('SEC_USER_AGENT')}
        response = requests.get(url, headers=headers)

        return response

    def htm_to_text(self, document):

        soup = BeautifulSoup(document, "html.parser")

        texts, tabls, merge_txtb = self.extract_recursive(soup.body)

        result = {}
        result['text']   = texts
        result['tables'] = tabls
        result['merged'] = merge_txtb

        return result

    def extract_recursive(self, element):
        
        text_all        = ""
        table_all       = ""
        text_wtable_all = ""
        is_page_end = False

        # for child in element.children:
        if isinstance(element, bs4.element.Tag):
            
            # find page end
            if ('style' in element.attrs) and (('page-break-after' in element['style']) or ('border-bottom' in element['style'])): 
                is_page_end = True
            if (element.name == 'hr') or is_page_end:    
                text_all        += self.marker_endpage + '\n\n'     
                table_all       += self.marker_endpage + '\n\n'   
                text_wtable_all += self.marker_endpage + '\n\n'   
                is_page_end = False
                return text_all, table_all, text_wtable_all

            # Skip the loop if the element is a table
            if element.name == 'table':
                table_html, table_md = self.table_reformatter.convert(element)
                table_all       += table_html + '\n\n'
                text_wtable_all += table_md + '\n\n'
                return text_all, table_all, text_wtable_all  
            
            # if the element has text, get texts from all ascendents
            is_text = element.find(text=True, recursive=False)
            if is_text and (len(is_text.strip()) > 0):
                text_all        += element.text + '\n\n'
                text_wtable_all += element.text + '\n\n'

            # if there is a child, go dive
            for child in element.children:
                result = self.extract_recursive(child)
                text_all        += result[0]
                table_all       += result[1]
                text_wtable_all += result[2]

        return text_all, table_all, text_wtable_all

    def get_filesinfo(self, sec_url):

        file_info = {}
        response = self.request_to_secarchive(sec_url)
        soup = BeautifulSoup(response.text, "html.parser")

        # components in table
        info = soup.find_all("div", class_ = "info")

        # urls for files
        file_urls = []
        table_of_filing = soup.find("table", class_ = "tableFile")
        for i, a in enumerate(table_of_filing.find_all('a')):
            file_url = a['href']
            file_url  = file_url.replace('/ix?doc=','')
            file_urls.append(file_url)
            if i == 0:
                fname = file_url.split('/')[-1].split('.')[0]

        htm_urls = [u for u in file_urls if u.endswith('.htm')]
        txt_url = file_urls[-1]

        file_info['filing_date']      = info[1].text # not used
        file_info['accepted_time']    = info[1].text # not used
        file_info['document_number']  = info[2].text # not used
        file_info['period_of_report'] = info[3].text # not used
        if len(info) < 5: file_info['items'] = None
        else:             file_info['items'] = info[4].text.split('Item ')[1:]
        file_info['htm_urls'] = htm_urls
        file_info['txt_url']  = txt_url
        file_info['first_fname']  = fname
        
        return file_info

    def parse(self, sec_files, target_date):

        files_folder = os.path.join(self.db_folder, target_date)
        if not os.path.exists(files_folder):        
            os.makedirs(files_folder, exist_ok=True)

        for i in range(len(sec_files)):
            form    = sec_files.loc[i,'form'].replace('/A','')
            sec_url = sec_files.loc[i,'sec-url']

            file_info = self.get_filesinfo(sec_url=sec_url)
            
            # add items
            sec_files.loc[i, "items"] = ','.join(file_info['items'])

            # parsed file
            document_all = {}
            for j, url in enumerate(file_info['htm_urls']):
                document = self.request_to_secarchive(url).text
                dict_result = self.htm_to_text(document)
                document_all[f'document_{j}'] = dict_result

            # original complete txt file
            document = self.request_to_secarchive(file_info['txt_url']).text
            document_all['document_txt'] = document
            json_path = os.path.join(files_folder, 'form{}_document_{}.json'.format(form, file_info['first_fname']))

            # save json file as database 
            with open(json_path, "w") as json_file:
                json.dump(document_all, json_file)

            sec_files.loc[i, "parsed-file"] = json_path
            sec_files.loc[i, "used_in_dashboard"] = False

        return sec_files


