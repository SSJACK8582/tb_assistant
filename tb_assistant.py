# coding=UTF-8
import json
import time
import hashlib
from log import logger

app_key = '12574478'
user_agent = 'Mozilla/5.0 (Linux; Android 9; MI 6 MIUI/20.6.18) AppleWebKit/537.36 (KHTML, like Gecko)'
headers = {'User-Agent': user_agent}


def get_sign(session, t, data):
    m_h5_tk = session.cookies.get('_m_h5_tk', '')
    token = m_h5_tk[:32]
    string = '&'.join([token, str(t), app_key, str(data)])
    sign = hashlib.md5(string.encode('utf-8')).hexdigest()
    return sign


def get_order(session, id, num, sku_id):
    url = 'https://h5api.m.taobao.com/h5/mtop.trade.order.build.h5/4.0/'
    buy_param = '{}_{}_{}'.format(id, num, sku_id)
    data = json.dumps({'buyNow': 'true', 'buyParam': buy_param,
                       'exParams': '{"requestIdentity":"#t#ip##_h5_web_unknown","tradeProtocolFeatures":"5","userAgent":"' + user_agent + '"}'})
    t = int(time.time() * 1000)
    sign = get_sign(session, t, data)
    payload = {
        'appKey': app_key,
        't': t,
        'sign': sign,
        'api': 'mtop.trade.order.build.h5',
        'data': data
    }
    try:
        resp = session.get(url=url, params=payload, data=data)
        resp_json = json.loads(resp.text)
        logger.info(resp_json)
        order_info = resp_json.get('data')
        return order_info
    except Exception as e:
        logger.error(e)


def create_order(session, order_info):
    submit_ref = order_info.get('data', {}).get('confirmOrder_1', {}).get('fields', {}).get('secretValue')
    data = '{"params":"{\\"data\\":\\"{'
    key_list1 = ['item_', 'address_', 'postageInsurance_', 'promotion_', 'memo_', 'anonymous_', 'invoice_',
                 'itemInfo_', 'confirmOrder_', 'ncCheckCode_', 'submitOrder_', 'deliveryMethod_', 'tbgold_']
    key_list2 = ['linkage', 'hierarchy', 'endpoint']
    for keys in order_info['data']:
        for key in key_list1:
            if key in keys:
                item = order_info['data'][keys]
                if key == 'postageInsurance_':
                    keys = keys.replace('postageInsurance_', 'service_yfx_')
                item_dict = json.dumps(item, ensure_ascii=False, separators=(',', ':')).replace('"', '\\\"').replace(
                    '\\\\"', '\\\\\\\"')
                if key == 'address_':
                    item_dict = item_dict.replace('\\\\\\\\\"', '\\\\\\\\\\\\\\\"')
                data += '\\\\\\"{}\\\\\\":{},'.format(keys, item_dict)
    data = data[:-1] + '}\\",'
    for keys in order_info:
        for key in key_list2:
            if key in keys:
                item = order_info[keys]
                item_dict = json.dumps(item, ensure_ascii=False, separators=(',', ':')).replace('"', '\\\"').replace(
                    '\\\\"', '\\\\\\\"')
                data += '\\\\\\"{}\\\\\\":{},'.format(keys, item_dict)
    data = data[:-1]
    t = int(time.time() * 1000)
    sign = get_sign(session, t, data)
    url = 'https://h5api.m.taobao.com/h5/mtop.trade.order.create.h5/4.0/'
    payload = {
        'appKey': app_key,
        't': t,
        'sign': sign,
        'api': 'mtop.trade.order.create.h5',
        'submitref': submit_ref
    }
    try:
        resp = session.post(url=url, params=payload, data=json.dumps(data))
        logger.info(resp.text)
    except Exception as e:
        logger.error(e)
