## ---------------------------------------------------------------------------
## Revisions:
## 0: 7-Aug-2026: Original Release
## ---------------------------------------------------------------------------

import pandas as pd
from datetime import timedelta, datetime
import bs4
import requests
import random
from random import randint
import time

from src.web_scrapers.static_info import user_agents


class LinkScraper:

    def __init__(self, start_date=None, end_date=None, start_page=None, end_page=None):
        """Initializes the scraper's date range, page range, and HTTP session.

        :param start_date: The earliest article date to scrape, as a
            date-parsable value. Defaults to yesterday.
        :param end_date: The latest article date to scrape, as a
            date-parsable value. Defaults to yesterday.
        :param start_page: The first pagination page to scrape. Defaults to 1.
        :param end_page: The last pagination page to scrape. Defaults to 3.
        :return: None.
        """
        self.headers = {'User-Agent': random.choice(user_agents)}
        self.session = requests.Session()

        if start_date is None:
            self.start_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            self.start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')

        if end_date is None:
            self.end_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            self.end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        if start_page is None:
            self.start_page = 1
        else:
            self.start_page = start_page

        if end_page is None:
            self.end_page = 3
        else:
            self.end_page = end_page

# ---------------------------------------------------------------------------
# 1. BeautifulSoup Scrappers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# a. CNN
# ---------------------------------------------------------------------------
    def cnn_links(self):
        """Scrapes CNN's monthly sitemap for article links within the instance's date range.

        :return: A DataFrame of date, source, href, and title columns for
            CNN articles, deduplicated by href and filtered to excluded
            sections (underscored, style, entertainment, games, media).
        """
        cnn_date, cnn_href, cnn_title = [], [], []

        base_url = 'https://www.cnn.com/sitemap/article/'

        month = self.start_date.month
        year = self.start_date.year

        url = f"{base_url}{year}/{month}"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.content, 'html.parser')

            articles = []
            items = soup.select('ul.sitemap__list li.sitemap__list-item')

            for item in items:
                # Extract date
                date_elem = item.select_one('span.sitemap__list-item__date')
                date = date_elem.text.strip() if date_elem else None

                # Extract link and title
                link_elem = item.select_one('a.sitemap__list-item__link')
                href = link_elem.get('href') if link_elem else None
                title = link_elem.text.strip() if link_elem else None

                cnn_date.append(date)
                cnn_href.append(href)
                cnn_title.append(title)

        else:
            print(f"Status code: {response.status_code}")

        time.sleep(randint(2, 7))

        links = pd.DataFrame({'date': cnn_date, "source": "cnn", 'href': cnn_href, 'title': cnn_title})

        exclude_pattern = r'/cnn-underscored/|/style/|/entertainment/|/games/|media\.cnn\.com'
        links = links[~links['href'].str.contains(exclude_pattern, na=False, regex=True)]

        links = links.sort_values(by='date', na_position='last')
        links = links.drop_duplicates(subset=['href'], keep='first').reset_index(drop=True)
        links['date'] = pd.to_datetime(links['date'])
        links[(links['date'] >= self.start_date) & (links['date'] <= self.end_date)]

        return links

# ---------------------------------------------------------------------------
# b. Hedge Week
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# c. Private Equity Wire
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# d. Techcrunch
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# e. CNBC
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# f. Mining.com
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# g. MongaBay
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# 2. Selenium Scrappers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# a. WSJ
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# b. Barrons
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# c. Fortune
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# d. The Information
# ---------------------------------------------------------------------------








