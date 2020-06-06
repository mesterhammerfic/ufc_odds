from bs4 import BeautifulSoup
import pandas as pd
import requests

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'


def find_missing_event_data(soup, event_link)
    div = soup.find(class_="details details_with_poster clearfix") #grab top header
    event_info_elem = div.find('ul') #grab first list in top header

    info_list = event_info_elem.get_text().split('\n\n\n')#turn it into text and split into list


    new_list = [] #fields with no info do not have a colon followed by a new line, so i will take those out
    for item in info_list:
        if ':\n' in item:
            new_list.append(item)

    info_list = '\n'.join(new_list).split('\n')
    info_list


def create_bouts_table(soup, event_link):
    """
    input: beautiful soup of the event page
    output: dataframe with list of bouts and links to the bout pages.
    """
    
    fightCard_element = soup.find(class_='fightCard')
    
    df_card = get_initial_bout_df(fightCard_element)
    df_card['link'] = get_links(fightCard_element)
    df_card['event_link'] = event_link
    
    return df_card

    
"""
Parsing functions
"""

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

def get_links(fightCard_element):
    """
    input: html element with class 'fightCard'
    output: list of links (strings) for each bout
    """
    bout_links = fightCard_element.find_all('a')
    bout_links = [a.get('href') for a in bout_links]
    links_by_match = group(bout_links, 3)
    match_links_only = [match[1] for match in links_by_match]
    
    return match_links_only
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