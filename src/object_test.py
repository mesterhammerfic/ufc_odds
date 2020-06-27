from bs4 import BeautifulSoup
import pandas as pd
import requests
import numpy as np
import re
from torrequest import TorRequest

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'

class table_scraper():
    """
    Contains a pandas DataFrame under the attribute 'table'. Specific scraping methods are added
    onto child classes defined below.
    """
    def __init__(self):
        self.table = pd.DataFrame()
        
    def export_csv(self, path):
        self.table.to_csv(path)
        
    def import_csv(self, path, index)
        """
        input: path to file and the name of the index column
        output: no return, assigns imported csv to class's 'table' attribute.
        """
        self.table = pd.read_csv(path, index_col)
        

"""
===========================================================================================================
Tapology scraping functions
    Take either soup objects or html (in the form of request.get(link).content) 
    and return dataframes
===========================================================================================================
"""

class events(table_scraper):
    """
    An instance of this class starts with an empty dataframe. The dataframe can be
    populated with the create import methods.
    """ 
    def create_table(self, html_content):
        """
        input: Search for an event on the tapology page
        output: dataframe of events
        """
        #the following three lines will get the intitial dataframe that lacks links
        events_df = pd.read_html(html_content) #grab all tables and turn them into dataframes
        events_df = events_df[0] #grab the first dataframe in that list
        events_df = events_df.dropna(axis=1,how='all') #drop all rows with all null values    
        events_df.columns = ['event', 'name', 'date', 'bouts']#clean columns

        #now I will get the links
        soup = BeautifulSoup(html_content, 'html.parser')
        results_table = soup.find('table')
        events_df['link'] = self.get_event_links(results_table) #add links to dataframe

        # now I will filter out all events that are not from the UFC, 
        # have not happened yet, or were cancelled
        events_df = self.keep_ufc_events_only(events_df)
        events_df = self.keep_previous_events_only(events_df)
        events_df = self.remove_cancelled_events(events_df)

        events_df = events_df.set_index('link')
        self.table = self.table.combine_first(events_df)
        
        return None
    
    
        
    """
    Parsing functions
    """
    def get_event_links(self, results_table):
        """
        input: a table element from a soup object
        output: a list of links for each result
        """
        rows = results_table.find_all('tr') #get all rows
        rows = rows[1:] #drop the header
        links = [row.find('a').get('href') for row in rows]
        return links

    def keep_ufc_events_only(self, events_df):
        """
        input: dataframe of event search results
        output: dataframe with only ufc events
        """
        mask=events_df['event'].map(is_ufc)
        ufc_only = events_df[mask]
        ufc_only.reset_index()
        return ufc_only

    def keep_previous_events_only(self, events_df):
        """
        input: dataframe of event search results
        output: dataframe with only events that were scheduled in the past
        """
        events_df['date'] = pd.to_datetime(events_df['date']) #make the date column a datetime object
        today = pd.to_datetime('today') #get today's date
        #get time delta for 1 day and subtract it from today
        yesterday = today - pd.to_timedelta(1, unit='days')

        mask=events_df['date'] < yesterday
        previous_events = events_df[mask]
        previous_events.reset_index()
        return previous_events

    def remove_cancelled_events(self, events_df):
        """
        input: dataframe of event search results
        output: dataframe with only events that were not cancelled
        """
        mask=events_df['bouts'] > 0
        not_cancelled = events_df[mask]
        not_cancelled.reset_index()
        return not_cancelled
    
    

    """
    The previous function does not contain all event info simply because
    that info is not available on the search page. In order to add that info
    to the events dataframe, I have to grab it from the page dedicated to that 
    specific event. The following functions will allow me to create a datframe 
    with the same link so that it can be joined to the original events dataframe.
    """    

    def get_missing_event_info(self, event_soup, event_link):
        """
        takes the link to an event page and returns a dataframe with the info 
        that is not on the event dataframe by default.
        input: soup of event webage, event_link
        output: dataframe with missing info
        """

        df = html_li_to_df(event_soup, "details details_with_poster clearfix", has_header=True)
        df = df.loc[:,['Location', 'Enclosure', 'Venue', 'header']]
        df['link'] = event_link

        return df.set_index('link')
    
    def update_missing_info(self, event_soup, event_link):
        missing_info = self.get_missing_event_info(event_soup, event_link)
        self.table = self.table.combine_first(missing_info)
        return

