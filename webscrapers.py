import pandas as pd
from datetime import timedelta, datetime
import bs4
import requests
import random
from random import randint
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.options import Options
from helper_lists import user_agents, chromeDriverPath


class WebScraper:

    def __init__(self, start_date=None, end_date=None, start_page=None, end_page=None):
        self.headers = {'User-Agent': random.choice(user_agents)}
        self.driver = chromeDriverPath
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

    # BeautifulSoup Scrapers:

    def techcrunch_links(self):
        """
        Function to extract the URLs from TechCrunch
        :return: DataFrame with Source, Date, Article Title and Article URL
        """

        original_start_date = self.start_date
        article_dates, article_titles, article_hrefs = [], [], []
        while self.start_date <= self.end_date:

            base_url = 'https://techcrunch.com/'
            the_date = self.start_date
            the_date = pd.to_datetime(the_date).strftime("%Y/%m/%d")
            url = base_url + the_date

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")
                for tag in soup.find_all("h2", {
                    "class": "has-link-color wp-block-post-title has-h-5-font-size "
                             "wp-elements-565fa7bab0152bfdca0217543865c205"}):
                    tag_header = tag.find("a")

                    article_date = the_date
                    article_title = tag_header.get_text(strip=True)
                    article_href = tag_header["href"]

                    article_dates.append(article_date)
                    article_titles.append(article_title)
                    article_hrefs.append(article_href)

            # move to the next day in the sequence until end_date is met
            self.start_date = pd.to_datetime(self.start_date) + timedelta(days=1)

            self.start_date = self.start_date.strftime('%Y-%m-%d')

            # pause program to not hit servers to quickly
            time.sleep(randint(2, 5))

        tc_links = pd.DataFrame({"date": article_dates, "source": "TechCrunch",
                                 "href": article_hrefs, "title": article_titles})

        tc_links = tc_links.drop_duplicates()

        tc_links['date'] = pd.to_datetime(tc_links['date'])

        # Reset start date to the original start date for the next scraper
        self.start_date = original_start_date

        return tc_links

    def techcrunch_contents(self, df, colname):
        """
        Function to scrape article contents from TechCrunch
        :param df: DataFrame created from `tech_crunch_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """

        article_contents, article_hrefs = [], []

        for link in df[colname]:
            url = link

            response = requests.get(url, allow_redirects=False, headers=self.headers)

            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")

                data = soup.find("div", {
                    "class": "entry-content wp-block-post-content is-layout-flow wp-block-post-content-is-layout-flow"})

                try:
                    tag = [x.text for x in data]
                    tag_content = " ".join(tag)

                    article_content = tag_content
                    article_href = url

                    article_contents.append(article_content)
                    article_hrefs.append(article_href)

                except AttributeError:
                    continue

                time.sleep(randint(1, 4))

        tc_contents = pd.DataFrame({"href": article_hrefs, "content": article_contents})
        tech_crunch_contents = pd.merge(left=df, right=tc_contents, left_on='href', right_on='href')
        tech_crunch_contents['date'] = pd.to_datetime(tech_crunch_contents['date'])

        return tech_crunch_contents

    def cnn_links(self):
        """
        Function to extract the URLs from CNN
        :return: DataFrame with Source, Date, Article Title and Article URL
        """

        original_start_date = self.start_date
        # Create lists to store scraped information for the data frame
        cnn_dates, cnn_titles, cnn_hrefs = [], [], []

        # While loop to cycle through provided dates
        while self.start_date <= self.end_date:

            base_url = 'https://www.cnn.com/article/sitemap-'
            the_date = self.start_date
            url = base_url + pd.to_datetime(the_date).strftime("%Y-%m-%d").replace("-0", "-") + ".html"

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")

            data = soup.find("div", {"class": "sitemap-entries"})

            for tag in data.find_all("li"):
                tag_header = tag.find("a")

                cnn_date = the_date
                cnn_title = tag_header.get_text(strip=True)
                cnn_href = tag_header["href"]

                cnn_dates.append(cnn_date)
                cnn_titles.append(cnn_title)
                cnn_hrefs.append(cnn_href)

            self.start_date = pd.to_datetime(self.start_date) + timedelta(days=1)
            self.start_date = self.start_date.strftime('%Y-%m-%d')

            time.sleep(randint(1, 5))

        cnn_links = pd.DataFrame({"date": cnn_dates, "source": "CNN",
                                  "href": cnn_hrefs, "title": cnn_titles})
        cnn_links['date'] = pd.to_datetime(cnn_links['date'])
        self.start_date = original_start_date

        return cnn_links

    def cnn_contents(self, df, colname):
        """
        Function to scrape article contents from CNN
        :param df: DataFrame created from `cnn_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `cnl` and article contents
        """
        cnn_contents, cnn_hrefs = [], []

        for link in df[colname]:
            url = link

            response = requests.get(url, headers=self.headers)

            # Check if the link is still good
            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")
                data = soup.find("div", {"class": "article__content"})

                try:
                    tag = [x.text for x in data.select("p")]
                    tag_content = " ".join(tag)

                    cnn_content = tag_content
                    cnn_href = url

                    cnn_contents.append(cnn_content)
                    cnn_hrefs.append(cnn_href)

                except AttributeError:
                    continue

        cnn_df = pd.DataFrame({"href": cnn_hrefs, "content": cnn_contents})
        cnn_contents = pd.merge(left=df, right=cnn_df, left_on='href', right_on='href')
        cnn_contents['date'] = pd.to_datetime(cnn_contents['date'])

        return cnn_contents

    # Selenium Web Scrapers

    def wsj_website(self):
        """
        Function to generate the WSJ archive pages to scrape links
        :return: DataFrame with Date, Article URL
        """
        original_start_date = self.start_date

        urls, date, dates, hrefs = [], [], [], []

        while self.start_date <= self.end_date:
            base_url = 'https://www.wsj.com/news/archive/'
            the_date = pd.to_datetime(self.start_date)

            url = base_url + the_date.strftime('%Y/%m/%d')

            urls.append(url)
            date.append(the_date)

            self.start_date = pd.to_datetime(self.start_date) + timedelta(days=1)
            self.start_date = self.start_date.strftime('%Y-%m-%d')

            # time.sleep(randint(1,2))
            wall_street_journal_pages = pd.DataFrame({"date": date, "url": urls})

        for date, url in zip(wall_street_journal_pages['date'], wall_street_journal_pages['url']):
            for page in range(1, 5):
                href = url + "?page=" + str(page)
                date = date

                hrefs.append(href)
                dates.append(date)

        wall_street_journal_page = pd.DataFrame({"date": dates, "href": hrefs})

        self.start_date = original_start_date

        return wall_street_journal_page

    def wsj_links(self):
        """
        Function to extract the URLs from WSJ. Calls from the `wsj_website` function
        :return: DataFrame with Source, Date, Article Title and Article URL
        """

        original_start_date = self.start_date
        article_dates, article_titles, article_hrefs = [], [], []
        links = self.wsj_website()

        for (date, url) in zip(links['date'], links['href']):

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")

                for tag in soup.findAll("div", {"class": "WSJTheme--headline--7VCzo7Ay"}):
                    tag_header = tag.find("a", {"class": ""})

                    article_date = date
                    article_title = tag_header.get_text(strip=True)
                    article_href = tag_header["href"]

                    article_dates.append(article_date)
                    article_titles.append(article_title)
                    article_hrefs.append(article_href)

                time.sleep(randint(1, 2))

        wall_street_journal_links = pd.DataFrame({"date": article_dates, "source": "Wall Street Journal",
                                                  "href": article_hrefs, "title": article_titles})

        self.start_date = original_start_date

        return wall_street_journal_links

    def wsj_content(self, df, colname):
        """
        Function to scrape article contents from WSJ
        :param df: DataFrame created from `wsj_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """

        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        options.add_argument(f'user-agent={self.headers}')
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://www.wsj.com")

        time.sleep(10)
        article_contents, article_hrefs = [], []
        original_window = driver.current_window_handle

        for link in df[colname]:
            url = link

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[0])
            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source, "lxml")

            data = soup.find("section", {"class": "ef4qpkp0 css-uouibe-Container etunnkc23"})

            try:
                tag = [x.text for x in data.select("p")]
                tag = tag[:-1]
                tag_content = " ".join(tag)

                article_content = tag_content
                article_href = url

                article_contents.append(article_content)
                article_hrefs.append(article_href)

            except AttributeError:
                continue

            time.sleep(randint(1, 3))

        wall_street_journal_content = pd.DataFrame({"href": article_hrefs, "content": article_contents})
        wall_street_journal_content = wall_street_journal_content.groupby('href')['content'].apply(
            ' '.join).reset_index()
        driver.switch_to.window(original_window)

        # driver.close()

        wall_street_journal_content = pd.merge(left=df, right=wall_street_journal_content, left_on='href',
                                               right_on='href')
        wall_street_journal_content = wall_street_journal_content[['date', 'source', 'href', 'title', 'content']]
        wall_street_journal_content = wall_street_journal_content[wall_street_journal_content['content'] != ""]
        wall_street_journal_content['date'] = pd.to_datetime(wall_street_journal_content['date'])

        return wall_street_journal_content

    def barrons_website(self):
        """
        Function to generate the Barrons archive pages to scrape links
        :return: DataFrame with Date, Article URL
        """
        original_start_date = self.start_date

        urls, date, dates, hrefs = [], [], [], []

        while self.start_date <= self.end_date:
            base_url = 'https://www.barrons.com/archive/'
            the_date = pd.to_datetime(self.start_date)
            url = base_url + the_date.strftime('%Y/%m/%d')

            urls.append(url)
            date.append(the_date)

            self.start_date = pd.to_datetime(self.start_date) + timedelta(days=1)
            self.start_date = self.start_date.strftime('%Y-%m-%d')

            time.sleep(randint(2, 4))

        barrons_pages = pd.DataFrame({"date": date, "url": urls})

        for date, url in zip(barrons_pages['date'], barrons_pages['url']):
            for page in range(1, 3):
                href = url + "?page=" + str(page)
                date = date

                hrefs.append(href)
                dates.append(date)

        barrons_page = pd.DataFrame({"date": dates, "href": hrefs})

        self.start_date = original_start_date

        return barrons_page

    def barrons_links(self):
        """
        Function to extract the URLs from Barrons. Calls from the `barrons_pages` function
        :return: DataFrame with Source, Date, Article Title and Article URL
        """

        original_start_date = self.start_date
        article_dates, article_titles, article_hrefs = [], [], []
        links = self.barrons_website()

        for (date, url) in zip(links['date'], links['href']):

            response = requests.get(url, allow_redirects=False, headers=self.headers)

            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")

                for tag in soup.findAll("div", {"class": "BarronsTheme--headline--1Q8XnyIf"}):
                    tag_header = tag.find("a", {"class": "BarronsTheme--headline-link--2s0JerNw"})

                    article_date = date
                    article_title = tag_header.get_text(strip=True)
                    article_href = tag_header["href"]

                    # append scraped information to the lists
                    article_dates.append(article_date)
                    article_titles.append(article_title)
                    article_hrefs.append(article_href)

                    time.sleep(randint(1, 3))

        barrons_links = pd.DataFrame({"date": article_dates, "source": "Barrons",
                                      "href": article_hrefs, "title": article_titles})

        self.start_date = original_start_date

        return barrons_links

    def barrons_content(self, df, colname):
        """
        Function to scrape article contents from Barrons
        :param df: DataFrame created from `barrons_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """

        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        options.add_argument(f'user-agent={self.headers}')
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://www.barrons.com")

        time.sleep(10)

        article_contents, article_hrefs = [], []

        original_window = driver.current_window_handle

        for link in df[colname]:
            url = link

            driver.execute_script("window.open('');")

            # driver.switch_to.window(driver.window_handles[0])

            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source, "lxml")
            data = soup.find("section", {"class": "css-yfonvn-Container ef4qpkp0"})

            try:
                tag = [x.text for x in data.select("p")]
                tag = tag[:-1]
                tag_content = " ".join(tag)

                article_content = tag_content
                article_href = url

                article_contents.append(article_content)
                article_hrefs.append(article_href)

            except AttributeError:
                continue

            time.sleep(randint(1, 4))

        barrons_content = pd.DataFrame({"href": article_hrefs, "content": article_contents})
        barrons_content = barrons_content.groupby('href')['content'].apply(' '.join).reset_index()
        driver.switch_to.window(original_window)

        # driver.close()
        barrons_content = pd.merge(left=df, right=barrons_content, left_on='href', right_on='href')
        barrons_content = barrons_content[['date', 'source', 'href', 'title', 'content']]
        barrons_content['date'] = pd.to_datetime(barrons_content['date'])

        return barrons_content

    def fortune_links(self):
        """
        Function to extract the URLs from Fortune.
        :return: DataFrame with Source, Date, Article Title and Article URL
        """
        original_start_date = self.start_date
        article_dates, article_titles, article_hrefs = [], [], []

        while self.start_date <= self.end_date:

            base_url = "https://fortune.com/sitemap/"
            the_date = pd.to_datetime(self.start_date)
            url = base_url + the_date.strftime("%Y/%m/%d").replace("/0", "/") + "/"

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                soup = None

            else:
                soup = bs4.BeautifulSoup(response.content, "lxml")

                data = soup.find("ol", {"class": "sitemap-grid-articles"})

                for tag in data.find_all("li"):
                    tag_header = tag.find("a")

                    article_date = the_date
                    article_href = tag_header["href"]
                    article_title = tag_header.get_text(strip=True)

                    article_dates.append(article_date)
                    article_titles.append(article_title)
                    article_hrefs.append(article_href)

                self.start_date = pd.to_datetime(self.start_date) + timedelta(days=1)

                self.start_date = self.start_date.strftime('%Y-%m-%d')

                time.sleep(randint(2, 4))

        fortune_links = pd.DataFrame(
            {"date": article_dates, "source": "Fortune", "href": article_hrefs, "title": article_titles})
        fortune_links = fortune_links[fortune_links['href'].str.contains("/well/|/recommends/|/video/") == False]
        self.start_date = original_start_date

        return fortune_links

    def fortune_contents(self, df, colname):
        """
        Function to scrape article contents from Fortune
        :param df: DataFrame created from `fortune_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """
        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(service=service, options=options)

        driver.implicitly_wait(randint(1, 3))
        article_contents, article_hrefs = [], []
        original_window = driver.current_window_handle

        for link in df[colname]:
            url = link
            driver.execute_script("window.open('');")
            # driver.switch_to.window(driver.window_handles[0])
            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source, "lxml")
            data = soup.find("div", {"id": "article-content"})

            try:
                tag = [x.text for x in data.select("p")]
                tag_content = " ".join(tag)

                article_content = tag_content
                article_href = url

                article_contents.append(article_content)
                article_hrefs.append(article_href)

            except AttributeError:
                continue

            time.sleep(randint(1, 3))

        fortune_df = pd.DataFrame({"href": article_hrefs, "content": article_contents})
        fortune_contents = pd.merge(df, fortune_df, left_on='href', right_on='href')
        fortune_contents['date'] = pd.to_datetime(fortune_contents['date'])
        driver.switch_to.window(original_window)
        #    driver.close()

        return fortune_contents

    def insider_links(self, month=None, year=None):
        """
        Function to extract the URLs from Business Insider. Archive page updates once per week.
        :return: DataFrame with Source, Date, Article Title and Article URL
        """
        original_start_date = self.start_date
        article_dates, article_titles, article_hrefs = [], [], []

        if month is None:
            month = pd.to_datetime(self.start_date)
            month = datetime.strftime(month, "%m")
        else:
            month = month

        if year is None:
            year = pd.to_datetime(self.start_date)
            year = datetime.strftime(year, "%Y")
        else:
            year = year

        base_url = "https://www.businessinsider.com/sitemap/html/"
        url = base_url + str(year) + "-" + str(month) + ".html"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            soup = None

        else:
            soup = bs4.BeautifulSoup(response.content, "lxml")

        for tag in soup.findAll("p"):
            tag_header = tag.find("a")
            tag_date = tag.find("br")

            if tag_date is not None:
                article_date = tag_date.find_next_sibling(string=True).strip()
            article_title = tag_header.get_text(strip=True)
            article_href = tag_header["href"]

            article_dates.append(article_date)
            article_titles.append(article_title)
            article_hrefs.append(article_href)

        time.sleep(randint(1, 3))

        business_insider_links = pd.DataFrame({"date": article_dates, "source": "Business Insider",
                                               "href": article_hrefs, "title": article_titles})

        business_insider_links = business_insider_links[
            business_insider_links['href'].str.contains("/personal-finance/|/guides/") == False]
        business_insider_links['date'] = business_insider_links['date'].str[:10]
        business_insider_links['date'] = pd.to_datetime(business_insider_links['date'])

        self.start_date = original_start_date

        return business_insider_links

    def insider_contents(self, df, colname):
        """
        Function to scrape article contents from Business Insider
        This is a weekly function, as the archive is updated on Thursday nights
        :param df: DataFrame created from `insider_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """
        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(service=service, options=options)

        driver.implicitly_wait(randint(1, 3))
        article_contents, article_hrefs = [], []
        original_window = driver.current_window_handle

        for link in df[colname]:
            url = link

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[0])
            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source, "lxml")
            data = soup.find("div", {"class": "content-lock-content"})

            try:
                tag = [x.text for x in data.select("p")]
                tag_content = ' '.join(tag)

                article_content = tag_content
                article_href = url

                article_contents.append(article_content)
                article_hrefs.append(article_href)

            except AttributeError:
                continue

            time.sleep(randint(1, 2))

        business_insider_df = pd.DataFrame({"href": article_hrefs, "content": article_contents})
        business_insider_content = pd.merge(df, business_insider_df, left_on='href', right_on='href')
        business_insider_content = business_insider_content[business_insider_content['content'] != ""]
        business_insider_content['date'] = pd.to_datetime(business_insider_content['date'])
        driver.switch_to.window(original_window)

        return business_insider_content

    def information_links(self):
        """
        Function to extract the URLs from The Information
        :return: DataFrame with Source, Date, Article Title and Article URL
        """
        article_links, article_dates = [], []

        url = "https://www.theinformation.com/sitemap-articles.xml"

        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        soup = bs4.BeautifulSoup(driver.page_source, "xml")
        urls = soup.find_all('url')

        for url in urls:
            loc = url.find('loc').text.strip()
            date = url.find('lastmod').text.strip()

            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
            date = date.strftime('%Y-%m-%d')

            article_links.append(loc)
            article_dates.append(date)

        information_links = pd.DataFrame({"date": article_dates, "href": article_links, "source": "The Information"})
        information_links = information_links[1:]
        information_links['date'] = pd.to_datetime(information_links['date'])
        information_links = information_links[
            (information_links['date'] >= self.start_date) & (information_links['date'] <= self.end_date)]

        return information_links

    def information_contents(self, df, colname):
        """
        Function to scrape article contents from The Information
        :param df: DataFrame created from `information_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """

        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(service=service, options=options)

        driver.implicitly_wait(randint(1, 3))
        article_contents, article_hrefs, article_headers = [], [], []

        original_window = driver.current_window_handle

        for link in df[colname]:
            url = link
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[0])
            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source, "lxml")
            data = soup.find("div", {"class": re.compile(r"SE2jANfgnguT1IMXb9i2 clipperable-content")})

            try:
                tag = [x.text for x in data.select("p")]
                tag_content = " ".join(tag)
                article_content = tag_content
                article_href = url

                # Extract the header
                header_div = soup.find("div", {"class": "z-10 mb-32 w-full flex-1 sm:mb-48 lg:mb-32"})
                if header_div:
                    header_elem = header_div.find("h1", {
                        "class": "my-8 font-suisse-works text-headline-sm text-black print:!text-headline-sm "
                                 "sm:text-headline-xl"})
                    if header_elem:
                        article_header = header_elem.text
                    else:
                        article_header = ""
                else:
                    article_header = ""

                article_contents.append(article_content)
                article_hrefs.append(article_href)
                article_headers.append(article_header)

            except AttributeError:
                continue

            time.sleep(randint(5, 9))

        information_content = pd.DataFrame(
            {"href": article_hrefs, "content": article_contents, "title": article_headers})

        driver.switch_to.window(original_window)
        # driver.close()
        information_content = pd.merge(left=df, right=information_content, left_on='href', right_on='href')
        information_content = information_content[['date', 'source', 'href', 'title', 'content']]
        information_content = information_content[information_content['content'] != ""]

        return information_content

    def bloomberg_links(self):
        """
        Function to extract the URLs from Bloomberg
        :return: DataFrame with Source, Date, Article Title and Article URL
        """

        article_links, article_dates, article_language = [], [], []

        url = "https://www.bloomberg.com/feeds/sitemap_news.xml"

        response = requests.get(url, headers=self.headers)
        soup = bs4.BeautifulSoup(response.content, "xml")
        urls = soup.find_all('url')

        for url in urls:
            loc = url.find('loc').text
            date = url.find('news:publication_date').text
            language = url.find('news:language').text

            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
            date = date.strftime('%Y-%m-%d')

            article_links.append(loc)
            article_dates.append(date)
            article_language.append(language)

        bloomberg_links = pd.DataFrame({"date": article_dates, "href": article_links, "language": article_language,
                                        "source": "Bloomberg"})

        bloomberg_links = bloomberg_links[bloomberg_links['language'] == 'en']
        bloomberg_links = bloomberg_links[['date', 'href', 'source']]
        bloomberg_links = bloomberg_links[~bloomberg_links['href'].str.contains('/opinion/')]
        bloomberg_links = bloomberg_links[
            (bloomberg_links['date'] >= self.start_date) & (bloomberg_links['date'] <= self.end_date)]

        return bloomberg_links

    def bloomberg_contents(self, df, colname):
        """
        Function to scrape article contents from Bloomberg
        :param df: DataFrame created from `bloomberg_links() function
        :param colname: column name containing the URLs in `df`
        :return: DataFrame containing the join of `df` and article contents
        """
        service = Service(self.driver)
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        options.add_argument("--incognito")
        options.add_argument(f'user-agent={self.headers}')
        driver = webdriver.Chrome(service=service, options=options)

        driver.implicitly_wait(randint(1, 3))
        article_contents, article_hrefs, article_headers = [], [], []

        original_window = driver.current_window_handle

        for link in df[colname]:
            url = link
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[0])
            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source, "lxml")
            data = soup.find("div", {"class": "styles_content__QvQ5s"})

            try:
                tag = [x.text for x in data.select("p")]
                # tag = tag[:-1]
                tag_content = " ".join(tag)
                article_content = tag_content
                article_href = url

                # Extract the header
                header_div = soup.find("div", {"class": "gridLayout_topContent__zu2nl"})
                if header_div:
                    header_elem = header_div.find("h1", {"class": "media-ui-HedAndDek_headline-D19MOidHYLI-"})
                    if header_elem:
                        article_header = header_elem.text
                    else:
                        article_header = ""
                else:
                    article_header = ""

                article_contents.append(article_content)
                article_hrefs.append(article_href)
                article_headers.append(article_header)
            except AttributeError:
                continue

            time.sleep(randint(5, 9))

        bloomberg_content = pd.DataFrame({"href": article_hrefs, "content": article_contents, "title": article_headers})
        driver.switch_to.window(original_window)
        # driver.close()
        bloomberg_content = pd.merge(left=df, right=bloomberg_content, left_on='href', right_on='href')
        bloomberg_content = bloomberg_content[['date', 'source', 'href', 'title', 'content']]
        bloomberg_content = bloomberg_content[bloomberg_content['content'] != ""]

        return bloomberg_content
