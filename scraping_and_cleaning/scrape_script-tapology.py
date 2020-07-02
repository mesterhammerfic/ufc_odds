import os
import sys

module_path = os.path.abspath(os.path.join(os.pardir))
if module_path not in sys.path:
    sys.path.append(module_path)

from bs4 import BeautifulSoup
import requests
import pandas as pd
import src
from src import object_test
from src import open_page as op

import psycopg2
from sqlalchemy import create_engine

from src import local
from src import ufcstats


bouts = pd.read_csv('../data/remaining_bouts.csv', index_col=0)


counter = 0

for bout_link in bouts['0']:
    print('--------------------------------')
    print(bout_link)
    print('--------------------------------')

    # open page
    bout_page = op.open_link(bout_link, async_=True)

    #update remaining events
    last_bout_index = bouts[bouts['0']==bout_link].index[0]
    bouts.loc[last_bout_index:].to_csv('../data/remaining_bouts.csv')
    
    #check for tables
    bout_soup = BeautifulSoup(bout_page)
    if bout_soup.find_all('table'):
        list_of_tables = pd.read_html(bout_page)
        
        #get outcome info
        outcomes = bout_soup.find_all(class_='b-fight-details__person')
        outcomes = [outcome.find('i').get_text().strip() for outcome in outcomes]
        outcomes = ' '.join(outcomes)

        #get bout id from link
        bout_id = bout_link.split('/')[-1]

        
        ## Get tables
        
        #strikes
        strikes = list_of_tables[3]
        strikes = ufcstats.format_stats_table(strikes)
        
        #add missing columns and clean up
        strikes['bout_id'] = bout_id
        strikes['outcome'] = outcomes
        strikes = strikes.drop(labels = 'unnamed:_9_level_0', axis=1)
        #split and send to postgres
        strikes_0 = strikes.applymap(lambda x: ufcstats.split(0, x))
        strikes_1 = strikes.applymap(lambda x: ufcstats.split(1, x))
        strikes_0.to_sql('strikes', engine, if_exists='append', index=False)
        strikes_1.to_sql('strikes', engine, if_exists='append', index=False)
        
        # general
        general = list_of_tables[1]
        general = ufcstats.format_stats_table(general)
        
        #add missing columns and clean up
        general['bout_id'] = bout_id
        general['outcome'] = outcomes
        general.columns = ['fighter', 'kd', 'sig_str', 'sig_str_prcnt', 'total_str', 'td_count',
               'td_prcnt', 'sub_att', 'pass', 'rev', 'round', 'bout_id', 'outcome']
        #split and send to postgres
        general_0 = general.applymap(lambda x: ufcstats.split(0, x))
        general_1 = general.applymap(lambda x: ufcstats.split(1, x))
        general_0.to_sql('general', engine, if_exists='append', index=False)
        general_1.to_sql('general', engine, if_exists='append', index=False)    
    
    
        counter+=1


    