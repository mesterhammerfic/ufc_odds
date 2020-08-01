import os
import sys

module_path = os.path.abspath(os.path.join(os.pardir))
if module_path not in sys.path:
    sys.path.append(module_path)

from bs4 import BeautifulSoup
import requests
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

#custom functions
from src import open_page as op
from src import local
from src import ufcstats



# import local postgres info
USER = local.user
PASS = local.password
HOST = local.host
PORT = local.port

#create engine
engine = create_engine(f'postgresql://{USER}:{PASS}@{HOST}:{PORT}/ufc_odds')

#load bookmarked list
bouts = pd.read_csv('../data/remaining_bouts.csv', index_col=0)

counter = 0

for bout_link in bouts['0']:
    print('--------------------------------')
    print(bout_link)
    print('--------------------------------')
    # open page
    bout_page = op.open_link(bout_link, async_=True)
    bout_soup = BeautifulSoup(bout_page)
    #check for tables
    if bout_soup.find_all('table'):
        #scrape bout table info
        bouts = ufcstats.scrape_bout_page(bout_soup, bout_link)
        bouts.to_sql('bouts', engine, if_exists='append', index=False)
        
        
        #get outcome info
        outcomes = bout_soup.find_all(class_='b-fight-details__person')
        outcomes = [outcome.find('i').get_text().strip() for outcome in outcomes]
        outcomes = ' '.join(outcomes)
        #get fighter links
        name_elems = bout_soup.find_all(class_='b-fight-details__person-name')
        fighter_links = [elem.find('a').get('href') for elem in name_elems]

        ## scrape round tables info
        list_of_tables = pd.read_html(bout_page)
        #strikes
        strikes = list_of_tables[3]
        strikes_0, strikes_1 = ufcstats.parse_strikes(strikes_df, fighter_links, outcomes, bout_link)
        #send to sql
        strikes_0.to_sql('strikes', engine, if_exists='append', index=False)
        strikes_1.to_sql('strikes', engine, if_exists='append', index=False)
        
        # general
        general = list_of_tables[1]
        general_0, general_1 = ufcstats.parse_general(general_df, fighter_links, outcomes, bout_link)
        #send to sql
        general_0.to_sql('general', engine, if_exists='append', index=False)
        general_1.to_sql('general', engine, if_exists='append', index=False)    
    
        #update counter
        counter+=1
        
    #update remaining events
    last_bout_index = bouts[bouts['0']==bout_link].index[0] #get index of last bout scraped
    bouts.loc[last_bout_index+1:].to_csv('../data/remaining_bouts.csv')