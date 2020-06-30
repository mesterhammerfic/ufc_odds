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
from src import scrape


bouts = pd.read_csv('../data/remaining_bouts.csv', index_col=0)


engine = create_engine('postgresql://postgres:abc@127.0.0.1:5432/ufc_odds')


for bout_link in bouts['0']:
    print('--------------------------------')
    print(bout_link)
    print('--------------------------------')
    last_bout = bouts[bouts['0'] == (bout_link)].index[0]
    remaining_bouts = bouts.loc[last_bout:]
    remaining_bouts.to_csv('../data/remaining_bouts.csv')

    # open page and parse tables with pd
    bout_page = op.open_link(bout_link, async_=True)
    list_of_tables = pd.read_html(bout_page)
    
    # Open page with beautiful soup and get outcomes info
    bout_soup = BeautifulSoup(bout_page)
    outcomes = bout_soup.find_all(class_='b-fight-details__person')
    outcomes = [outcome.find('i').get_text().strip() for outcome in outcomes]
    outcomes = ' '.join(outcomes)
    
    #get bout id from link
    bout_id = bout_link.split('/')[-1]

    
    ## Get tables and send to postgres
    #strikes
    strikes = list_of_tables[3]
    strikes = scrape.format_stats_table(strikes)

    strikes['bout_id'] = bout_id
    strikes['outcome'] = outcomes
    strikes = strikes.drop(labels = 'unnamed:_9_level_0', axis=1)
    strikes.to_sql('strikes', engine, if_exists='append', index=False)

    ## general

    general = list_of_tables[1]
    general = scrape.format_stats_table(general)

    general['bout_id'] = bout_id
    general['outcome'] = outcomes
    general.to_sql('general', engine, if_exists='append', index=False)
    
    
    



    