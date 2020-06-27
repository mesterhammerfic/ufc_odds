Tor is quite useful when you have to use requests without revealing your IP address, especially when you are web scraping. This tutorial will use a wrapper in python that helps you with the same.

What is TOR?
TOR is short for “The Onion Project”, a worldwide network of servers used by U.S. Navy. While enabling people to browse the internet anonymously, TOR also acts as a non-profit organization for research and development of online privacy tools.

TOR can mean two things

The software you install in your computer to run TOR
The network of computers that manages TOR connections
In simple words, TOR allows you to route your web traffic through several other computers so that a third person can’t trace the traffic back to a user. Anyone who tries to look up the traffic would see random untraceable nodes on TOR network.

Install TOR
TorRequest has TOR as a dependency. Install TOR first.

The instructions are for Ubuntu / Debian users. To install on windows or Mac, check here.

sudo apt-get update
sudo apt-get install tor
Restart the TOR service

sudo /etc/init.d/tor restart
Configure TOR
Let’s hash a new password so that random access to the port by outside agents is prevented.

tor --hash-password <enter your password here>
You will get a long combination of alphabets and numbers as your new hashed password. Now let’s go to the TOR configuration file (torrc) and make necessary changes.

Where the torrc file is placed depends on the operating system you use and where you are receiving tor from. Mine was at ./etc/tor/torrc .You can refer this to know more.

We have three things to do

Enable the “ControlPort” listener for TOR to listen on port 9051, as this is the port to which TOR will listen for any communication from applications talking to the Tor controller.
Update the hashed password
Implement cookie authentication
You can achieve this by uncommenting and editing the following lines just above the section for location hidden services.

SOCKSPort 9050
HashedControlPassword <your hashed passsword obtained earlier here>
CookieAuthentication 1

### This section is just for location-hidden services ###
Save and exit and restart TOR.

sudo /etc/init.d/tor restart
Now TOR is all set! Kudos!

What is TorRequest?
TorRequest is a wrapper around requests and stem libraries that allows making requests through TOR. View the project here.

You can install torrequest via PyPI:

pip install torrequest
Let’s try TorRequest. Open your python terminal.

from torrequest import TorRequest
Pass your password to Tor

tr=TorRequest(password='your_unhashed_password here')
Let’s check our current IP address

import requests
response= requests.get('http://ipecho.net/plain')
print ("My Original IP Address:",response.text)
My response was

My Original IP Address: 45.55.117.170
Let’s try the same through TorRequest

tr.reset_identity() #Reset Tor
response= tr.get('http://ipecho.net/plain')
print ("New Ip Address",response.text)
You will get a different IP address now. Reset Tor again to get a new IP address again.

Now you can easily mask your IP address in python using Torrequests.

All the best!