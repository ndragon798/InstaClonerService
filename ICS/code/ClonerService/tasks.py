from celery import shared_task
# from .models import

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import onetimepass as otp

@shared_task
def get_stories():
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("nathan.p.easton")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        ).send_keys("2AKdCGtfQ^Un")
        webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
        time.sleep(5)
        if "two_factor" in driver.current_url:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "verificationCode"))
            ).send_keys(otp.get_totp("NVYY24SHO3X4YPI5AVTWKVEUISDJG33T"))
            webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
        time.sleep(5)
        driver.get('https://www.instagram.com/')

        time.sleep(30)
        driver.quit()
    except Exception as e:
        print(e)
