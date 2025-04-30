# coding: utf-8
import utils as log
from data import data as data_init
from flask import Flask, render_template, request, make_response, jsonify
import time
import threading
import time
from datetime import datetime


data = data_init()
app = Flask(__name__)
my_status = 0
device1_wait_time, device2_wait_time, device3_wait_time = data.dget('device1_wait_time'), data.dget('device2_wait_time'), data.dget('device3_wait_time')
device1_time_update, device2_time_update, device3_time_update = False, False, False
device1_status = "电脑离线"
device1_status_int = 0
device1_app = ""
device2_status = "红米K50 Ultra离线"
device2_status_int = 0
device2_app = ""
device3_status = "一加Ace Pro离线"
device3_status_int = 0
device3_app = ""
sleep = False
current_desktop_background = ""
current_mobile_background = ""
last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def autoSwitchBackground():
    global current_desktop_background, current_mobile_background

    if my_status and (time.localtime().tm_hour >= 19 or time.localtime().tm_hour < 7):
        #night online
        current_desktop_background = data.dget('desktopbgnight')
        current_mobile_background = data.dget('mobilebgnight')
        return

    if not my_status and (time.localtime().tm_hour >= 19 or time.localtime().tm_hour < 7):
        #night offline
        current_desktop_background = data.dget('desktopbgnightsleep')
        current_mobile_background = data.dget('mobilebgnightsleep')
        return

    if my_status and (7 <= time.localtime().tm_hour < 19):
        #day online
        current_desktop_background = data.dget('desktopbgday')
        current_mobile_background = data.dget('mobilebgday')
        return

    if not my_status and (7 <= time.localtime().tm_hour < 19):
        #day offline
        current_desktop_background = data.dget('desktopbgdaysleep')
        current_mobile_background = data.dget('mobilebgdaysleep')
        return
    
    log.error('[Auto Switch Background] error:\n status: {my_status}, hour: ' + time.localtime().tm_hour)


def autoSleep():
    global my_status, sleep
    if not sleep:
        if not device1_status_int and not device2_status_int and not device3_status_int:
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
                log.info('Device 1 has not update status for long time. Reseted.')
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
                device2_status="红米K50 Ultra离线"
                device2_status_int = 0
                device2_app=""
                log.info('Device 2 has not update status for long time. Reseted.')
            else:
                log.info('Device 2 current status already is 0(offline) no change')
            autoSleep()
            autoSwitchBackground()

def device3Timer():
    global device3_status, device3_status_int, device3_app, device3_wait_time, device3_time_update
    log.info('[Device 3 Timer]: waiting server start')
    time.sleep(1)
    while True:

        if sleep:
            time.sleep(15)
            autoSwitchBackground()
            continue

        if device3_time_update:
            device3_time_update = False
            log.info('detected device 3 status changed. reset timer')
            device3_wait_time = data.dget('device3_wait_time')

        if device3_wait_time > 0:
            time.sleep(1)
            device3_wait_time -= 1
        else:
            device3_wait_time = data.dget('device3_wait_time')
            log.info('Telling server not to update the device 3 status for the next 900 seconds')
            if device3_status_int:
                device3_status="红米K50 Ultra离线"
                device3_status_int = 0
                device3_app=""
                log.info('Device 3 has not update status for long time. Reseted.')
            else:
                log.info('Device 3 current status already is 0(offline) no change')
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
            'color': '255, 0, 0'
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
        device2_app=device2_app,
        device3_status=device3_status,
        device3_app=device3_app,
        last_update_time=last_update_time,
        auto_refresh_time=data.dget('auto_refresh_time')
    )

@app.route('/get_data')
def get_data():
    try:
        stat = data.data['status_list'][my_status]
    except:
        log.error("auto refresh failed!")

    return jsonify({
        "status_name": stat['name'],
        "device1_status": device1_status,
        "device1_app": device1_app,
        "device2_status": device2_status,
        "device2_app": device2_app,
        "device3_status": device3_status,
        "device3_app": device3_app,
        "status_desc": stat['desc'],
        "status_color": stat['color'],
        "last_update_time": last_update_time
    })

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


@app.route('/setdevice', methods=['POST'])
def set_device():
    global my_status, device1_status, device1_status_int, device1_app, device1_time_update, device2_status, device2_status_int, device2_app, device2_time_update, device3_status, device3_status_int, device3_app, device3_time_update, last_update_time
    showip(request, '/setdevice')
    request_data=request.get_json()
    print(request_data)
    status = request_data["status"]
    device = request_data["device"]
    try:
        status = int(status)
        device = int(device)
    except:
        return reterr(
            code='bad request',
            message="argument 'status' or 'device' must be a number"
        )
    if request_data["secret"] == data.dget('secret'):
        if device == 1:
            log.info(f'device1 status: {device1_status_int} -> {status}, app: {device1_app} -> {request_data["app"] if status else "ignored"}')
            if status == 0:
                device1_status = "电脑离线"
                device1_status_int = 0
                device1_app = ""
                autoSleep()
            elif status == 1:
                device1_status = "电脑在线: "
                device1_status_int = 1
                device1_app = request_data["app"]
                my_status = 1
                device1_time_update = True
                wakeup()
            else:
                return reterr(
                    code='bad request',
                    message='status not found'
                )
        
        elif device == 2:
            log.info(f'device2 status: {device2_status_int} -> {status}, app: {device2_app} -> {request_data["app"] if status else "ignored"}')
            if status == 0:
                device2_status = "红米K50 Ultra离线"
                device2_status_int = 0
                device2_app = ""
                autoSleep()
            elif status == 1:
                device2_status = "红米K50 Ultra在线: "
                device2_status_int = 1
                device2_app = request_data["app"]
                my_status = 1
                device2_time_update = True
                wakeup()
            else:
                return reterr(
                    code='bad request',
                    message='status cant bigger than 1'
                )

        elif device == 3:
            log.info(f'device3 status: {device3_status_int} -> {status}, app: {device3_app} -> {request_data["app"] if status else "ignored"}')
            if status == 0:
                device3_status = "一加Ace Pro离线"
                device3_status_int = 0
                device3_app = ""
                autoSleep()
            elif status == 1:
                device3_status = "一加Ace Pro在线: "
                device3_status_int = 1
                device3_app = request_data["app"]
                my_status = 1
                device3_time_update = True
                wakeup()
            else:
                return reterr(
                    code='bad request',
                    message='status cant bigger than 1'
                )

        else:
            return reterr(
                code='bad request',
                message='device num cant bigger than 3'
            )
        
        last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
    autoSwitchBackground()
    threading.Thread(target=device1Timer).start()
    threading.Thread(target=device2Timer).start()
    threading.Thread(target=device3Timer).start()
    app.run(
        host=data.data['host'],
        port=data.data['port'],
        debug=data.data['debug']
    )
