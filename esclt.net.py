import traceback

import pymysql as pymysql
import requests as re
from lxml.html import etree
import time


class Esclt:

    def __init__(self, index):
        self.homeUrl = f"https://www.esclt.net/buycar?pageIndex={index}&keywords=&cx=&dm=&mc=&bh=&jc=&lx=&cl=&pl=&px=&jgfwmin=&jgfwmax=&zsfl=zxcl"
        self.baseUrl = "https://www.esclt.net"
        self.headers = {
            "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            "Accept-Encoding": "gzip, deflate, br",
            'Referer': 'https://www.esclt.net/',
            "Accept-Language": "zh - CN, zh;q = 0.9",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        }
        self.cookie = {
            "JSESSIONID": "1783CA2C82379C4A68E424EBF935790A",
            "cookiename": "931000398ABA743F307217EB2814A6F8",
            "UM_distinctid": "177f1718b9cce-0087930e1edd758-4c3f217f-1fa400-177f1718b9d4a",
            "CNZZDATA1278830134": "1841848300-1614659024-%7C1615365017"
        }

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
    def page_index(total):
        ls = []
        for i in range(4, total + 1, 1):
            ls.append(Esclt(i).homeUrl)
        return ls

    @staticmethod
    def db_conn(data):
        db = pymysql.connect(host="8.136.12.232", database="spiders", user="root", password="123456", port=3306)
        table = "car_model"
        # data = {
        #     "model": "车型",
        #     "model_cn": "车型全称",
        #     "car_model": "车辆型号",
        #     "twice_price": 5.00,
        #     "all_model": "车辆品牌加型号",
        #     "brand": "车辆品牌",
        #     "type": "车辆类型",
        #     "output_volume": 1000,
        #     "fuel_type": "燃料种类",
        #     "factory_price": 5.00,
        #     "level": "级别",
        #     "year": "2018",
        #     "seat": 7,
        # }
        values = data.values()
        cloum = ",".join(data.keys())
        values = ",".join(['%s'] * len(data))
        db_cursor = db.cursor()
        sql = "INSERT INTO {table} ({cloums}) VALUES ({values}) ".format(table=table, cloums=cloum, values=values)
        try:
            db_cursor.execute(sql, tuple(data.values()))
            print("SUCCESSFUL->")
            db.commit()
        except Exception:
            print("FAILED")
            traceback.print_exc()
            db.rollback()
        db.close()


def main():
    esclt = Esclt(1)
    for url in esclt.page_index(10):
        print(url)
        response = re.get(url, None, cookies=esclt.cookie, headers=esclt.headers)
        car_info_url_list = etree.HTML(response.text).xpath('//div[@id="buycarList"]/dl/dd/a/@href')
        if response.status_code == 200:
            set_cookie = response.headers['Set-Cookie']
            need_list = ['CNZZDATA1278830134', 'cookiename', 'JSESSIONID', 'UM_distinctid']
            new_cookie = esclt.parse_setcookie(set_cookie, need_list)
        for info_url_last in car_info_url_list:
            info_url_all = esclt.baseUrl + info_url_last.strip('\'')
            print(info_url_all)
            info_html = re.get(info_url_all, None, cookies=new_cookie, headers=esclt.headers)
    # info_html = re.get("https://www.esclt.net/car21013.html", None, cookies=esclt.cookie, headers=esclt.headers)
            HTML = etree.HTML(info_html.text)
            try:
                pinpai = HTML.xpath('//div[@class="subNav"]/a[3]/text()')[0]
                chexi = HTML.xpath('//div[@class="subNav"]/a[4]/text()')[0]

                # chexing = pinpai + ',' + chexi
                chexing_all = HTML.xpath('//div[@class="swiper-slide"]/img/@alt')[0]

                chejia = HTML.xpath('//div[@class="carshowJgBox rel"]/strong/text()')[0].replace('¥', '')
                car_box = HTML.xpath('//div[@id="clDetail"]/div[@class="contentBox"][1]/dl/dd')
                chepinpai = car_box[0].text.replace('车辆品牌：', '')
                cheliangxinghao = car_box[1].text.replace('车辆型号：', '')
                cheliangleixing = car_box[16].text.replace('车辆类型：', '')
                pailiang = car_box[12].text.replace('排量(ml)：', '')
                ranliao = car_box[19].text.replace('燃料种类：', '')

                chuchangjiage=''
                jibie = ''
                niankuan = ''
                zuoweishu = ''
                chuchangjiage = HTML.xpath('//table[@id="cx-tab"]//td[@id="zdjg"]')[0].text
                jibie = HTML.xpath('//table[@id="cx-tab"]//td[@id="cljb"]')[0].text
                niankuan = HTML.xpath('//table[@id="cx-tab"]//td[@id="nk"]')[0].text
                zuoweishu = HTML.xpath('//table[@id="cx-tab"]//td[@id="zws"]')[0].text
            except IndexError:
                traceback.print_exc()
            data = {}
            data["model"] = chexi
            data["model_cn"] = chexing_all
            data["model_num"] = cheliangxinghao
            data["twice_price"] = chejia
            data["all_model"] = chepinpai + cheliangxinghao
            data["brand"] = chepinpai
            data["output_volume"] = pailiang
            data["fuel_type"] = ranliao
            data["factory_price"] = chuchangjiage
            data["level"] = jibie
            data["year"] = niankuan
            data['type'] = cheliangleixing
            data["seat"] = zuoweishu
            print(data)
            esclt.db_conn(data=data)


if __name__ == '__main__':
    main()
