## Stock_Scraper
## Author : jingbo.liu2013@gmail.com
## Date : 2017/11/26
1. Scrape historical stock price (Package  pandas_datareader)
    
2. Scrape yahoo finance for summary and statistics table (Package requests and bs4)

web example : https://finance.yahoo.com/quote/TOT?p=TOT
  
3. Scrape historical financial statement (quarterly/annual) from amigobulls.com
   (package selenium)

``` python
## Test 
from finance_scraper import stock_scrape
import os
test = stock_scrape.stock_scrape()
download_path = "/home/jingbo/Downloads/"
print("the GE summary in yahoo finance is ",test.yahoo_summary_one("GE")) ## Test for yahoo_summary
print("Test for yahoo summary for all tickers",test.yahoo_summary_all(["TOT", "GE"]))
start_date = datetime.datetime(1994, 7, 1)
end_date = datetime.datetime.now()
test.yahoo_hist_price_all(["GE","CGG"],start_date=start_date,end_date=end_date,folder=download_path)
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
user_name = os.environ["AMIGOBULLS_USERID"]
user_pwd = os.environ["AMIGOBULLS_PWD"]
test.amigobulls_statement_all(tics = ["GE","CGG"],download_path=download_path,chromedriver_path=CHROMEDRIVER_PATH,
                              username = user_name,pwd = user_pwd)
```                              
