

import os
import csv
import pandas as pd
from modules import SEC_Archive_Scraper, SEC_HTML_Parser 

def explore_edgar(scraper, parser, logger, args):
    
    # scrap sec data from SEC archive
    logger.info('*'*8 + f' Exploring files for {args.symbol} '+'*'*8)       

    # loading previous sec data
    if os.path.isfile(args.sec_files_csvpath):
        prev_sec_files = pd.read_csv(args.sec_files_csvpath, delimiter='|')
    else:
        prev_sec_files = pd.DataFrame()

    logger.info(f'\tScrap file information in SEC archive')   
    sec_files = scraper.scrap(target_date = args.target_date, cnt_scrap_files = 20, 
                              prev_df = prev_sec_files)
  
    if len(sec_files) == 0:
        logger.info(f'\tThere is no valid files')   
        return

    logger.info(f'\tParse the scrapped html files')   
    sec_files = parser.parse(sec_files = sec_files, target_date = args.target_date)

    # update and save
    new_sec_files = pd.concat([sec_files, prev_sec_files], axis=0, ignore_index=True)
    new_sec_files.to_csv(args.sec_files_csvpath, sep='|', index=False)


