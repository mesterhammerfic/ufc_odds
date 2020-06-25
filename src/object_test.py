from bs4 import BeautifulSoup
import pandas as pd
import requests
import numpy as np
import re
from torrequest import TorRequest

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'

"""
Tapology scraping functions
    Take either soup objects or html (in the form of request.get(link).content) 
    and return dataframes
"""
class events:
    """
    An instance of this class starts with an empty dataframe. The dataframe can be
    populated with the create or update methods.
    """
    def __init__(self):
        self.table = pd.DataFrame()
        
    def create_events_df(self, html_content):
        """
        input: html of tapology events search results
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

        self.table = self.table.combine_first(events_df.reset_index())
        
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
        df['link'] = event_link

        df = df.loc[:,['Location', 'Enclosure', 'Venue', 'header']]
        return df
    
    def update_missing_info(self, event_soup, event_link):
        missing_info = self.get_missing_event_info(event_soup, event_link)
        self.table = self.table.combine_first(missing_info)
        return

"""
===========================================================================================================
===========================================================================================================
"""

class bouts:
    def __init__(self):
        self.table = pd.DataFrame()
    
    def create_temp_bouts_table(self, event_soup, event_link):
        """
        input: beautiful soup of the event page
        output: dataframe with list of bouts and links to the bout pages.
        """

        fightCard_element = event_soup.find(class_='fightCard')

        bouts_df = self.get_initial_bouts_df(fightCard_element)
        bouts_df['link'] = self.get_bouts_links(fightCard_element)
        bouts_df['event_link'] = event_link

        self.temp_table = bouts_df
        return
    
    def create_bouts_table(self, event_soup, event_link):
        """
        input: beautiful soup of the event page
        output: dataframe with list of bouts and links to the bout pages.
        """

        fightCard_element = event_soup.find(class_='fightCard')

        bouts_df = self.get_initial_bouts_df(fightCard_element)
        bouts_df['link'] = self.get_bouts_links(fightCard_element)
        bouts_df['event_link'] = event_link

        self.table = self.table.combine_first(bouts_df)
        return
    """
    Parsing functions
    """
    def get_initial_bouts_df(self, fightCard_element):
        """
        input: html element with class 'fightCard'
        output: dataframe of fightcard with no links
        """
        bout_list = fightCard_element.get_text().split('\n') #get the fight card list and split it by the new lines
        bout_list = list(filter(lambda item: item != '', bout_list)) #filter out blank elements ('')
        initial_list = group(bout_list, 10) #make into 2d array with 10 columns

        bouts_df = pd.DataFrame(initial_list)

        bouts_df.columns = ['method', 
                           'length', 
                           'order', 
                           'fighter_0', 
                           'record_0',
                           'bout_type', 
                           'weight_class', 
                           'scheduled_rounds', 
                           'fighter_1', 
                           'record_1']
        bouts_df = bouts_df.drop(labels=['record_0', 'record_1'], axis=1) #removing record info
        return bouts_df

    def get_bouts_links(self, fightCard_element):
        """
        input: html element with class 'fightCard'
        output: list of links (strings) for each bout
        """
        bouts_links = fightCard_element.find_all('a')
        bouts_links = [a.get('href') for a in bouts_links]
        links_by_bout = group(bouts_links, 3)
        bouts_links = [bout[1] for bout in links_by_bout]

        return bouts_links

    def get_missing_bout_info(self, bout_soup, bout_link):
        """
        takes the link to an event page and returns a dataframe with the info 
        that is not on the event dataframe by default.
        input: soup of event webage, event_link
        output: dataframe with missing info
        """
        class_="details details_with_poster clearfix"
        info_df = html_li_to_df(bout_soup, class_, has_header=False)
        relevent_df = info_df.loc[:, ['Referee', 'Pro/Am']]
        relevent_df['link'] = bout_link
        return relevent_df

    def update_missing_info(self, bout_soup, bout_link):
        missing_info = self.get_missing_bout_info(bout_soup, bout_link)
        self.table = self.table.combine_first(missing_info)
        return None
    
    def update_missing_temp_info(self, bout_soup, bout_link):
        missing_info = self.get_missing_bout_info(bout_soup, bout_link)
        self.table = self.table.combine_first(missing_info)
        return None
    
    def combine_tables(self):
        self.table = pd.concat([self.table, self.temp_table])
    


"""
===========================================================================================================
===========================================================================================================
"""

class fighter_instances:
    def __init__(self):
        self.table = pd.DataFrame({'Pro Record At Fight': [],
                                 'Record After Fight': [],
                                 'Betting Odds': [],
                                 'Nationality': [],
                                 'Fighting out of': [],
                                 'Age at Fight': [],
                                 'Weigh-In Result': [],
                                 'Height': [],
                                 'Reach': [],
                                 'Gym': [],
                                 'fighter_link': [],
                                 'bout_link': [],
                                 'instance_id': []})
        
    def create_fighter_instances_table(self, html_content, bout_link):
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

        self.table = self.table.combine_first(fighter_inst_df)

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
class fighters:
    def __init__(self):
        self.table = pd.DataFrame()
        
    def create_fighters_table(self, fighter_soup, fighter_link):
        """
        input: beautiful soup of the fighter page
        output: dataframe with fighter info.
        """
        df = html_li_to_df(fighter_soup, 'details details_two_columns')
        df['link'] = fighter_link
        self.table = self.table.combine_first(df)

    """
    Parsing functions
    """



"""
===========================================================================================================
===========================================================================================================
"""

"""
helper functions
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