"""
===========================================================================================================
===========================================================================================================
"""

class bouts(table_scraper):
    def add_to_table(self, event_soup, event_link):
        temp_table = self.get_bouts_table(event_soup, event_link)
        self.table = pd.concat([self.table, temp_table], join='inner')
    
    def create_table(self, event_soup, event_link):
        """
        input: beautiful soup of the event page
        output: dataframe with list of bouts and links to the bout pages.
        """
        self.table = self.get_bouts_table(event_soup, event_link)
        
    def get_bouts_table(self, event_soup, event_link):
        """
        input: beautiful soup of the event page
        output: dataframe with list of bouts and links to the bout pages.
        """
        #here's a table that will be ready to populate
        df = pd.DataFrame()
        
        bout_info = event_soup.find(class_='fightCard')
        li_bouts = bout_info.find_all('div', class_='fightCardBout')
        for bout in li_bouts:
            bout_dict = {}
            
            names = bout.find_all(class_='fightCardFighterName')
            bout_dict['fighter_0'] = [names[0].get_text()]
            bout_dict['fighter_1'] = [names[1].get_text()]
            if bout.find(class_='result'):
                bout_dict['method'] = [bout.find(class_='result').get_text()]
                
            if bout.find(class_='time'):
                bout_dict['time'] = [bout.find(class_='time').get_text()]
                
            if bout.find(class_='weight'):
                bout_dict['weight'] = [bout.find(class_='weight').get_text()]
                
            if bout.find(class_='billing'):
                bout_dict['billing'] = [bout.find(class_='billing').get_text()]
                
            if bout.find(class_='fightCardBoutNumber'):
                bout_dict['bout_number'] = [bout.find(class_='fightCardBoutNumber').get_text()]
                
            if bout.find(class_='billing'):
                bout_dict['link'] = [bout.find(class_='billing')\
                                     .find('a')\
                                     .get('href')]
                
            bout_dict['event_link'] = [event_link]

            # now I can update my df with this info by turning it into a df and using combine first
            bout_df = pd.DataFrame(bout_dict)
            df = pd.concat([df, bout_df])
            
        df = df.applymap(lambda x: x.strip() if type(x)==str else x)
        return df.set_index('link')
    

    """
    Parsing functions
    """

    def update_missing_info(self, bout_soup, bout_link):
        missing_info = self.get_missing_bout_info(bout_soup, bout_link)
        self.table = self.table.combine_first(missing_info)
        
    
    def get_missing_bout_info(self, bout_soup, bout_link):
        """
        takes the link to an event page and returns a dataframe with the info 
        that is not on the event dataframe by default.
        input: soup of event webage, event_link
        output: dataframe with missing info
        """
        list_class="details details_with_poster clearfix"
        info_df = html_li_to_df(bout_soup, list_class, has_header=True)
        relevent_df = info_df.loc[:, ['Referee', 'Pro/Am']]
        relevent_df['link'] = bout_link
        
        #get ufcstats link
        table = bout_soup.find(class_= list_class)
        if table:    
            icon_elem = table.find(alt='Ufc stats')
            stats_link=icon_elem.parent.parent.get('href')
            relevent_df['ufc_stats'] = stats_link
        
        return relevent_df.set_index('link')
    
    


    


"""
===========================================================================================================
===========================================================================================================
"""

