#! /usr/bin/python3
import getopt
import getpass
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import pickle
import shutil
import sys
import threading
import datetime
import time
import urllib.request
from random import randint
from sys import argv

import onetimepass as otp
import wget
import yaml
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import Column, Integer, String, create_engine, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base

try:
    handler = TimedRotatingFileHandler(
        'logs/ICS.log', when='D', backupCount=7, atTime=datetime.time(0, 30))

    logging.basicConfig(
        # filemode='a',
        format='%(asctime)s - %(name)s - %(message)s',
        datefmt='%d-%b-%y %H:%M:%S',
        level=logging.INFO,
        handlers=[handler])
except FileNotFoundError as e:
    print("Unable to find logs")
    if not os.path.exists('logs'):
        os.makedirs('logs')
    os.execl(sys.executable, sys.executable, *sys.argv)
engine = create_engine("sqlite:///ICS.db", echo=True)
Base = declarative_base()


class User(Base):
    __tablename__ = 'stories'
    id = Column(String, primary_key=True)
    last_seen = Column(DateTime)


def save_cookie(driver, path="cookies.pkl"):
    try:
        pickle.dump(driver.get_cookies(), open(path, "wb"))
        logging.info('Saved cookies to %s', path)
    except Exception as e:
        logging.error("Error saving cookies to %s", path, exc_info=True)
        logging.error(str(e))


def load_cookie(driver, path="cookies.pkl"):
    try:
        cookies = pickle.load(open(path, "rb"))
        for cookie in cookies:
            if "expiry" in cookie:
                cookie.pop('expiry', None)
            driver.add_cookie(cookie)
        logging.info('Loaded cookies from %s', path)
    except Exception as e:
        logging.error("Error loading cookie at %s", path, exc_info=True)
        logging.error(str(e))


def find_element_by_name_retry(
        driver,
        name,
        retry_count=5,
        wait_time=5,
        killprocess=True):
    logging.info(
        "Attempting to find element %s with retry count %d",
        name,
        retry_count)
    for i in range(retry_count):
        try:
            return driver.find_element_by_name(name)
        except Exception as e:
            time.sleep(wait_time)
            print(e)
            logging.error(
                "Error finding element %s on attempt number %d",
                name,
                i,
                exc_info=True)
    if (killprocess):
        exit()


def find_element_by_tag_and_text(
        driver,
        tag,
        text,
        attribute="innerHTML",
        multiple=False):
    logging.info(
        "Trying to find element with tag: %s and text: %s and attribute: %s",
        tag,
        text,
        attribute)
    try:
        tags = driver.find_elements_by_tag_name(tag)
        elements = []
        for i in tags:
            if text in i.get_attribute(attribute):
                if multiple:
                    elements.append(i)
                else:
                    return i
        return elements
    except Exception as e:
        logging.error(
            "Error finding element with tag: %s and text: %s and attribute: %s",
            tag,
            text,
            attribute,
            exc_info=True)
        logging.error(str(e))


def createDriver(headless=True, proxy=False):
    """ Creates the chrome driver with an option to make the driver headless
    Keyword arguments:
    headless -- true / false if the driver should be headless (default True)
    """
    logging.info("Attemtping to create a chrome driver")
    # Optional argument, if not specified will search path.
    # Setup headless chrome for selenium
    try:
        chrome_options = webdriver.ChromeOptions()
        if (headless):
            chrome_options.add_argument('headless')
        if (proxy):
            chrome_options.add_argument('--proxy-server='+proxy)
        mobile_emulation = {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
        }
        chrome_options.add_experimental_option(
            "mobileEmulation", mobile_emulation)
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome('./chromedriver', options=chrome_options)
        logging.info("Created chrome driver")
        return driver
    except Exception as e:
        logging.error(
            "Error occured during creation of the chrome driver headless: %s",
            str(headless),
            exc_info=True)
        logging.error(str(e))


def login(driver, username_=None, password_=None, totp_key=None):
    driver.get('https://www.instagram.com/accounts/login/')
    load_cookie(driver)
    driver.get('https://www.instagram.com/accounts/login/')
    # Read in username and password for instagram
    if (driver.current_url == "https://www.instagram.com/accounts/login/"):
        if (not username_ or not password_):
            username_ = input("Please Input Username: ").strip()
            password_ = getpass.getpass("Please Input Password: ").strip()
        try:
            if driver.current_url == "https://www.instagram.com/accounts/login/":
                # Type in login
                find_element_by_name_retry(
                    driver, 'username').send_keys(username_)
                find_element_by_name_retry(
                    driver, 'password').send_keys(password_)
                webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
                # Wait for login
                time.sleep(5)
                # Check for 2FA
                if "two_factor" in driver.current_url:
                    if not totp_key:
                        two_fa_code = input("Please Enter 2FA Code: ").strip()
                    else:
                        logging.info(
                            "Attempting to create 2fa code using config key")
                        two_fa_code = otp.get_totp(totp_key)
                        logging.info("Created 2FA Code: %s", two_fa_code)
                    find_element_by_tag_and_text(
                        driver, 'input', "Security Code", "aria-label").send_keys(two_fa_code)
                    webdriver.ActionChains(driver).send_keys(
                        Keys.ENTER).perform()
                # Wait for login
                time.sleep(5)
                logging.info("Logged in as %s", username_)
                # Save cookie
                save_cookie(driver)
        except Exception as e:
            logging.error("Failed to login as %s", username_, exc_info=True)
            logging.error(str(e))
            driver.save_screenshot(str(time.time()) + ".png")
    return username_


