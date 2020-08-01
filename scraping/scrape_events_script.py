"""
Requrements:
- local.py file in the source folder.
        The local.py file must contain the user info for the local postgres database 
        including name, password, port, and host address

- remaining_events.csv in the data folder
        if running this script for the first time, the remaining_events.csv should be 
        the entire ufcstats_events.csv created in the 01_ufc_stats_event_search notebook.
        
Result:
Creates or appends (if the tables exist) the events tables in the 
local postgres database. 

An updated remaining_events.csv that contains all events that were not scraped in the 
previous sessions.

If this script throws an error, one can restart the script and it will continue populating 
the appropriate tables based on the remaining events csv.
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
remaining_events = pd.read_csv('../data/remaining_events.csv')


for event_link in remaining_events['0']:
    print('--------------------------------')
    print(event_link)
    print('--------------------------------')
    # open page
    event_page = op.open_link(event_link, async_=True)
    event_soup = BeautifulSoup(event_page)
    #check for tables
    events = ufcstats.event_scraper(event, event_link)
    events.to_sql('events', engine, if_exists='append', index=False)

    #update remaining events
    last_event_index = remaining_events[remaining_events['0']==event_link].index[0] #get index of last event scraped
    remaining_events.loc[last_event_index+1:].to_csv('../data/remaining_events.csv', index=False)