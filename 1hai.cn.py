import hashlib
import time

import requests
import datetime
import random
import math
import re

import xlutils
import xlrd as xlrd
import xlwt as xlwt
from lxml.html import etree
import execjs
import json
import openpyxl
from pip._vendor.retrying import retry


class Yihai:
    def __init__(self):
        # 起始页
        self.start_url = 'https://booking.1hai.cn/?from=index'
        # 获取门店列表
        self.getstore_url = "https://booking.1hai.cn/Order/Address/SearchStore"
        # 获取车辆种类列表
        self.cartype_url = 'https://booking.1hai.cn/Order/FirstStep/LoadCarTypeData'
        # 认证时间是否正常
        self.validate_url = 'https://booking.1hai.cn/Order/Validate/Index'
        self.update_query_cookie_url = 'https://booking.1hai.cn/'
        # 更新token
        self.refreshToken = 'https://booking.1hai.cn/Order/Common/RefreshToken'

        # cityId=5,get请求
        self.getCarConfig = "https://booking.1hai.cn/Order/FirstStep/CartypeConfig"  # post
        self.SecondStep = "https://booking.1hai.cn/Order/SecondStep?from=index"

    def get_cookies(self):
        """
        获取cookies
        :return:
        """
        response = requests.get(self.start_url)
        if response.status_code == 200:
            set_cookie = response.headers['Set-Cookie']
            city_list = self.city_list(response.text)
            need_list = ['1010902oday', '1010902oref', '1010902r', 'ASP.NET_SessionId', 'fr_safety']
            cookies = self.parse_setcookie(set_cookie, need_list)

            token = \
                re.findall('<input name="__RequestVerificationToken" type="hidden" value="(.*?)" />', response.text)[0]
            return cookies, token, city_list
        else:
            print(f'错误响应码为：{response.status_code}')

    def first_request(self, cookies, token):
        print("将token添加到cookies")
        sign_1 = self.generate_sign()
        sign_2 = self.generate_sign()
        requests_id = '|' + sign_1 + '.' + sign_2
        headers = {
            '__RequestVerificationToken': token,
            'Request-Id': requests_id,
            'Referer': 'https://booking.1hai.cn/?from=index',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }
        timestamp, uct_date = self.generate_timestamp()
        ai_session = self.generate_sign() + '|' + timestamp + '|' + timestamp
        ai_user = self.generate_sign() + '|' + uct_date
        js = 'true'
        cookies = {
            **cookies,
            'ai_session': ai_session,
            'ai_user': ai_user,
            'js': js,
        }
        data = {'PriceLevel': '', 'Brands': '', 'Gear': '', 'Type': '', 'Seat': '', 'SortBy': '',
                'IsEnterprise': 'false'}
        response = requests.post(self.cartype_url, data=data, cookies=cookies, headers=headers)
        # print(response.status_code)
        # print(response.text)
        # self.parse_html(response.text)
        set_cookie = response.headers['Set-Cookie']
        need_list = ['1010902oat', '1010902tk']
        update_cookies = self.parse_setcookie(set_cookie, need_list)
        cookies.update(update_cookies)

        cookies['sensorsdata2015jssdkcross'] = self.sensorsdata2015jssdkcross()
        return cookies, sign_1

    def validate_request(self, cookies, token, sign_1, store, scrapy_time, hour):
        """
        效验前面的参数是否正确
        正常响应是： {"IsSuccess":true,"Message":"000000"}
        :param store:
        :return:
        """
        data = {'PickUpServiceAddress': '', 'IsSendService': 'false', 'ReturnServiceAddress': '',
                'IsReturnService': 'false',
                'PickUpDate': scrapy_time[0],
                'ReturnDate': scrapy_time[2],
                'PickUpCityId': '77',
                'PickUpStoreId': store[0],
                'ReturnCityId': '77',
                'ReturnStoreId': store[0],
                'FlightNumber': '', 'PickUpServiceDto.Lat': '', 'PickUpServiceDto.Lng': '', 'ReturnServiceDto.Lat': '',
                'ReturnServiceDto.Lng': '', 'PickUpServiceDto.Address': '', 'ReturnServiceDto.Address': '',
                'PickUpServiceDto.IsFree': 'False', 'ReturnServiceDto.IsFree': 'False',
                'ReturnHour': scrapy_time[1],
                'PickUpHour': scrapy_time[3],
                'ReturnMinute': '0', 'PickUpMinute': '0'}
        sign_2 = self.generate_sign()
        requests_id = '|' + sign_1 + '.' + sign_2
        headers = {
            '__RequestVerificationToken': token,
            'Request-Id': requests_id,
            'Content-Type': 'application/json;charset=UTF-8',
            'Referer': 'https://booking.1hai.cn/?from=index',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }
        response = requests.post(url='https://booking.1hai.cn/Order/Validate/Index', data=json.dumps(data),
                                 cookies=cookies, headers=headers)
        json_ob = json.loads(response.text, strict=False)
        print(response.status_code)
        print('校验响应= ', response.text)
        return json_ob

    def update_store_time_request(self, cookies, token, sign_1, store_tuple, scrapy_time):
        """
        第二次请求
        :param scrapy_time:
        :param store_tuple:
        :param token:
        :return:
        """
        print('更新时间和门店获取新cookie')
        sign_2 = self.generate_sign()
        requests_id = '|' + sign_1 + '.' + sign_2
        headers = {
            'Request-Id': requests_id,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://booking.1hai.cn/?from=index',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }

        data = {
            "PickUpCity": "阿克苏",
            "PickUpStoreName": "阿克苏机场便捷点",
            "PickUpServiceAddress": "请输入送车上门地址",
            "IsSendService": "false",
            "ReturnCity": "阿克苏",
            "ReturnStoreName": "阿克苏机场便捷点",
            "ReturnServiceAddress": "请输入上门取车地址",
            "IsReturnService": "false",
            "PickUpDate": scrapy_time[0],
            "ReturnDate": scrapy_time[2],
            "PickUpCityId": "441",
            "PickUpStoreId": store_tuple[0],
            "ReturnCityId": "441",
            "ReturnStoreId": store_tuple[0],
            "FlightNumber": "",
            "PickUpServiceDto.Lat": "0",
            "PickUpServiceDto.Lng": "0",
            "ReturnServiceDto.Lat": "0",
            "ReturnServiceDto.Lng": "0",
            "PickUpServiceDto.Address": "",
            "ReturnServiceDto.Address": "",
            "PickUpServiceDto.IsFree": "False",
            "ReturnServiceDto.IsFree": "False",
            "IsEnterprise": "False",
            "ReturnHour": scrapy_time[1],
            "PickUpHour": scrapy_time[3],
            "ReturnMinute": "0",
            "PickUpMinute": "0",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = requests.post(self.update_query_cookie_url, cookies=cookies, data=data, headers=headers)  # ,

        set_cookie = response.headers['Set-Cookie']
        need_list = ['1010902oday', '1010902r', '1010902pr']
        update_cookies = self.parse_setcookie(set_cookie, need_list)
        cookies.update(update_cookies)
        return sign_1, cookies

    def cartype_data_request(self, cookies, sign_1, token, ws, store, scrapy_time, city):
        """
        第三次请求
        :param store:
        :param ws:
        :param sign_1:
        :param token:
        :return:
        """
        print('请求数据')
        data = {'PriceLevel': '', 'Brands': '', 'Gear': '', 'Type': '', 'Seat': '', 'SortBy': '',
                'IsEnterprise': 'false'}
        headers = {
            '__RequestVerificationToken': token,
            'Request-Id': '|' + sign_1 + '.' + self.generate_sign(),
            'Referer': 'https://booking.1hai.cn/?from=index',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }
        response = requests.post(self.cartype_url, data=data, cookies=cookies, headers=headers)
        self.LoadCarTypeData_html(self, response.text, ws, store, scrapy_time, city)

    def second_step(self, cookies, sign_1, token):
        data = {'PriceLevel': '', 'Brands': '', 'Gear': '', 'Type': '', 'Seat': '', 'SortBy': '',
                'IsEnterprise': 'false'}
        headers = {
            '__RequestVerificationToken': token,
            'Request-Id': '|' + sign_1 + '.' + self.generate_sign(),
            'Referer': 'https://booking.1hai.cn/?from=index',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }
        response = requests.get(self.SecondStep, None, cookies=cookies, headers=headers)
        self.dealwith_html()

    @staticmethod
    def parse_setcookie(set_cookie, need_list):
        """
        解析setcookie
        :param set_cookie: 响应的set_cookie
        :param need_list: 需要解析的字段列表
        :return:
        """
        set_cookie_list = set_cookie.replace(',', ';').split(';')
        cookie = {}
        for k in set_cookie_list:
            for i in need_list:
                if i in k:
                    k_v = k.split('=', 1)
                    k = k_v[0].strip(' ')
                    v = k_v[1].strip(' ')
                    cookie[k] = v
        return cookie

    @staticmethod
    def generate_timestamp():
        """
        生成时间戳和 UTC 时间戳
        :return:
        """
        now_time = datetime.datetime.now()
        timestamp = str(datetime.datetime.timestamp(now_time) * 1000)
        utc_time = str(now_time.utcnow())
        utc_time_list = utc_time.split()
        utc_date = utc_time_list[0] + 'T' + utc_time_list[-1][:-3] + 'Z'
        print(f'时间戳： {timestamp}  UTC时间:   {utc_date}')
        return timestamp, utc_date

    @staticmethod
    @retry
    def generate_sign():
        """
        生成一段加密参数
        :return:
        """
        salt = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        t = 10737418245665 * random.random()
        e = ''
        while t > 0:
            e += salt[math.ceil(t % 64)]
            t = int(t / 64)
        return e

    @staticmethod
    def LoadCarTypeData_html(self, text, ws, store, scrapy_time,city):
        """
        解析HTML
        :param city:
        :param store:
        :param ws:
        :param text:
        :return:
        """
        html_xpath = etree.HTML(text)
        data = html_xpath.xpath('//div[@class="wraplist"]/div')
        for dt in data:
            lis = dt.xpath('.//li')
            car_name = lis[1].xpath('.//p[1]/span/text()')[0]
            price = lis[2].xpath('.//*[@class="total-price"]/text()')[0]
            config_request = lis[1].xpath('.//p[2]/a/@data-cid')[0]
            # deploy = lis[1].xpath(".//p[@class='car-introinfo']//text()")

            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Referer': 'https://booking.1hai.cn/?from=index',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
            }
            response = requests.post(self.getCarConfig, config_request, headers=headers)
            cinfig_result = etree.HTML(response.text)
            text_data = cinfig_result.xpath("//ul[@class='current-carconfigure clear_float']//p//text()")
            config_text = "|".join(text_data).strip()
            print("城市:" + store[1])
            print("车型:" + car_name)
            print("价格:" + price)
            print("配置:" + config_text)
            ws.append((city[1],store[1], scrapy_time[0], scrapy_time[2], car_name, config_text, price))

    @staticmethod
    def dealwith_html(text):
        """
        订单第二步骤页面解析
        :param text:
        :return:
        """
        _element = etree.HTML(text)
        list_span = _element.xpath("//div[@id='baseRateDetail']/span")
        car_name = _element.xpath("//div[@class='car-name']/text()")[1].strip()
        print("匹配成功")
        print("车型", "时间", "价格")
        for span in list_span:
            lis_p = span.xpath('.//p')
            # strip() 方法用于移除字符串头尾指定的字符（默认为空格或换行符）或字符序列。
            time = lis_p[0].text.strip().strip('(周|星期|礼拜)[1-7一二三四五六七天日]').strip()
            price = lis_p[1].text.strip().strip('￥')
            print(car_name, time, price)

    @staticmethod
    def city_list(text):
        # 解析获取城市列表
        element = etree.HTML(text)
        citys = element.xpath("//li/div[@class='inner-box']/dl/div/dd")
        city_list = {}
        for city in citys:
            city_id = str(city.xpath(".//span//@data-id")[0])
            city_name = city.xpath(".//span")[0].text
            city_list[city_id] = city_name
        # dict排序
        city_list = sorted(city_list.items(), key=lambda item: item[0])
        return city_list

    @staticmethod
    def getstore_list(text):
        element = etree.HTML(text)
        store_list = element.xpath("//dl[@class='dl-mendian clearfix']/dd")
        smap = {}
        for store in store_list:
            sid = str(store.xpath(".//span/@sid")[0])
            sname = store.xpath(".//span/em/text()")[0]
            smap[sid] = sname

        return smap

    @staticmethod
    def sensorsdata2015jssdkcross():
        """
        获取 sensorsdata2015jssdkcross 加密验证码
        :return:
        """
        height = 1080
        width = 1920
        n = str(height * width)

        # e = hex(round(time.time()*1000)).strip('0x') + '0'
        # t = hex(int(str(random.random()).replace('.', '')))

        e = execjs.compile("""var e = function() {
                        for (var e = 1 * new Date, t = 0; e == 1 * new Date; )
                            t++;
                        return e.toString(16) + t.toString(16)
                    }""")
        e = e.call('e')

        t = execjs.compile("""t = function() {
                return Math.random().toString(16).replace(".", "")
            }""")
        t = t.call('t')

        # r = '3f604900-2073600'
        r = '3f604900'
        s = e + '-' + t + '-' + r + '-' + n + '-' + e
        print(s)
        # sensorsdata2015jssdkcross = {
        #     "distinct_id": s,
        #     "$device_id": s,
        #     "props": {
        #         "$latest_traffic_source_type": "直接流量",
        #         "$latest_referrer": "",
        #         "$latest_referrer_host": "",
        #         "$latest_search_keyword": "未取到值_直接打开"
        #     }
        # }
        sensorsdata2015jssdkcross = "%7B%22distinct_id%22%3A%22{}%22%2C%22%24device_id%22%3A%22{}%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%7D%7D".format(
            s, s)
        # print(sensorsdata2015jssdkcross)
        return sensorsdata2015jssdkcross


def main():
    """
    抓取一嗨租车
    抓包分析：
       第一次请求：
           url： https://booking.1hai.cn/?from=index
           获取初始化cookie和token
       第二次请求：
            url： https://booking.1hai.cn/Order/FirstStep/LoadCarTypeData
            获取set_cookie，变更了cookie
       第三次请求：
             url： https://booking.1hai.cn/Order/Validate/Index    （可以不要）
            这个请求对后续请求没作用，唯一的作用就是能判断 前面得到的cookie、token等参数 是否正常解密
       第三次请求：
             url： https://booking.1hai.cn/
             这个请求很重要，他会带上 我们参数， 比如门店、时间之类的参数，还会更改cookie
       第四次请求
             url： https://booking.1hai.cn/Order/FirstStep/LoadCarTypeData
             这个请求得到最终数据
    执行时 需要 调整下 two_request 方法中参数里面的日期和小时
    加密那块执行报错再执行一次，那块因为时间戳在变，做运算时可能会除不尽
    :return:
    """
    hour = 14
    scrapy_time = ['2021-02-04', hour, '2021-03-05', hour]
    yihai = Yihai()
    # 创建一个workbook对象，而且会在workbook中至少创建一个表worksheet
    # wb = openpyxl.Workbook()
    # wb.remove(wb.active)  # 删除默认表格
    book_name = '一嗨租车价格表.xlsx'
    wb = openpyxl.load_workbook(book_name)
    cookies, token, city_list = yihai.get_cookies()
    cookies, sign_1 = yihai.first_request(cookies, token)
    ws = wb.active
    # ws.append(['城市', '取车', '取车时间', '还车时间', '车型', '车辆详情', '平均价格'])
    # 遍历城市列表
    try:
        for city in city_list:
            try:
                store_map = yihai.getstore_list(requests.get(yihai.getstore_url, {"cityId": city[0]}).text)
                # store_map = {'5': "上海浦东", '799': "上海虹桥"}
                for store in store_map.items():
                    json_obj = yihai.validate_request(cookies, token, sign_1, store, scrapy_time, hour)  # 可以不参与执行，可以注释掉
                    if json_obj['IsSuccess'] is (False):
                        continue
                    sign_1, cookies = yihai.update_store_time_request(cookies, token, sign_1, store, scrapy_time)
                    # todo refreshtoken
                    yihai.cartype_data_request(cookies, sign_1, token, ws, store, scrapy_time, city)
                    time.sleep(2)
                # yihai.second_step(cookies, sign_1, token)
                print(city[1], "爬取完毕==================")
            except Exception as ex:
                continue
            finally:
                wb.save(book_name)
    finally:
        wb.close()


if __name__ == '__main__':
    main()
