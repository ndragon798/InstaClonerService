import os
import time
import getpass
import pickle
from sys import argv
from random import randint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait


def save_cookie(driver, path="cookies.pkl"):
    pickle.dump(driver.get_cookies(), open(path, "wb"))


def load_cookie(driver, path="cookies.pkl"):
    cookies = pickle.load(open(path, "rb"))
    for cookie in cookies:
        if "expiry" in cookie:
            cookie.pop('expiry', None)
        driver.add_cookie(cookie)


def find_element_by_name_retry(driver, name, retry_count=5, wait_time=5, killprocess=True):
    for i in range(retry_count):
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


def getFollowerList():
    # Read in username and password for instagram
    try:
        scriptname_, username_, password_ = argv
    except Exception as e:
        print(e)
        username_ = input("Please Input Username: ").strip()
        password_ = getpass.getpass("Please Input Password: ").strip()

    # Optional argument, if not specified will search path.
    # Setup headless chrome for selenium
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    # driver = webdriver.Chrome('./chromedriver')
    driver = webdriver.Chrome('./chromedriver', options=chrome_options)
    driver.get('https://www.instagram.com/accounts/login/')

    load_cookie(driver)
    # Load login page
    driver.get('https://www.instagram.com/accounts/login/')
    time.sleep(5)
    # print(driver.current_url)
    if driver.current_url == "https://www.instagram.com/accounts/login/":
        # Type in login
        find_element_by_name_retry(driver, 'username').send_keys(username_)
        find_element_by_name_retry(driver, 'password').send_keys(password_)
        webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
        # Wait for login
        time.sleep(5)
        # Save cookie
        save_cookie(driver)
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


def main():
    print(getFollowerList())


if __name__ == "__main__":
    main()
