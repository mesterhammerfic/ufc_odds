from bs4 import BeautifulSoup
import pandas as pd
import requests
import numpy as np
import re

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'

"""
Secondary scraping functions
    Take either soup objects or html (in the form of request.get(link).content) 
    and return dataframes
"""

def get_ufc_events(html_content):
    """
    input: html of tapology events search results
    output: dataframe of events
    """
    #the following three lines will get the intitial dataframe that lacks links
    df_results = pd.read_html(html_content) #grab all tables and turn them into dataframes
    df_results = df_results[0] #grab the first dataframe in that list
    df_results = df_results.dropna(axis=1,how='all') #drop all rows with all null values    
    df_results.columns = ['event', 'name', 'date', 'bouts']#clean columns
    
    #now I will get the links
    soup = BeautifulSoup(html_content, 'html.parser')
    results_table = soup.find('table')
    links = get_event_links(results_table) #get the list of links
    df_results['link'] = links #add links to dataframe
    
    # now I will filter out all events that were cancelled, 
    # have not happened yet, or are not from the UFC
    df_results = keep_ufc_events_only(df_results)
    df_results = keep_previous_events_only(df_results)
    df_results = remove_cancelled_bouts(df_results)
    
    return df_results
    

def get_missing_event_info(event_soup, event_link):
    """
    takes the link to an event page and returns a dataframe with the info 
    that is not on the event dataframe by default.
    input: soup of event webage, event_link
    output: dataframe with missing info
    """
    div = event_soup.find(class_="details details_with_poster clearfix") #grab top header
    event_info_elem = div.find('ul') #grab first list in top header
    info_list = event_info_elem.get_text().split('\n\n\n')#turn it into text and split into list
    
    info_list = clean_info_list(info_list)
    
    info_df = info_list_to_df(info_list, event_link)
    info_df.columns = ['location', 'venue', 'enclosure', 'link', 'start_time']
    return info_df


def create_bouts_table(event_soup, event_link):
    """
    input: beautiful soup of the event page
    output: dataframe with list of bouts and links to the bout pages.
    """
    
    fightCard_element = event_soup.find(class_='fightCard')
    
    df_card = get_initial_bout_df(fightCard_element)
    df_card['link'] = get_links(fightCard_element)
    df_card['event_link'] = event_link
    
    return df_card

   
    
    
    
    
    
    
    
    
    
    
    
    
"""
Parsing functions
"""

def get_event_links(results_table):
    """
    input: a table element from a soup object
    output: a list of links for each result
    """
    rows = results_table.find_all('tr') #get all rows
    rows = rows[1:] #drop the header
    links = [row.find('a').get('href') for row in rows]
    return links

def keep_ufc_events_only(df_results):
    """
    input: dataframe of event search results
    output: dataframe with only ufc events
    """
    mask=df_results['event'].map(is_ufc)
    ufc_only = df_results[mask]
    ufc_only.reset_index()
    return ufc_only

def keep_previous_events_only(df_results):
    """
    input: dataframe of event search results
    output: dataframe with only events that were scheduled in the past
    """
    df_results['date'] = pd.to_datetime(df_results['date']) #make the date column a datetime object
    today = pd.to_datetime('today') #get today's date
    #get time delta for 1 day and subtract it from today
    yesterday = today - pd.to_timedelta(1, unit='days')
    
    mask=df_results['date'] < yesterday
    previous_events = df_results[mask]
    previous_events.reset_index()
    return previous_events

def remove_cancelled_bouts(df_results):
    """
    input: dataframe of event search results
    output: dataframe with only events that were not cancelled
    """
    mask=df_results['bouts'] > 0
    not_cancelled = df_results[mask]
    not_cancelled.reset_index()
    return not_cancelled

def clean_info_list(info_list):
    """
    input: info_list
    output: info_list with no empty elements
    """
    new_list = [] #fields with no info do not have a colon followed by a new line, so i will take those out
    for item in info_list:
        if ':\n' in item:
            new_list.append(item)
    info_list = '\n'.join(new_list).split('\n')
    clean_info_list = list(filter(lambda item: item != '', info_list))

    return clean_info_list

def info_list_to_df(info_list, event_link):
    """
    input: clean info_list
    output: dataFrame with: start_time, venue, location, enclosure and link
    """
    start_time = info_list.pop(0)#take date out from top of list
    info_list = group(info_list, 2) #group it into a list of 2 elem lists
    info_dict = dict(info_list) #turn 2d list into dictionary for the create_info_df function
    info_df = create_info_df(info_dict, start_time, event_link)
    return info_df

def create_info_df(info_dict, start_time, event_link):
    """
    Input: a dictionary made from the event info list, 
           a start time string, 
           and an event_link string
    Output: dataFrame with: start_time, venue, location, enclosure and link
    """
    info_df = pd.DataFrame(info_dict, index=[0]) #zipped the group into a dictionary, needs index param to work
    
    relevent_df = info_df.loc[:, ['Location:', 'Venue:', 'Enclosure:']] #remove all irrelevent data
    relevent_df['link'] = event_link
    relevent_df['start_time'] = start_time
    return relevent_df
    
def get_bout_df(fightCard_element):
    """
    input: html element with class 'fightCard'
    output: pandas dataframe of the fight card
    """
    df = get_initial_bout_df(fightCard_element)
    df['link'] = get_links(fightCard_element)
    return df

def get_initial_bout_df(fightCard_element):
    """
    input: html element with class 'fightCard'
    output: dataframe of fightcard with no links
    """
    bout_list = fightCard_element.get_text().split('\n') #get the fight card list and split it by the new lines
    bout_list = list(filter(lambda item: item != '', bout_list)) #filter out blank elements ('')
    initial_list = group(bout_list, 10) #make into 2d array with 10 columns
    
    df_card = pd.DataFrame(initial_list)
    
    df_card.columns = ['method', 
                       'length', 
                       'order', 
                       'fighter_1', 
                       'record_1',
                       'bout_type', 
                       'weight', 
                       'scheduled_rounds', 
                       'fighter_2', 
                       'record_2']
    return df_card

def get_bout_links(fightCard_element):
    """
    input: html element with class 'fightCard'
    output: list of links (strings) for each bout
    """
    bout_links = fightCard_element.find_all('a')
    bout_links = [a.get('href') for a in bout_links]
    links_by_bout = group(bout_links, 3)
    bout_links_only = [bout[1] for bout in links_by_bout]
    
    return bout_links_only












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

def open_tapology_link(link, user_agent = user_agent):
    url = 'https://www.tapology.com'+link
    headers = {'User-Agent': user_agent} #set user agent
    response = requests.get(url, headers=headers)
    return response.content

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