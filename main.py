# coding=UTF-8
import asyncio
import requests
import tb_account
import tb_assistant
from log import logger

app_key = '12574478'
user_agent = 'Mozilla/5.0 (Linux; Android 9; MI 6 MIUI/20.6.18) AppleWebKit/537.36 (KHTML, like Gecko)'
headers = {'User-Agent': user_agent}


if __name__ == '__main__':
    logger.info('Power By JACK')
    id = '638456093357'
    num = '1'
    sku_id = '4950230150476'
    if not tb_account.load_cookies():
        tb_account.login_by_qr_code()
        # username = ''
        # password = ''
        # loop = asyncio.get_event_loop()
        # task = asyncio.ensure_future(tb_account.login_by_username_password(username, password))
        # loop.run_until_complete(task)
    account_list = tb_account.get_account()
    for account in account_list:
        cookies = tb_account.string_to_cookies(account[1])
        session = requests.session()
        session.headers = headers
        session.cookies = cookies
        if '_m_h5_tk' not in account[1]:
            tb_account.get_m_h5_tk(session)
        if tb_account.check_login('cookies', session):
            order_info = tb_assistant.get_order(session, id, num, sku_id)
            tb_assistant.create_order(session, order_info)
