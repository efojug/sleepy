# coding: utf-8
import utils as log
from data import data as data_init
from flask import Flask, render_template, request, url_for, redirect, flash, make_response
from markupsafe import escape
import json
import time
import threading
import time


data = data_init()
app = Flask(__name__)
my_status = 0
device1_wait_time, device2_wait_time = data.dget('device1_wait_time'), data.dget('device2_wait_time')
device1_time_update, device2_time_update = False, False
device1_status = "电脑离线"
device1_status_int = 0
device1_app = ""
device2_status = "手机离线"
device2_status_int = 0
device2_app = ""
sleep = False
current_desktop_background = "./static/desktopbgdaysleep.jpg"
current_mobile_background = "./static/mobilebgdaysleep.jpg"


def autoSwitchBackground():
    global current_desktop_background, current_mobile_background
    if my_status and (time.localtime().tm_hour >= 19 or time.localtime().tm_hour < 7):
        #night online
        current_desktop_background = data.dget('desktopbgnight')
        current_mobile_background = data.dget('mobilebgnight')
    elif not my_status and (time.localtime().tm_hour >= 19 or time.localtime().tm_hour < 7):
        #night offline
        current_desktop_background = data.dget('desktopbgnightsleep')
        current_mobile_background = data.dget('mobilebgnightsleep')
    elif my_status and (7 <= time.localtime().tm_hour < 19):
        #day online
        current_desktop_background = data.dget('desktopbgday')
        current_mobile_background = data.dget('mobilebgday')
    else:
        #day offline
        current_desktop_background = data.dget('desktopbgdaysleep')
        current_mobile_background = data.dget('mobilebgdaysleep')


def autoSleep():
    global my_status, sleep
    if not sleep:
        if not device1_status_int and not device2_status_int:
            my_status = 0
            log.info('All devices are offline, set status to 0')
            log.info('server sleeping...')
            sleep = True

def wakeup():
    global sleep
    if sleep:
        sleep = False
        log.info('server wakeup')

def device1Timer():
    global device1_status, device1_status_int, device1_app, device1_wait_time, device1_time_update
    log.info('[Device 1 Timer]: waiting server start')
    time.sleep(1)
    while True:

        if sleep:
            time.sleep(15)
            autoSwitchBackground()
            continue

        if device1_time_update:
            device1_time_update = False
            log.info('detected device 1 status changed. reset timer')
            device1_wait_time = data.dget('device1_wait_time')

        if device1_wait_time > 0:
            time.sleep(1)
            device1_wait_time -= 1
        else:
            device1_wait_time = data.dget('device1_wait_time')
            log.info('Telling server not to update the device 1 status for the next 900 seconds')
            if device1_status_int:
                device1_status="电脑离线"
                device1_status_int = 0
                device1_app=""
                log.info('Device 1 has not updated its status for a long time. Reseted.')
            else:
                log.info('Device 1 current status already is 0(offline) no change')
            autoSleep()
            autoSwitchBackground()


def device2Timer():
    global device2_status, device2_status_int, device2_app, device2_wait_time, device2_time_update
    log.info('[Device 2 Timer]: waiting server start')
    time.sleep(1)
    while True:

        if sleep:
            time.sleep(15)
            autoSwitchBackground()
            continue

        if device2_time_update:
            device2_time_update = False
            log.info('detected device 2 status changed. reset timer')
            device2_wait_time = data.dget('device2_wait_time')

        if device2_wait_time > 0:
            time.sleep(1)
            device2_wait_time -= 1
        else:
            device2_wait_time = data.dget('device2_wait_time')
            log.info('Telling server not to update the device 2 status for the next 900 seconds')
            if device2_status_int:
                device2_status="手机离线"
                device2_status_int = 0
                device2_app=""
                log.info('Device 2 has not updated its status for a long time. Reseted.')
            else:
                log.info('Device 2 current status already is 0(offline) no change')
            autoSleep()
            autoSwitchBackground()


def reterr(code, message):
    ret = {
        'success': False,
        'code': code,
        'message': message
    }
    log.error(f'{code} - {message}')
    return log.format_dict(ret)


def showip(req, msg):
    ip1 = req.remote_addr
    try:
        ip2 = req.headers['X-Forwarded-For']
        log.infon(f'- Request: {ip1} / {ip2} : {msg}')
    except:
        ip2 = None
        log.infon(f'- Request: {ip1} : {msg}')


@app.route('/')
def index():
    data.load()
    showip(request, '/')
    try:
        stat = data.data['status_list'][my_status]
    except:
        stat = {
            'name': '未知',
            'desc': '未知的标识符，可能是配置问题。',
            'color': 'error'
        }
    return render_template(
        'index.html',
        user=data.dget('user'),
        status_name=stat['name'],
        status_desc=stat['desc'],
        status_color=stat['color'],
        device1_status=device1_status,
        device1_app=device1_app,
        device2_status=device2_status,
        device2_app=device2_app
    )


@app.route('/style.css')
def style_css():
    response = make_response(render_template(
        'style.css',
        desktopbg=current_desktop_background,
        mobilebg=current_mobile_background,
        alpha=data.dget('alpha')
    ))
    response.mimetype = 'text/css'
    return response


@app.route('/setdevice', methods=['PUT'])
def set_device():
    global my_status, device1_status, device1_status_int, device1_app, device1_time_update, device2_status, device2_status_int, device2_app, device2_time_update
    showip(request, '/setdevice')
    status = escape(request.args.get("status"))
    try:
        status = int(status)
    except:
        return reterr(
            code='bad request',
            message="argument 'status' must be a number"
        )
    if escape(request.args.get("secret")) == data.dget('secret'):
        if escape(request.args.get("device")) == "1":
            log.info(f'device1_status: "{device1_status}", device1_app: "{device1_app}"')

            if status == 0:
                device1_status = "电脑离线"
                device1_status_int = 0
                device1_app = ""
                autoSleep()
            elif status == 1:
                device1_status = "电脑在线: "
                device1_status_int = 1
                device1_app = escape(request.args.get("app"))
                my_status = 1
                device1_time_update = True
                wakeup()
            else:
                return reterr(
                    code='bad request',
                    message='status cant bigger than 1'
                )

            log.info(f'set device1 status to "{device1_status}", app: "{"ignored" if status == 0 else device1_app}"')
        
        elif escape(request.args.get("device")) == "2":
            log.info(f'device2_status: {device2_status}, device2_app: "{device2_app}"')

            if status == 0:
                device2_status = "手机离线"
                device2_status_int = 0
                device2_app = ""
                autoSleep()
            elif status == 1:
                device2_status = "手机在线: "
                device2_status_int = 1
                device2_app = escape(request.args.get("app"))
                my_status = 1
                device2_time_update = True
                wakeup()
            else:
                return reterr(
                    code='bad request',
                    message='status cant bigger than 1'
                )
            
            log.info(f'set device2 status to "{device2_status}", app: "{"ignored" if status == 0 else device2_app}"')

        else:
            return reterr(
                code='bad request',
                message='device num cant bigger than 3'
            )
        
        autoSwitchBackground()
        ret = {
            'success': True,
            'code': 'OK'
            }
        return log.format_dict(ret)

    else:
        return reterr(
            code='not authorized',
            message='invaild secret'
        )


if __name__ == '__main__':
    data.load()
    threading.Thread(target=device1Timer).start()
    threading.Thread(target=device2Timer).start()
    app.run(
        host=data.data['host'],
        port=data.data['port'],
        debug=data.data['debug']
    )
