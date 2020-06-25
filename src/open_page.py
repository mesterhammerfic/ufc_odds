from bs4 import BeautifulSoup
import requests
import numpy as np
from torrequest import TorRequest
from fake_useragent import UserAgent


#log in to tor
tr=TorRequest(password='8453')

#set user agent object
ua = UserAgent()



def get_user_agent(user_agent_list):
    return np.random.choice(user_agent_list)


def open_tapology_link(link, reset=True, async_=True):
    """
    input: the portion of a tapology webpage url after 'tapology.com'
    output: html content
    """
    url = 'https://www.tapology.com'+link
    #set user agent
    headers = {'User-Agent': ua.random}
    
    if reset:
        if async_:
            tr=TorRequest(password='8453')
            tr.reset_identity_async() #Reset Tor
            response = tr.get(url, headers=headers)
        else:
            tr=TorRequest(password='8453')
            tr.reset_identity() #Reset Tor
            response = tr.get(url, headers=headers)
    else:
        response = tr.get(url, headers=headers)
    
    return response.content
