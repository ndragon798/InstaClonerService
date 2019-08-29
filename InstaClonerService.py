#! /usr/bin/python3
import getopt
import getpass
import logging
import os
import pickle
import shutil
import sys
import threading
import time
import urllib.request
from random import randint
from sys import argv

import wget
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger('InstaClonerService')
hdlr = logging.FileHandler('./InstaClonerService.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.WARNING)


def save_cookie(driver, path="cookies.pkl"):
    pickle.dump(driver.get_cookies(), open(path, "wb"))


def load_cookie(driver, path="cookies.pkl"):
    try:
        cookies = pickle.load(open(path, "rb"))
        for cookie in cookies:
            if "expiry" in cookie:
                cookie.pop('expiry', None)
            driver.add_cookie(cookie)
    except:
        pass


def find_element_by_name_retry(driver, name, retry_count=5, wait_time=5, killprocess=True):
    for _1 in range(retry_count):
        try:
            return driver.find_element_by_name(name)
        except Exception as e:
            time.sleep(wait_time)
            print(e)
    if (killprocess):
        exit()


def find_element_by_tag_and_text(driver, tag, text, attribute="innerHTML", multiple=False):
    tags = driver.find_elements_by_tag_name(tag)
    elements = []
    for i in tags:
        if text in i.get_attribute(attribute):
            if multiple:
                elements.append(i)
            else:
                return i
    return elements


def createDriver(headless=True):
    """ Creates the chrome driver with an option to make the driver headless
    Keyword arguments:
    headless -- true / false if the driver should be headless (default True)
    """
    
    # Optional argument, if not specified will search path.
    # Setup headless chrome for selenium
    chrome_options = webdriver.ChromeOptions()
    if (headless):
        chrome_options.add_argument('headless')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome('./chromedriver', options=chrome_options)
    return driver


def login(driver, username_ = None,password_ = None):
    driver.get('https://www.instagram.com/accounts/login/')
    load_cookie(driver)
    driver.get('https://www.instagram.com/accounts/login/')
        # Read in username and password for instagram
    if (driver.current_url == "https://www.instagram.com/accounts/login/"):
        if (not username_  or not password_):
            username_ = input("Please Input Username: ").strip()
            password_ = getpass.getpass("Please Input Password: ").strip()
        try:
            if driver.current_url == "https://www.instagram.com/accounts/login/":
                # Type in login
                find_element_by_name_retry(driver, 'username').send_keys(username_)
                find_element_by_name_retry(driver, 'password').send_keys(password_)
                webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
                # Wait for login
                time.sleep(5)
                # Check for 2FA
                if "two_factor" in driver.current_url:
                    two_fa_code = input("Please Enter 2FA Code: ").strip()
                    find_element_by_tag_and_text(driver,'input',"Security Code","aria-label").send_keys(two_fa_code) 
                    webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
                #Wait for login
                time.sleep(5)
                # Save cookie
                save_cookie(driver)
        except Exception as e:
            logger.error(e)
            driver.save_screenshot(str(time.time())+".png")
    return username_


def getFollowerList(driver, username_):
    username_ = driver.find_element_by_xpath('//section/div/div/div/div/div/a').get_attribute("innerHTML")
    # Go to profile
    driver.get('https://www.instagram.com/'+username_)
    # link.click()
    time.sleep(3)
    # Get following amount
    follower_amount_class_id = find_element_by_tag_and_text(driver, 'a', 'following').get_attribute('innerHTML').split('"')[1].strip()
    follower_amount = find_element_by_tag_and_text(driver, 'span', follower_amount_class_id, 'class', True)[2].get_attribute('innerHTML')
    # Open following tab
    find_element_by_tag_and_text(driver, 'a', 'following', 'href').click()
    time.sleep(5)
    usernames_elements = driver.find_elements_by_xpath("//li/div/div/div/div/a")
    usernames = []
    while (len(usernames_elements) < int(follower_amount)):
        webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
        usernames_elements = driver.find_elements_by_xpath("//li/div/div/div/div/a")
    for names in usernames_elements:
        usernames.append(names.text)
    return usernames

def downloadStoryFile(url,download_folder):
    # Download the file from `url` and save it locally under `file_name`:
    print(download_folder)
    if not os.path.exists('stories/'+download_folder):
        os.makedirs('stories/'+download_folder)
    wget.download(url,out='stories/'+download_folder+'/')
        

def getStories(driver):
    amt_downloaded = 0
    download_threads = []
    driver.get("https://www.instagram.com/")
    time.sleep(3)
    #check for button to enable notifications
    try:
        find_element_by_tag_and_text(driver,'button','Not Now').click()
    except:
        pass
    time.sleep(2)
    try:
        find_element_by_tag_and_text(driver,'a',"Watch All").click()
    except:
        # driver.set_window_size(1920,1080)
        try:
            find_element_by_tag_and_text(driver,'button',"menuitem",'role').click()
        except Exception as e:
            logger.error(e)
            driver.save_screenshot(str(time.time())+".png")   
            sys.exit(1)
    while(driver.current_url == "https://www.instagram.com/"):
        time.sleep(1)
    print("test")
    while(driver.current_url != "https://www.instagram.com/"):
        time.sleep(1)
        try:
            # stories[driver.current_url].update(find_element_by_tag_and_text(driver,'source','video/mp4','type').get_attribute('src'))
            # stories[driver.current_url].add(find_element_by_tag_and_text(driver,'img','sync',"decoding").get_attribute('src'))
            url=find_element_by_tag_and_text(driver,'img','sync',"decoding").get_attribute('src')
            print(url)
            download_threads.append(threading.Thread(target=downloadStoryFile,args=(url,driver.current_url.split('/')[-2])))
            download_threads[-1].start()
            amt_downloaded+=1
            find_element_by_tag_and_text(driver,'div','coreSpriteRightChevron','class').click()
        except AttributeError as e:
            # stories[driver.current_url].update(find_element_by_tag_and_text(driver,'video','auto','preload'))
            print(e)
        except Exception as e:            
            print(e)
    for t in download_threads:
        t.join()
            

def main():
    driver = createDriver(False)
    login(driver)
    getStories(driver)
    print("end")
    # print(getFollowerList(driver, username_))


if __name__ == "__main__":
    main()
