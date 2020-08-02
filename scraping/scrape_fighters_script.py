"""
Requrements:
- local.py file in the source folder.
        The local.py file must contain the user info for the local postgres database 
        including name, password, port, and host address

- remaining_fighters.csv in the data folder
        if running this script for the first time, the remaining_fighters.csv should be 
        the entire ufcstats_fighters.csv created in the 01_ufc_stats_fighter_search notebook.
        
Result:
Creates or appends (if the tables exist) the fighters tables in the 
local postgres database. 

An updated remaining_fighters.csv that contains all fighters that were not scraped in the 
previous sessions.

If this script throws an error, one can restart the script and it will continue populating 
the appropriate tables based on the remaining fighters csv.
"""



import os
import sys

module_path = os.path.abspath(os.path.join(os.pardir))
if module_path not in sys.path:
    sys.path.append(module_path)

from bs4 import BeautifulSoup
import pandas as pd
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
remaining_fighters = pd.read_csv('../data/remaining_fighters.csv')


for fighter_link in remaining_fighters['0']:
    print('--------------------------------')
    print(fighter_link)
    print('--------------------------------')
    # open page
    try:
        fighter_page = op.open_link(fighter_link, async_=True)
    except ConnectionError as e:
        print(e)
        fighter_page = op.open_link(fighter_link, async_=False)
        
    fighter_soup = BeautifulSoup(fighter_page)
    #check for tables
    fighters = ufcstats.fighter_scraper(fighter_soup, fighter_link)
    fighters.to_sql('fighters', engine, if_exists='append', index=False)

    #update remaining fighters
    last_fighter_index = remaining_fighters[remaining_fighters['0']==fighter_link].index[0] #get index of last fighter scraped
    remaining_fighters.loc[last_fighter_index+1:].to_csv('../data/remaining_fighters.csv', index=False)