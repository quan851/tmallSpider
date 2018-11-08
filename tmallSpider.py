from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
from config import *
import pymongo

client  = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)

browser.set_window_size(1400,900)

def search():
    print('正在搜索')
    try:
        browser.get('https://www.tmall.com')
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mq')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mallSearch > form > fieldset > div > button')))
        input.send_keys('美食')
        submit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#content > div.main > div.ui-page > div > b.ui-page-skip > form')))
        
        return total.text
    except TimeoutException:
        return search()
    except Exception as er:
        print(er)


def next_page(page_number):
    try:
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#content > div.main > div.ui-page > div > b.ui-page-skip > form > input.ui-page-skipTo')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#content > div.main > div.ui-page > div > b.ui-page-skip > form > button')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#content > div.main > div.ui-page > div > b.ui-page-num > b.ui-page-cur')))
    except TimeoutException:
        next_page(page_number)


def get_products():
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_ItemList')))
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all(class_="product item-1111 ")
        for item in items:
            try:
                soup = BeautifulSoup(str(item),'html.parser')
                imgResult = soup.find('div',attrs = {'class':'productImg-wrap'}).contents[1].contents[1]
                image = ''
                try:
                    image = imgResult.attrs['data-ks-lazyload']
                except Exception:
                    image = imgResult.attrs['src']
                try:
                    priceResult = soup.find('p', attrs={'class':'productPrice'}).contents[3]
                except Exception:
                    priceResult = soup.find('p', attrs={'class':'productPrice'}).contents[1]
                dealResult = soup.find('p',attrs={'class':'productStatus'}).contents[1].contents[1]
                titleResult = soup.find('p',attrs={'class':'productTitle'}).contents[1]  
                deal = re.compile('(\d+\.?\d*)').search(dealResult.contents[0])
                if deal:
                    deal = deal.group(1)
                else:
                    deal = '0'
                product = {
                    'title':titleResult.contents[0][1:],
                    'image':'http:' + image,
                    'price':priceResult.contents[1],
                    'deal':deal,
                   }
                save_to_mongo(product)
            except Exception as err:
                print("解析出错了",err)
    except TimeoutException:
        print("超时出错了")
    except Exception as er:
        print(er)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功', result)
    except Exception:
        print('存储到MONGODB失败')


def main():
    total = search()
    get_products()
    total  = int(re.compile('(\d+)').search(total).group(1))
    #for i in range(2,total + 1):
    #    next_page(i)
    browser.close()

if __name__ == '__main__':
    main()
