#! /usr/bin/python3
import os
import time
import base64
from importlib import reload

from flask import Flask, render_template, url_for
from flask_apscheduler import APScheduler

import InstaClonerService as ICS

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/<user>')
def usergallery(user=None):
    photosloc=[]
    for (_root, _dirs, files) in os.walk("static/stories/"+user):
        for file in files:
            with open(_root+"/"+file,"rb") as img_file:
               photosloc.append(base64.b64encode(img_file.read()).decode('utf-8'))
            #photosloc.append("stories/"+user+"/"+file)
    return render_template('user.html',photos=photosloc,photolen=len(photosloc))

@scheduler.task('cron', id='stories', hour='*')
def scheduled_task():
    reload(ICS)
    driver = ICS.createDriver()
    config = ICS.loadcfg()
    try:
        ICS.login(driver, username_=config['username'],password_=config['password'],totp_key=config['totp_key'])
    except:
        ICS.login(driver, username_=config['username'],password_=config['password'])
    ICS.getStories(driver)
    print("end")
    ICS.endChrome(driver)
         
app.run(host='0.0.0.0', port=12345)
