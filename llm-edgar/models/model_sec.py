

import os
import csv
import pandas as pd
from modules import SEC_Archive_Scraper, SEC_HTML_Parser 

def explore_edgar(scraper, parser, logger, args):
    
    # scrap sec data from SEC archive
    logger.info('\t' + '*'*8 + f' Exploring files of {args.symbol} '+'*'*8)       

    # loading previous sec data
    if os.path.isfile(args.sec_files_csvpath):
        prev_sec_files = pd.read_csv(args.sec_files_csvpath, delimiter='|')
    else:
        prev_sec_files = pd.DataFrame()

    logger.info('\t\tScrap file information in SEC archive')   
    sec_files = scraper.scrap(target_date = args.target_date, cnt_scrap_files = 300, 
                              prev_df = prev_sec_files)

    if len(sec_files) == 0:
        logger.info('\t\tThere is no valid files')   
        return

    logger.info('\t\tParse the scrapped html files')   
    sec_files = parser.parse(sec_files = sec_files, target_date = args.target_date)

    logger.info('\t\tUpdate SEC files')   
    new_sec_files = pd.concat([sec_files, prev_sec_files], axis=0, ignore_index=True)
    new_sec_files.to_csv(args.sec_files_csvpath, sep='|', index=False)

    return

def run_tasks(tasks, logger, args):

    logger.info('\t' + '*'*8 + f'Update SEC Dashboard for {args.symbol} '+'*'*8)  

    if os.path.isfile(args.sec_files_csvpath): 
        sec_files = pd.read_csv(args.sec_files_csvpath, delimiter='|')
        new_sec_files = sec_files[sec_files.loc[:,'used_in_dashboard']==False]
        if len(new_sec_files) == 0:
            logger.info('\t\tThere is no valid files')   
            return
    else:
        logger.info('\t\tThere is no valid files')  
        return

    logger.info('\t\tUpdate information for sec dashboard')  
    new_sec_files = new_sec_files.reset_index(drop=True)
    tasks.run(sec_files = new_sec_files)

    logger.info('\t\tUpdate SEC files as used')   
    sec_files.loc[sec_files['used_in_dashboard'] == False, 'used_in_dashboard'] = True
    sec_files.to_csv(args.sec_files_csvpath, sep='|', index=False)

    return