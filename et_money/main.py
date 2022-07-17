import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from openpyxl import load_workbook
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MfTracker:
    def __init__(self):
        self.types_of_mf = ['large-cap/32', 'mid-cap/35', 'small-cap/36', 'large-and-midcap/33',
                            'multi-cap/34', 'focused/77', 'value-oriented/37']
        self.website = "https://www.etmoney.com/mutual-funds/equity/"
        pass

    def get_fund_web_soup(self, fund_link):
        page = requests.get(fund_link)
        soup = BeautifulSoup(page.content, 'html.parser')
        return soup

    def get_left_table(self, fund_soup):
        div_tag = fund_soup.find("div", attrs={"class": "mfSceme-key-parameters mfSceme-key-parameters-table"})
        perf_dfs = pd.read_html(str(div_tag))
        for perf_df in perf_dfs:
            perf_df = perf_df.T
            perf_df.columns = perf_df.iloc[0]
            perf_df = perf_df.iloc[1:]
        return perf_df

    def get_more_perf_params(self, fund_soup, perf_df):
        params = fund_soup.find("ul", attrs={"class": "inline-list", "id": "performance-indicators-list"})
        for perf_param in params.findAll("li"):
            # lets get std. dev, alpha, beta, sharpe, sortino
            perf_param = perf_param.get_text()
            col, value = perf_param.split(':')[0].strip(), perf_param.split(':')[1].strip()
            perf_df[col] = value
        return perf_df

    def save_files(self, df_list, each_fund, today):
        df_final = pd.concat(df_list)
        target_dir = os.path.join(os.getcwd(), each_fund[:each_fund.find('/')] + '_outputs')
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)
        df_final.to_csv(os.path.join(target_dir, f'{today}.csv'), index=False)
        logger.info(f'{each_fund}_file_saved')

    def download_perf_data(self, fund_family_soup, each_fund):
        df_list = []
        for div in fund_family_soup.findAll("div", attrs={"class": "scheme-name"}):
            a_tag = div.find("a")
            fund_name = a_tag.get_text()
            fund_link = "".join(['https://www.etmoney.com', a_tag['href']])

            # now lets open the page for a mf of a mf family
            fund_page = requests.get(fund_link)
            fund_soup = BeautifulSoup(fund_page.content, "lxml")

            # extract the performance table on the left side of the webpage
            perf_df = self.get_left_table(fund_soup)

            # extract the extra performance measures below
            perf_df = self.get_more_perf_params(fund_soup, perf_df)

            # add some more info
            today = datetime.today().strftime("%Y-%m-%d")
            perf_df.insert(0, 'fund_name', fund_name)
            perf_df.insert(1, 'timestamp', today)
            df_list.append(perf_df)
        self.save_files(df_list, each_fund, today)


    def run(self):
        for each_fund in self.types_of_mf:
            logger.info(f'scrapping {each_fund} webpage')
            fund_family_link = ''.join([self.website, each_fund])
            fund_family_soup = self.get_fund_web_soup(fund_family_link)
            self.download_perf_data(fund_family_soup, each_fund)


def run():
    mf_tracker = MfTracker()
    mf_tracker.run()


if __name__ == '__main__':
    run()
