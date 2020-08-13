import pandas as pd

"""
UFCStats.com Webscraping Functions

These functions are used in the scrape scripts found in the /scraping/ folder of this repository
"""


"""
===================================================================================
Bout page functions

Example of a bout page: http://www.ufcstats.com/fight-details/a2e34655a41ba45c
===================================================================================
"""
def scrape_bout_page(bout_soup, bout_link):
    """
    input: beautiful soup of a ufcstats fight details page
    output: a dataframe with all bout info, ready to be sent to sql database
    """
    #get event link
    title = bout_soup.find(class_='b-content__title')
    event_link = title.find('a').get('href')
    #get details
    details = parse_details(bout_soup)
    #get rest of fight info
    bouts = html_i_to_df(bout_soup, list_class="b-fight-details__text")
    bouts['details'] = details
    bouts['event_link'] = event_link
    bouts['link'] = bout_link
    return bouts

def parse_details(bout_soup):    
    """
    input: beautiful soup of a ufcstats fight details page
    output: a parsed string of the 'details' item
    """
    #get all detail items
    details_elem = bout_soup.find_all(class_='b-fight-details__text')[1]
    detail_items = details_elem.find_all('i', recursive=False)
    #remove whitespace
    detail_items = [item.get_text().split('\n') for item in detail_items]
    details = []
    for item in detail_items:
        cleaned = [part.strip() for part in item]
        details.append(''.join(cleaned))
    details = ''.join(details)
    #remove label
    details = details[8:]
    return details


def parse_strikes(strikes_df, fighter_links, outcomes, bout_link):
    """
    input dataframe with striking bout info from ufcstats
    """
    strikes = format_stats_table(strikes_df)   
    #add missing columns and clean up
    strikes['bout_link'] = bout_link
    strikes['outcome'] = outcomes
    strikes = strikes.drop(labels = 'unnamed:_9_level_0', axis=1)
    #split
    strikes_0 = strikes.applymap(lambda x: split(0, x))
    strikes_1 = strikes.applymap(lambda x: split(1, x))
    strikes_0['fighter_link'] = fighter_links[0]
    strikes_1['fighter_link'] = fighter_links[1]
    
    return strikes_0, strikes_1


def parse_general(general_df, fighter_links, outcomes, bout_link):
    """
    input dataframe with general bout info from ufcstats
    """
    general = format_stats_table(general_df)
    #add missing columns and clean up
    general['bout_id'] = bout_link
    general['outcome'] = outcomes
    general.columns = ['fighter', 'kd', 'sig_str', 'sig_str_prcnt', 'total_str', 'td_count',
                       'td_prcnt', 'sub_att', 'pass', 'rev', 'round', 'bout_id', 'outcome']
    #split
    general_0 = general.applymap(lambda x: split(0, x))
    general_1 = general.applymap(lambda x: split(1, x))
    general_0['fighter_link'] = fighter_links[0]
    general_1['fighter_link'] = fighter_links[1]
    
    return general_0, general_1


"""
===================================================================================
Event page functions

Example of an event page: http://www.ufcstats.com/event-details/bda04c573563cc2e
===================================================================================
"""
def event_scraper(event_soup, event_link):
    """
    input: beautiful soup object of the event page
    output: dataframe with all relevent info
    """
    info = html_li_to_df(event_soup, 'b-list__box-list', is_nested=False)
    info['name'] = event_soup.find(class_='b-content__title-highlight').get_text().strip()
    info['link'] = event_link
    return info


"""
===================================================================================
Fighter page functions

Fighter page example: http://www.ufcstats.com/fighter-details/d3df1add9d9a7efb
===================================================================================
"""
def fighter_scraper(fighter_soup, fighter_link):
    """
    input: beautiful soup object of the fighter page
    output: dataframe with all relevent info
    """
    info = html_li_to_df(fighter_soup, 'b-list__box-list', is_nested=False)
    info['name'] = fighter_soup.find(class_='b-content__title-highlight').get_text().strip()
    info['link'] = fighter_link
    return info


"""
===================================================================================
General functions
===================================================================================
"""
def split(fighter_index, value):
    """
    use this in an apply map function to get seperate fighters from a ufcstats table. 
    fighter_index: (int) specify which fighter (0: first, 1: second)
    """
    if type(value) != str:
        return value

    split_string = value.split(' ')
    length = len(split_string)
    if  length > 1:
        if fighter_index == 0:
            fighter_0_stats = split_string[:int(length/2)]
            return ' '.join(fighter_0_stats)
        elif fighter_index == 1:
            fighter_1_stats = split_string[int(length/2):]
            return ' '.join(fighter_1_stats)
    else:
        return value

def format_stats_table(df):
    """
    input: dataframe of stats table from ufc stats.com
    output: dataframe with column names fixed and round column added.
    """
    df['round'] = df.index+1

    new_columns = [column[0] for column in df.columns]
    new_columns = [column.strip() for column in new_columns]
    new_columns = [column.replace(' ', '_') for column in new_columns]
    new_columns = [column.replace('%', 'prcnt') for column in new_columns]
    new_columns = [column.replace('.', '') for column in new_columns]
    new_columns = [column.lower() for column in new_columns]
    df.columns = new_columns
    return df

def html_i_to_df(soup, list_class):
    """
    input: beautiful soup object, the class assigned to the list you are looking for.
    output: dataframe with values assigned to different items
    """

    ### Find the list element
    div = soup.find(class_=list_class) #grab top header
    event_info_elem = div
    
    ### Find the list items in the element
    html_list_items = event_info_elem.find_all('i', recursive=False)
    html_list_items = [item.get_text() for item in html_list_items]
    item_list = [item.split(':\n') for item in html_list_items]

    #Encapsulating the second element of each row in the list
    # allows them to be made into a dataframe easily
    item_list = [[item[0], [item[1]]] for item in item_list]


    ### Convert to dataframe
    list_df = pd.DataFrame(dict(item_list))

    # clean up white space
    list_df = list_df.applymap(lambda x: x.strip())
    list_df.columns = [(col.strip()).replace(' ', '') for col in list_df.columns]
    
    return list_df

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
