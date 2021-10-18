from celery import shared_task
from .models import loginInfo

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import onetimepass as otp
import os
import urllib.request
import shutil
import urllib.parse as urlparse
import pickle


def find_element_by_tag_and_text(
        driver,
        tag,
        text,
        attribute="innerHTML",
        multiple=False):
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
    except Exception:
        return ""


def load_cookie(driver, path="cookies.pkl"):
    login = loginInfo.objects.all()[0]
    try:
        cookies = login.cookie

        for cookie in cookies:
            if "expiry" in cookie:
                cookie.pop('expiry', None)
            driver.add_cookie(cookie)
        print('Loaded cookies :' + login.cookie)
    except Exception as e:
        print("Error loading cookie at %s", path, exc_info=True)
        print(str(e))


def save_cookie(driver, path="cookies.pkl"):
    login = loginInfo.objects.all()[0]
    try:
        login.cookie=driver.get_cookies()
        login.save()
        # pickle.dump(driver.get_cookies(), open(path, "wb"))
        # print('Saved cookies to ' + path)
    except Exception as e:
        print("Error saving cookies to "+str(path))
        print(str(e))


def filename_from_url(url):
    """:return: detected filename as unicode or None"""
    # [ ] test urlparse behavior with unicode url
    fname = os.path.basename(urlparse.urlparse(url).path)
    if len(fname.strip(" \n\t.")) == 0:
        return None
    return(fname)


@shared_task
def downloadStoryFile(url, download_folder):
    print(download_folder)
    if not os.path.exists('static/stories/' + download_folder):
        os.makedirs('static/stories/' + download_folder)
    with urllib.request.urlopen(url) as response, open(str(download_folder)+filename_from_url(url), 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


@shared_task
def get_stories():
    login = loginInfo.objects.all()[0]
    try:
        driver = webdriver.Remote(
            command_executor="http://ics-selenium-firefox:4444/wd/hub",
            desired_capabilities={
                "browserName": "firefox",
                "video": "True",
            }
        )
        driver.maximize_window()
        driver.get('https://www.instagram.com/accounts/login/')
        try:
            load_cookie(driver)
        except:
            print("ERROR LOADING COOKIE")
        driver.get('https://www.instagram.com/accounts/login/')
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            ).send_keys(login.username)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            ).send_keys(login.password)
            webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(5)
            if "two_factor" in driver.current_url:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.NAME, "verificationCode"))
                ).send_keys(otp.get_totp(login.totp_key))
                webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(5)
            save_cookie(driver)
        except Exception as e:
            print(e)
            driver.get('https://www.instagram.com/')
        time.sleep(10)
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
                # print(e)
                driver.save_screenshot(str(time.time()) + ".png")
                # sys.exit(1)
        while(driver.current_url == "https://www.instagram.com/"):
            time.sleep(1)
        # emptyurlcount = 0
        amt_downloaded = 0
        oldpurl = ""
        oldurl = ""
        while(driver.current_url != "https://www.instagram.com/"):
            try:
                url = find_element_by_tag_and_text(
                    driver, 'img', 'sync', "decoding").get_attribute('src')
                purl = find_element_by_tag_and_text(
                    driver, 'img', 'profile picture', 'alt').get_attribute("alt")
                if oldurl != url:
                    print("URL is " + url)
                    print("PURL is " + purl)
                    downloadStoryFile(url, purl.split(' ')[0])
                    oldpurl = purl
                    oldurl = url
                    amt_downloaded += 1
                    find_element_by_tag_and_text(
                        driver, 'div', 'coreSpriteRightChevron', 'class').click()
            except Exception as e:
                print(e)
        print("Got stories: "+str(amt_downloaded))
        time.sleep(30)
        driver.quit()
    except Exception as e:
        print(e)
