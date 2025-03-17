#!/usr/bin/python3
# coding: utf-8
import utils as log
from data import data as data_init
from flask import Flask, render_template, request, url_for, redirect, flash, make_response
from markupsafe import escape
import json
import time
import threading

data = data_init()
app = Flask(__name__)
wait_time = 900
time_update = False
device1_status = "电脑离线"
device1_app = ""
device2_status = "手机离线"
device2_app = ""

def autoReset():
    global device1_status, device1_app, device2_status, device2_app, wait_time, time_update
    log.info('waiting server start')
    time.sleep(1)
    while True:
        if time_update:
            log.info('detected status changed. reset timer')
            wait_time = 900

        if wait_time > 0:
            time.sleep(1)
            wait_time -= 1
        else:
            log.info('Telling server not to update the status for the next 900 seconds')
            if data.dget('status') != 1:
                data.dset('status', 1)
                device1_status="电脑离线"
                device1_app=""
                device2_status="手机离线"
                device2_app=""
                log.info('too long time not update status. auto reset')
            else:
                log.info('current status is 0(offline) no changes')


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
    info = data.data['info']
    try:
        stat = data.data['status_list'][data.data['status']]
    except:
        stat = {
            'name': '未知',
            'desc': '未知的标识符，可能是配置问题。',
            'color': 'error'
        }
    return render_template(
        'index.html',
        user=info['user'],
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
        bg=data.data['info']['background'],
        alpha=data.data['info']['alpha']
    ))
    response.mimetype = 'text/css'
    return response


@app.route('/query')
def query():
    data.load()
    showip(request, '/query')
    st = data.data['status']
    # stlst = data.data['status_list']
    try:
        stinfo = data.data['status_list'][st]
    except:
        stinfo = {
            'status': st,
            'name': '未知'
        }
    ret = {
        'success': True,
        'status': st,
        'info': stinfo
    }
    return log.format_dict(ret)


@app.route('/get/status_list')
def get_status_list():
    showip(request, '/get/status_list')
    stlst = data.dget('status_list')
    return log.format_dict(stlst)


@app.route('/setstatus', methods=['PUT'])
def set_normal():
    showip(request, '/setstatus')
    status = escape(request.args.get("status"))
    try:
        status = int(status)
    except:
        return reterr(
            code='bad request',
            message="argument 'status' must be a number"
        )
    secret = escape(request.args.get("secret"))
    log.info(f'status: {status}, secret: "{secret}"')
    secret_real = data.dget('secret')
    if secret == secret_real:
        data.dset('status', status)
        log.info(f'set status to {status} success')
        ret = {
            'success': True,
            'code': 'OK',
            'set_to': status
        }
        return log.format_dict(ret)
    else:
        return reterr(
            code='not authorized',
            message='invaild secret'
        )
    

@app.route('/setdevice', methods=['PUT'])
def set_device():
    global device1_status, device1_app, device2_status, device2_app
    showip(request, '/setdevice')
    if escape(request.args.get("secret")) == data.dget('secret'):
        if escape(request.args.get("device")) == "1":
            log.info(f'device1_status: "{device1_status}", device1_app: "{device1_app}"')
            device1_status = escape(request.args.get("status"))
            device1_app = escape(request.args.get("app"))
            log.info(f'set device1 status to "{device1_status}", app to "{device1_app}"')
            ret = {
            'success': True,
            'code': 'OK'
            }
            return log.format_dict(ret)
        
        elif escape(request.args.get("device")) == "2":
            log.info(f'device2_status: {device2_status}, device2_app: "{device2_app}"')
            device2_status = escape(request.args.get("status"))
            device2_app = escape(request.args.get("app"))
            log.info(f'set device2 status to "{device2_status}", app to "{device2_app}"')
            ret = {
            'success': True,
            'code': 'OK'
            }
            return log.format_dict(ret)
        
        return reterr(
            code='bad request',
            message='device num cant bigger than 3'
        )

    else:
        return reterr(
            code='not authorized',
            message='invaild secret'
        )


if __name__ == '__main__':
    data.load()
    threading.Thread(target=autoReset).start()
    app.run(
        host=data.data['host'],
        port=data.data['port'],
        debug=data.data['debug']
    )
