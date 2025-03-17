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
global_time = 900


def autoReset():
    log.info('waiting server start')
    time.sleep(1)
    while True:
        log.info('Telling server not to update the status for the next 900 seconds')
        time.sleep(900)
        if data.dget('status') != 1:
            data.dset('status', 1)
            log.info('auto reset success')
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
    ot = data.data['other']
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
        user=ot['user'],
        status_name=stat['name'],
        status_desc=stat['desc'],
        status_color=stat['color'],
    )


@app.route('/style.css')
def style_css():
    response = make_response(render_template(
        'style.css',
        bg=data.data['other']['background'],
        alpha=data.data['other']['alpha']
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


@app.route('/set', methods=['PUT'])
def set_normal():
    showip(request, '/set')
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
        log.info('set success')
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


@app.route('/set/<secret>/<int:status>')
def set_path(secret, status):
    showip(request, f'/set/{secret}/{status}')
    secret = escape(secret)
    log.info(f'status: {status}, secret: "{secret}"')
    secret_real = data.dget('secret')
    if secret == secret_real:
        data.dset('status', status)
        log.info('set success')
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

if __name__ == '__main__':
    data.load()
    threading.Thread(target=autoReset).start()
    app.run(
        host=data.data['host'],
        port=data.data['port'],
        debug=data.data['debug']
    )
