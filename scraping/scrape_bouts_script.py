"""
Requrements:
- local.py file in the source folder.
        The local.py file must contain the user info for the local postgres database 
        including name, password, port, and host address

- remaining_bouts.csv in the data folder
        if running this script for the first time, the remaining_bouts.csv should be 
        the entire ufcstats.bouts.csv created in the 01_ufc_stats_event_search notebook.
        
Result:
Creates or appends (if the tables exist) the strikes, general, and bouts tables in the 
local postgres database. 

An updated remaining_bouts.csv that contains all bouts that were not scraped in the 
previous sessions.

If this script throws an error, one can restart the script and it will continue populating 
the appropriate tables based on the remaining bouts csv.
"""



import os
import sys

module_path = os.path.abspath(os.path.join(os.pardir))
if module_path not in sys.path:
    sys.path.append(module_path)

from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from requests.exceptions import ConnectionError
import time

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
remaining_bouts= pd.read_csv('../data/remaining_bouts.csv')


for bout_link in remaining_bouts['0']:
    print('--------------------------------')
    print(bout_link)
    print('--------------------------------')
    # open page
    try:
        bout_page = op.open_link(bout_link, async_=True)
    except ConnectionError as e:
        print(e)
        time.sleep(60)
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
        try:
            fighter_links = [elem.find('a').get('href') for elem in name_elems]
        except AttributeError:
            fighter_links = []
            for elem in name_elems:
                if elem.find('a'):
                    fighter_links.append((elem.find('a').get('href')))
                else:
                    fighter_links.append('no_link')
        ## scrape round tables info
        list_of_tables = pd.read_html(bout_page)
        #strikes
        strikes = list_of_tables[3]
        strikes_0, strikes_1 = ufcstats.parse_strikes(strikes, fighter_links, outcomes, bout_link)
        #send to sql
        strikes_0.to_sql('strikes', engine, if_exists='append', index=False)
        strikes_1.to_sql('strikes', engine, if_exists='append', index=False)
        
        # general
        general = list_of_tables[1]
        general_0, general_1 = ufcstats.parse_general(general, fighter_links, outcomes, bout_link)
        #send to sql
        general_0.to_sql('general', engine, if_exists='append', index=False)
        general_1.to_sql('general', engine, if_exists='append', index=False)    


    #update remaining events
    last_bout_index = remaining_bouts[remaining_bouts['0']==bout_link].index[0] #get index of last bout scraped
    remaining_bouts.loc[last_bout_index+1:].to_csv('../data/remaining_bouts.csv', index=False)