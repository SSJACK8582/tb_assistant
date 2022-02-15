# coding=UTF-8
import os
import re
import sys
import json
import time
import hashlib
import requests
import configparser
from pyppeteer import launch
from log import logger

app_key = '12574478'
user_agent = 'Mozilla/5.0 (Linux; Android 9; MI 6 MIUI/20.6.18) AppleWebKit/537.36 (KHTML, like Gecko)'
headers = {'User-Agent': user_agent}


def load_cookies(file_name='config.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    string = config.get('account', 'cookies')
    cookies = string_to_cookies(string)
    if cookies:
        session = requests.session()
        session.headers = headers
        session.cookies = cookies
        if '_m_h5_tk' not in string:
            get_m_h5_tk(session)
        if check_login('cookies', session):
            return True
    return False


def get_account(file_name='config.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    return config.items('account')


def save_cookies(cookies, file_name='config.ini'):
    string = cookies_to_string(cookies)
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    config.set('account', 'cookies', string)
    with open(file_name, 'w') as f:
        config.write(f)


def string_to_cookies(string):
    try:
        item_list = string.split(';')
        cookies_dict = {}
        for item in item_list:
            if item:
                name, value = item.strip().split('=', 1)
                cookies_dict[name] = value
        cookies = requests.utils.cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
        return cookies
    except Exception as e:
        logger.error('cookies转换异常：{}'.format(e))


def cookies_to_string(cookies):
    try:
        cookies_dict = requests.utils.dict_from_cookiejar(cookies)
        string = ''
        for item in cookies_dict:
            string += item + '=' + cookies_dict[item] + ';'
        return string[:-1]
    except Exception as e:
        logger.error('cookies转换异常：{}'.format(e))


def get_sign(session, t, data):
    m_h5_tk = session.cookies.get('_m_h5_tk', '')
    token = m_h5_tk[:32]
    string = '&'.join([token, str(t), app_key, str(data)])
    sign = hashlib.md5(string.encode('utf-8')).hexdigest()
    return sign


def get_m_h5_tk(session):
    url = 'https://h5api.m.taobao.com/h5/mtop.taobao.mclaren.index.data.get.h5/1.0/?appKey={}'.format(app_key)
    try:
        session.get(url=url)
    except Exception as e:
        logger.error(e)


def get_qr_code(session):
    url = 'https://qrlogin.taobao.com/qrcodelogin/generateQRCode4Login.do'
    try:
        resp = session.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        lg_token = resp_json.get('lgToken')
        img_url = resp_json.get('url')
        login_url = 'https://login.m.taobao.com/qrcodeCheck.htm?lgToken={}'.format(lg_token)
        logger.info('二维码链接【https:{}】'.format(img_url))
        logger.info('登录链接【{}】'.format(login_url))
        return lg_token
    except Exception as e:
        logger.error(e)


def check_qr_code(session, lg_token):
    url = 'https://qrlogin.taobao.com/qrcodelogin/qrcodeLoginCheck.do?lgToken={}'.format(lg_token)
    headers['Referer'] = 'https://login.taobao.com/member/login_unusual.htm'
    try:
        resp = session.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        logger.info(resp_json)
        resp_url = resp_json.get('url')
        return resp_url
    except Exception as e:
        logger.error(e)


def check_qr_code_login(session, url):
    try:
        resp = session.get(url=url)
        if resp.url == 'https://www.taobao.com':
            return True
        else:
            return False
    except Exception as e:
        logger.error(e)


def check_login(account, session):
    url = 'https://h5api.m.taobao.com/h5/mtop.taobao.mclaren.index.data.get.h5/1.0/'
    data = json.dumps({'mytbVersion': '4.0.1', 'moduleConfigVersion': -1, 'dataConfigVersion': -1, 'requestType': 1})
    t = int(time.time() * 1000)
    sign = get_sign(session, t, data)
    payload = {
        'appKey': app_key,
        't': t,
        'sign': sign,
        'api': 'mtop.taobao.mclaren.index.data.get.h5',
        'data': data
    }
    try:
        resp = session.get(url=url, params=payload)
        result = re.findall('"淘宝账号：(.*?)"', resp.text)
        if result:
            logger.info('登录成功【{}】账号【{}】'.format(account, result[0]))
            return True
        else:
            logger.info('登录失败【{}】'.format(account))
            return False
    except Exception as e:
        logger.error(e)


def login_by_qr_code():
    session = requests.Session()
    lg_token = get_qr_code(session)
    if not lg_token:
        logger.info('获取二维码失败')
        sys.exit()
    for i in range(0, 80):
        url = check_qr_code(session, lg_token)
        if url:
            break
        time.sleep(2)
    else:
        logger.info('二维码过期，请重新获取扫描')
        sys.exit()
    if not check_qr_code_login(session, url):
        logger.info('校验二维码信息失败')
        sys.exit()
    get_m_h5_tk(session)
    if check_login('cookies', session):
        save_cookies(session.cookies)


async def login_by_username_password(username, password):
    try:
        args = {
            'headless': False,
            'dumpio': True,
            'args': ['--windows-size=720,1280', '--disable-infobars']
        }
        driver = await launch(args)
        page = await driver.newPage()
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)')
        await page.setViewport(viewport={'width': 450, 'height': 800})
        await page.evaluateOnNewDocument(
            "() => { Object.defineProperties(navigator, { webdriver: { get: () => false }})}")
        await page.evaluateOnNewDocument("() => { Object.defineProperty(navigator, 'plugins', { get: () => []})}")
        await page.evaluateOnNewDocument(
            "() => { Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh']})}")
        await page.goto('https://main.m.taobao.com/cart/index.html')
        await page.waitFor('iframe')
        iframe = page.frames[1]
        await iframe.click('#login-form > div.login-blocks.login-links > a')
        await iframe.type('#fm-login-id', username, {'delay': 50})
        await iframe.type('#fm-login-password', password, {'delay': 50})
        await iframe.click('#login-form > div.login-blocks.block9 > div > label')
        await iframe.click('#login-form > div.fm-btn > button')
        await iframe.waitFor(2000)
        await page.waitFor('#cart_sticky_fixed_bar')
        cookies = await page.cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        cookies = requests.utils.cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
        save_cookies(cookies)
    except Exception as e:
        logger.error(e)
