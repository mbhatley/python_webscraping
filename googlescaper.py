import pandas as pd
import bs4
import requests
import random
from random import randint
import time
import json
from helper_lists import user_agents

headers = {'User-Agent': random.choice(user_agents)}

with open('pink_slimes_dict.json', 'r') as file:
    pink_slimes_dict = json.load(file)

base_url = 'http://www.google.com/search?q='
data = []

for dict_key in list(pink_slimes_dict.keys())[0:150]: #slice to only collect sample of the data to avoid block
    # for dict_key in pink_slimes_dict.keys(): # used when running all keys in dict (may result in blocking)
    url = base_url + dict_key + 'politician'
    response = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(response.content, "html.parser")

    side_info = soup.find_all('div', class_='OOijTb P6Tjc gDQYEd')

    # Iterate over each side_info block
    for info in side_info:
        # Find all g-link elements within each side_info
        g_links = info.find_all('g-link')
        for g_link in g_links:
            # Extract href and text if available
            href = g_link.find('a')['href'] if g_link.find('a') else None
            text = g_link.find(class_='CtCigf').get_text() if g_link.find(class_='CtCigf') else None
            data.append({'Person': dict_key, 'Socials': text, 'URL': href})

        time.sleep(randint(25, 93)) #

df = pd.DataFrame(data)

df_wide = df.pivot(index='Person', columns='Socials', values='URL').reset_index()

df_wide.columns.name = None

print(df_wide)