## Scrape yahoo finance for summary and statistics table
## web example : https://finance.yahoo.com/quote/TOT?p=TOT
## The worflow for scraping
## 1. Create a valid url for each ticker
## 2. request url
## 3. Parse with Beautifulsoup
## 4. Search the parsed content, and return the required table

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from time import sleep
from pandas_datareader import data as pdr
import datetime

import os
import sys
import time
from selenium.webdriver import Chrome
from selenium.webdriver.chrome import webdriver as chrome_webdriver

## This class is for headless download of stock files using chrome driver
## The whole purpose is to avoid a security bug in the chromedriver, which prevent driver from downloading
## in headless mode
class DriverBuilder():
    def get_driver(self, driver_path, download_location=None, headless=False):

        driver = self._get_chrome_driver(driver_path, download_location, headless)

        driver.set_window_size(1400, 700)

        return driver

    def _get_chrome_driver(self, driver_path, download_location, headless):
        chrome_options = chrome_webdriver.Options()
        if download_location:
            prefs = {'download.default_directory': download_location,
                     'download.prompt_for_download': False,
                     'download.directory_upgrade': True,
                     'safebrowsing.enabled': False,
                     'safebrowsing.disable_download_protection': True}

            chrome_options.add_experimental_option('prefs', prefs)

        if headless:
            chrome_options.add_argument("--headless")

#        dir_path = os.path.dirname(os.path.realpath(__file__))
#        driver_path = os.path.join(dir_path, "drivers/chromedriver")

        if sys.platform.startswith("win"):
            driver_path += ".exe"

        driver = Chrome(executable_path=driver_path, chrome_options=chrome_options)

        if headless:
            self.enable_download_in_headless_chrome(driver, download_location)

        return driver

    def enable_download_in_headless_chrome(self, driver, download_dir):
        """
        there is currently a "feature" in chrome where
        headless does not allow file download: https://bugs.chromium.org/p/chromium/issues/detail?id=696481
        This method is a hacky work-around until the official chromedriver support for this.
        Requires chrome version 62.0.3196.0 or above.
        """

        # add missing support for chrome "send_command"  to selenium webdriver
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        command_result = driver.execute("send_command", params)
        print("response from browser:")
        for key in command_result:
            print("result:" + key + ":" + str(command_result[key]))


