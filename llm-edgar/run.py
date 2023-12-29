
import csv
import os
import models.model_sec as model_sec
from utils.logger import setup_logger

import argparse
from datetime import date, datetime, timedelta
import pytz
from modules import SEC_Archive_Scraper, SEC_HTML_Parser, App_SEC_Dashboard

def get_args_parser():
    parser = argparse.ArgumentParser('sec-dashboard', add_help=False)
    parser.add_argument('--len_posted_edgar', default=100, type=int,
                        help='maximum length of posted edgar list')
    parser.add_argument('--daysago', default=0, type=int, 
                        help='how many days ago data will be collected from today')
    parser.add_argument('--company_list_path', default='./company_list.csv', type=str,
                        help='csv file path for company list')
    parser.add_argument('--output_path', default='./outputs/', type=str,
                        help='output path for blog contents')
    parser.add_argument('--llm_modelname', default='gpt-3.5-turbo-1106', type=str,
                        help='llm provided by OpenAI API')
    parser.add_argument('--llm_temperature', default=0.0, type=float,
                        help='temperature for llm model')
    parser.add_argument('--llm_input_maxlen', default=15000, type=int,
                        help='maximum string length for input of llm')
    parser.add_argument('--do_data_collection', action='store_true', default=False,
                        help='flag to perform data collection and processing')
    parser.add_argument('--do_llm_tasks', action='store_true', default=False,
                        help='flag to perform reserved tasks with LLM')
    return parser

def load_company_info(path_company_list):

    dict_company = {}
    with open(path_company_list, mode='r', newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            ticker = row['Ticker']
            en_name = row['English_Name']
            ciknumer = row['CIK_Number']
            dict_company[ticker] = [en_name, ciknumer]

    return dict_company

def args_updates(args, symbol, ticker_to_info):

    # set time to SEC offical timezone
    args.symbol = symbol
    args.company_name = ticker_to_info[symbol][0]
    args.cik_number = ticker_to_info[symbol][1] 

    args.symbol_path = os.path.join(args.output_path, symbol)
    if not os.path.exists(args.symbol_path):        
        os.makedirs(args.symbol_path, exist_ok=True)

    # a reference file for sec edgar database
    args.sec_files_csvpath = os.path.join(args.symbol_path, 'secdata.tsv')

    return args

if __name__ == "__main__":
    
    args = get_args_parser()
    args = args.parse_args()
    
    # get company list
    dict_company = load_company_info(args.company_list_path)

    # set time to SEC offical timezone
    current_utc_time = datetime.utcnow()
    et_time = current_utc_time.astimezone(pytz.timezone('US/Eastern'))
    et_time = et_time - timedelta(days=args.daysago)

    args.time = et_time
    args.target_date = et_time.strftime("%Y-%m-%d")
    args.curre_time = et_time.strftime("%H_%M_%S")

    # logger file
    log_folderpath = os.path.join(args.output_path, 'log')
    if not os.path.exists(log_folderpath):        
        os.makedirs(log_folderpath, exist_ok=True)
    log_filepath = os.path.join(log_folderpath,'sec-dashboard-{}.log'.format(args.target_date))
    logger = setup_logger(log_filepath)
    
    for symbol in dict_company.keys():

        # print(symbol, args.target_date)
        args = args_updates(args, symbol, dict_company)

        # Data Collection & Processing
        if args.do_data_collection:
            logger.info(f'Collect SEC data -- {symbol} {args.target_date}')   
            scraper = SEC_Archive_Scraper(symbol = args.symbol, cik_number = args.cik_number, 
                                        company_name = args.company_name)
            parser = SEC_HTML_Parser(db_folder=args.symbol_path, marker_endpage = '-'*80)

            model_sec.explore_edgar(scraper=scraper, parser=parser, 
                                    logger=logger, args=args)

        # Tasks with LLMs
        if args.do_llm_tasks:
            logger.info(f'Perform reserved tasks with LLMs')    
            secdashboard = App_SEC_Dashboard(company_name = args.company_name, marker_endpage = '-'*80,
                                                db_folder=args.symbol_path, model_name = args.llm_modelname, 
                                                maxlen_llminput = args.llm_input_maxlen, temperature=args.llm_temperature)

            model_sec.run_tasks(tasks=secdashboard, logger=logger, args=args)










        