def getFollowerList(driver, username_):
    logging.info("Attempting to get Follower List")
    username_ = driver.find_element_by_xpath(
        '//section/div/div/div/div/div/a').get_attribute("innerHTML")
    # Go to profile
    driver.get('https://www.instagram.com/' + username_)
    # link.click()
    time.sleep(3)
    # Get following amount
    follower_amount_class_id = find_element_by_tag_and_text(
        driver, 'a', 'following').get_attribute('innerHTML').split('"')[1].strip()
    follower_amount = find_element_by_tag_and_text(
        driver,
        'span',
        follower_amount_class_id,
        'class',
        True)[2].get_attribute('innerHTML')
    # Open following tab
    find_element_by_tag_and_text(driver, 'a', 'following', 'href').click()
    time.sleep(5)
    usernames_elements = driver.find_elements_by_xpath(
        "//li/div/div/div/div/a")
    usernames = []
    while (len(usernames_elements) < int(follower_amount)):
        webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
        usernames_elements = driver.find_elements_by_xpath(
            "//li/div/div/div/div/a")
    for names in usernames_elements:
        usernames.append(names.text)
    logging.info("Got list of users length %d", len(usernames))
    return usernames


def downloadStoryFile(url, download_folder):
    # Download the file from `url` and save it locally under `file_name`:
    logging.info("Attempting to download %s to %s", url, download_folder)
    print(download_folder)
    if not os.path.exists('static/stories/' + download_folder):
        os.makedirs('static/stories/' + download_folder)
    wget.download(url, out='static/stories/' + download_folder + '/')


def getStories(driver):
    logging.info("Attempting to getStories")
    amt_downloaded = 0
    download_threads = []
    driver.get("https://www.instagram.com/")
    time.sleep(3)
    # check for button to enable notifications
    try:
        find_element_by_tag_and_text(driver, 'button', 'Not Now').click()
    except BaseException:
        pass
    time.sleep(2)
    try:
        find_element_by_tag_and_text(driver, 'a', "Watch All").click()
    except BaseException:
        # driver.set_window_size(1920,1080)
        try:
            find_element_by_tag_and_text(
                driver, 'button', "menuitem", 'role').click()
        except Exception as e:
            logging.error(e)
            driver.save_screenshot(str(time.time()) + ".png")
            sys.exit(1)
    while(driver.current_url == "https://www.instagram.com/"):
        time.sleep(1)
    print("test")
    emptyurlcount = 0
    while(driver.current_url != "https://www.instagram.com/"):
        time.sleep(1)
        try:
            # stories[driver.current_url].update(find_element_by_tag_and_text(driver,'source','video/mp4','type').get_attribute('src'))
            # stories[driver.current_url].add(find_element_by_tag_and_text(driver,'img','sync',"decoding").get_attribute('src'))
            url = find_element_by_tag_and_text(
                driver, 'img', 'sync', "decoding").get_attribute('src')
            logging.info("URL is %s length", str(len(url)))
            logging.info("URL is %s", url)
            if len(url) == 0:
                emptyurlcount += 1
                logging.error(
                    "URL is empty. EmptyURLCount is now: %s", str(emptyurlcount))
            if emptyurlcount > 50:
                logging.error("Unable to get stories.")
                for t in download_threads:
                    t.join()
                return None
            print(url)
            download_threads.append(threading.Thread(
                target=downloadStoryFile, args=(url, driver.current_url.split('/')[-2])))
            download_threads[-1].start()
            amt_downloaded += 1
            find_element_by_tag_and_text(
                driver, 'div', 'coreSpriteRightChevron', 'class').click()
        except AttributeError as e:
            # stories[driver.current_url].update(find_element_by_tag_and_text(driver,'video','auto','preload'))
            print(e)
        except Exception as e:
            print(e)
    for t in download_threads:
        t.join()
    logging.info("Got %d stories", amt_downloaded)


def loadcfg(settings_file='./settings.yml'):
    logging.info("Attempting to load cfg from %s", settings_file)
    return yaml.safe_load(open(settings_file))


def endChrome(driver):
    logging.info("Exiting driver instance.")
    try:
        driver.close()
        driver.quit()
    except BaseException:
        logging.error("Failed to endChrome Driver", exc_info=True)


def main():
    logging.info("Starting Main Method")
    config = loadcfg()
    driver = createDriver()
    try:
        login(
            driver,
            username_=config['username'],
            password_=config['password'],
            totp_key=config['totp_key'])
    except BaseException:
        login(
            driver,
            username_=config['username'],
            password_=config['password'])
    getStories(driver)
    print("end")
    # print(getFollowerList(driver, username_))


if __name__ == "__main__":
    main()