def html_li_to_df(soup, list_class, has_header=False):
    """
    input: beautiful soup object, the class assigned to the list you are looking for.
    output: dataframe with values assigned to different items
    """

    ### Find the list element

    div = soup.find(class_=list_class) #grab top header
    event_info_elem = div.find('ul') #grab first list in top header

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
    ### Insert a 'header' label.
    #### The info in the header may be useful later on
    if has_header:
        item_list[0].insert(0, 'header')

    ### Encapsulate the second element of each row in a list
    #### This allows them to be made into a dataframe easily
    item_list = [[item[0], [item[1]]] for item in item_list]


    ### Convert to dataframe
    list_df = pd.DataFrame(dict(item_list))

    # clean up white space
    list_df = list_df.applymap(lambda x: x.strip())
    list_df.columns = [(col.strip()).replace(' ', '') for col in list_df.columns]
    
    return list_df




"""
===========================================================================================================
Old, will be removed and replaced with new list parser found above
===========================================================================================================
"""

def html_list_to_df(info_elem):
    """
    input: info element from tapology. Should be a <ul> element
    output: dataframe version of the list where the header of the dataframe becomes
            the first column
    """
    info_list = to_info_list(info_elem)
    info_dict = to_info_dict(info_list)
    info_df = to_info_df(info_dict)
    return info_df

def to_info_list(info_elem):
    """
    input: info_list
    output: info_list with no empty elements
    """
    info_list = info_elem.get_text().split('\n\n\n')#turn it into text and split into list
    new_list = [] 
    for item in info_list:
        #fields with no info do not have a colon followed by a new line, so i will take those out
        if ':\n' in item: 
            new_list.append(item)   
    #this creates a list with the info separated by empty string elements
    info_list = '\n\n\n'.join(new_list).split('\n\n\n') 
    #this removes those empty string elements
    info_list = list(filter(lambda item: item != '', info_list)) 
    return info_list

def to_info_dict(info_list):
    """
    input: clean info_list
    output: dictionary version of the info list
    """
    #take first element out from top of list
    info_list=info_list
    first_elem = info_list.pop(0)
    #group it into a list of 2 elem lists
    info_list = [elem.split(':\n') for elem in info_list]
    #turn 2d list into dictionary for the create_info_df function
    info_dict = dict(info_list) 
    #now I want to add the first element back on
    info_dict['first_elem'] = first_elem
    return info_dict

def to_info_df(info_dict):
    """
    Input: a dictionary made from an info dict 
    Output: dataFrame 
    """
    info_df = pd.DataFrame(info_dict, index=[0]) #zipped the group into a dictionary, needs index param to work
    return info_df