class fighter_instances(table_scraper):
    def add_to_table(self, html_content, bout_link):
        temp_table = self.get_fighter_instances_table(html_content, bout_link)
        self.table = pd.concat([self.table, temp_table], join='inner')
    
    def create_table(self, html_content, bout_link):
        """
        input: beautiful soup of the event page
        output: dataframe with list of bouts and links to the bout pages.
        """
        self.table = self.get_fighter_instances_table(html_content, bout_link)
        
        
    def get_fighter_instances_table(self, html_content, bout_link):
        """
        input: html of the bout page
        output: dataframe with one row for each fighter in the bout.
        """
        tables = pd.read_html(html_content)
        #i'm going to grab the first table but it needs to be pivoted
        initial_df = tables[0]
        fighter_inst_df = self.pivot_instance_table(initial_df)

        #now I need to grab the links
        fighter_inst_df['fighter_link'] = self.get_instance_links(html_content)

        #here I add the bout links
        fighter_inst_df['bout_link'] = bout_link

        #Here I create a unique id for all the fighter instances
        fighter_inst_df['instance_id'] = fighter_inst_df['bout_link'] + fighter_inst_df['fighter_link']
        fighter_inst_df = fighter_inst_df.set_index('instance_id')
        
        return self.table.combine_first(fighter_inst_df)

    """
    Parsing functions
    """
    def pivot_instance_table(self, initial_df):
        """
        input: initial dataframe taken from a bout page
        ouptut: dataframe tilted 90 degrees with columns 0 and 4 
                as the rows and column 2 as the column names
        """
        fighter_inst_df = pd.DataFrame([list(initial_df[0]), list(initial_df[4])])
        fighter_inst_df.columns = list(initial_df[2])
        return fighter_inst_df

    def get_instance_links(self, html_content):
        bout_soup = BeautifulSoup(html_content, 'html.parser')
        name_elem = bout_soup.find(class_="fighterNames botPad clearfix")
        name_elem = name_elem.find_all('a')
        links = [name.get('href') for name in name_elem]
        return links




"""
===========================================================================================================
===========================================================================================================
"""
class fighters(table_scraper):
    def add_to_table(self, fighter_soup, fighter_link):
        temp_table = self.get_fighters_table(fighter_soup, fighter_link)
        self.table = pd.concat([self.table, temp_table], join='inner')
    
    def create_table(self, fighter_soup, fighter_link):
        """
        input: beautiful soup of the event page
        output: dataframe with list of bouts and links to the bout pages.
        """
        self.table = self.get_fighters_table(fighter_soup, fighter_link)
        
    def get_fighters_table(self, fighter_soup, fighter_link):
        """
        input: beautiful soup of the fighter page
        output: dataframe with fighter info.
        """
        df = html_li_to_df(fighter_soup, 'details details_two_columns')
        df['link'] = fighter_link
        df.set_index('link')
        
        return self.table.combine_first(df)
    
        
        

"""
===========================================================================================================
helper functions
===========================================================================================================
"""
def group(a, group_size):
    '''
    input: 1d array
    output: 2d array where group size is the number of columns
    '''
    final_list = []
    for index in range(int(len(a)/group_size)):
        final_list.append(a[index*group_size:index*group_size+group_size])
    return final_list


def is_ufc(event_name):
    """
    input: String of event name
    output: True if the event has UFC or Contender at beginning, otherwise false
    """
    
    ufc = re.compile('^UFC') #matches the start of the string with UFC
    contender = re.compile('^Contender')
    if ufc.match(event_name) or contender.match(event_name):
        return True
    else:
        return False


def html_li_to_df(soup, list_class, has_header=False, is_nested=True):
    """
    input: beautiful soup object, the class assigned to the list you are looking for.
    output: dataframe with values assigned to different items
    
    params:
    has_header means that the list has useful information as the first li elemtn
    
    is_nested=True means there is a <ul> element nested inside the list_class element.
    if False, take <li> straight from list_class element.
    """

    ### Find the list element
    div = soup.find(class_=list_class) #grab top header
    if is_nested:
        event_info_elem = div.find('ul') #grab first list in top header
    else:
        event_info_elem = div
    
    ### Find the list items in the element
    html_list_items = event_info_elem.find_all('li')
    html_list_items = [item.get_text() for item in html_list_items]
    html_list_items

    #Some rows in the list have two attributes separated by a '|', here we split them
    column_value_strings = []
    for row in html_list_items:
        if '\n|' in row:
            column_value_strings+=row.split('\n|')
        else:
            column_value_strings.append(row)
    
    item_list = [item.split(':\n') for item in column_value_strings]
    ### Insert a 'header' label. The info in the header may be useful later on
    if has_header:
        item_list[0].insert(0, 'header')
        
    #Encapsulating the second element of each row in the list
    # allows them to be made into a dataframe easily
    item_list = [[item[0], [item[1]]] for item in item_list]


    ### Convert to dataframe
    list_df = pd.DataFrame(dict(item_list))

    # clean up white space
    list_df = list_df.applymap(lambda x: x.strip())
    list_df.columns = [(col.strip()).replace(' ', '') for col in list_df.columns]
    
    return list_df


