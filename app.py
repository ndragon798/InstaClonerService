#! /usr/bin/python3
from flask import Flask
from flask_apscheduler import APScheduler
from importlib import reload
 
import time
import InstaClonerService as ICS

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
 
@app.route('/')
def welcome():
    return 'Welcome to flask_apscheduler demo', 200
 
# @app.route('/run-tasks')
# def run_tasks():
#     for i in range(10):
#         app.apscheduler.add_job(func=scheduled_task, trigger='date', args=[i], id='j'+str(i))
 
#     return 'Scheduled several long running tasks.', 200

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
         
app.run(host='0.0.0.0', port=12345)