class stock_scrape:
    def __init__(self,tickers = None):
        self.tic = tickers
    def yahoo_hist_price_one_tic(self,tic,start_date,end_date):
        '''
        :param tic:
        :param start_date:
        :param end_date:
        :return: a dataframe with all the historical prices daily for each ticker
        '''
        return pdr.get_data_yahoo(tic, start=start_date, end=end_date)
    def yahoo_hist_price_all(self,tics,start_date,end_date,folder = "./"):
        if tics is None:
            tics = self.tic
        if len(tics) == 0:
            return "No tickers provided"
        for tic in tics:
            try:
                print(tic,start_date,end_date)
                df = self.yahoo_hist_price_one_tic(tic,start_date,end_date)
                df.to_csv(folder + str(tic) + ".csv")
            except ValueError:
                print("Yahoo finance has no hist price for " + str(tic))
    def yahoo_summary_one(self,tic):
        '''
        :param tic:
        :return: a dictionary contains the summary for the given ticker in yahoo finance
            keys: 'Avg. Volume',
                'PE Ratio (TTM)',
                 'Previous Close',
                 'Bid',
                 'EPS (TTM)',
                 'Forward Dividend & Yield',
                 'Volume',
                 "Day's Range",
                 'Beta',
                 '1y Target Est',
                 'Ask',
                 '52 Week Range',
                 'Open',
                 'Market Cap',
                 'Earnings Date',
                 'Ex-Dividend Date'
        '''
        url = "https://finance.yahoo.com/quote/" + tic + "?p=" + tic
        req = requests.get(url)
        sleep(3)
        html = BeautifulSoup(req.content, "html.parser")
        summary_tables = html.find_all("div", {"data-test": re.compile(".*-summary-table")}) ## find the summary tables
        tic_df = {}
        for table in summary_tables:
            tbody = table.find_all("tbody")[0]
            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                col_,val_ = [tem.text.strip().encode('utf-8') for tem in cols] ## First column is the fundamentals
                                                                            # ## Second is the value of fundamental
                tic_df[col_] = val_
        return tic_df
    def yahoo_summary_all(self,tics = None):
        if tics is None:
            tics = self.tic
        if len(tics) == 0:
            return "No tickers provided"
        tics = list(tics)
        dict_init = self.yahoo_summary_one(tics[0])
        dict_init["tic"] = tics[0]
        summary_df = pd.DataFrame.from_dict([dict_init])
        for i in range(1,len(tics)):
            try:
                dict_new = self.yahoo_summary_one(tics[i])
                dict_new["tic"] = tics[i]
                summary_df = summary_df.append([dict_new])
            except ValueError:
                print("Yahoo summary has no info for " + str(tics[[i]]))
        summary_df.set_index("tic")
        return summary_df
    def amigobulls_statement(self,tic,download_path,chromedriver_path,username,pwd):
        '''
        :param tic:
        :param download_path:
        :param chromedriver_path:
        :param username: registered user email
        :param pwd:  user password
        :return: None Saved the past 10 years' financial statement in download folder
        '''
        driver_builder = DriverBuilder()
        CHROMEDRIVER_PATH =chromedriver_path
        driver = driver_builder.get_driver(CHROMEDRIVER_PATH, download_path, headless=True)

        ## Go to the login page and login first
        driver.get("https://amigobulls.com/login")
        elem_login = driver.find_element_by_id("login_email")
        elem_login.clear()
        elem_login.send_keys(username)
        elem_pwd = driver.find_element_by_id("login_pswd")
        elem_pwd.clear()
        elem_pwd.send_keys(pwd)
        elem_sub = driver.find_element_by_id("loginbtn")
        elem_sub.click()
        time.sleep(2)
        ## Go to the income statement and click download
        driver.get("https://amigobulls.com/stocks/"+tic+"/income-statement/quarterly?t=ibc")
        elem = driver.find_element_by_class_name("reportdownload").click()
        time.sleep(2)
        driver.get("https://amigobulls.com/stocks/"+tic+"/income-statement/annual?t=ibc")
        elem = driver.find_element_by_class_name("reportdownload").click()
        time.sleep(2)
        ## Go to the balance sheet and click download
        driver.get("https://amigobulls.com/stocks/"+tic+"/balance-sheet/quarterly?t=ibc")
        elem = driver.find_element_by_class_name("reportdownload").click()
        time.sleep(2)
        driver.get("https://amigobulls.com/stocks/"+tic+"/balance-sheet/annual?t=ibc")
        elem = driver.find_element_by_class_name("reportdownload").click()
        time.sleep(2)
        ## Go to the Cash Flow and click download
        driver.get("https://amigobulls.com/stocks/"+tic+"/cash-flow/quarterly?t=ibc")
        elem = driver.find_element_by_class_name("reportdownload").click()
        time.sleep(2)
        driver.get("https://amigobulls.com/stocks/"+tic+"/cash-flow/annual?t=ibc")
        elem = driver.find_element_by_class_name("reportdownload").click()
        time.sleep(2)
        driver.close()
        return

    def amigobulls_statement_all(self, tics, download_path, chromedriver_path, username, pwd):
        if tics is None:
            tics = self.tic
        if len(tics) == 0:
            return "No tickers provided"
        for tic in tics:
            try:
                self.amigobulls_statement(tic=tic,download_path=download_path,
                                          chromedriver_path=chromedriver_path,
                                          username=username,
                                          pwd = pwd)
            except ValueError:
                print("amigobulls.com has no statement info for " + str(tic))
        return

if __name__=="__main__":
    test = stock_scrape()
    download_path = "/home/jingbo/Downloads/"
#    print("the GE summary in yahoo finance is ",test.yahoo_summary_one("GE")) ## Test for yahoo_summary
#    print("Test for yahoo summary for all tickers",test.yahoo_summary_all(["TOT", "GE"]))
    start_date = datetime.datetime(1994, 7, 1)
    end_date = datetime.datetime.now()
#    test.yahoo_hist_price_all(["GE","CGG"],start_date=start_date,end_date=end_date,folder=download_path)
    CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
    user_name = os.environ["AMIGOBULLS_USERID"]
    user_pwd = os.environ["AMIGOBULLS_PWD"]
    test.amigobulls_statement_all(tics = ["GE","CGG"],download_path=download_path,chromedriver_path=CHROMEDRIVER_PATH,
                              username = user_name,pwd = user_pwd)
