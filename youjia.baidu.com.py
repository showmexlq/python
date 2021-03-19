import traceback

import pymysql as pymysql
import requests as re
import json


class Youjia:

    def __init__(self, token, brand):
        self.chexiget = f"https://youjia.baidu.com/getseriesbybrand?token={token}&brandname={brand}"
        self.headers = {
            "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            "Accept-Encoding": "gzip, deflate, br",
            'Referer': 'https://youjia.baidu.com//',
            "Accept-Language": "zh - CN, zh;q = 0.9",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        }
        self.cookie = {
            "__yjs_duid": "1_972166a244978dcf576298c7676c81951615365196393",
            "ab_sr": "1.0.0_NjI5ODAyZDBmNjk0NzE0Zjg0NGUzYWE2MjZjYzkxNWJjZmU5ZDc2YmVmNTQ4NDY3Y2QxZTQxOGVhNThlZDM3NmQ5YWUxMmY1NTcxZTExMGRhNDhmN2YwNjhjNmI4ZGZi",
            "BA_HECTOR": "a42l8lal20a18hak531g581k40r",
            "BAIDUID": "1B345FE30ADE973F621B515BF16D0718:FG=1",
            "BDORZ": "FFFB88E999055A3F8A630C64834BD6D0",
            "BIDUPSID": "C90036A419A0AC8D8E65219990D60BE8",
            "Hm_lpvt_434996f833a81e36e21d9263f4d1e866": "1616120592",
            "Hm_lvt_434996f833a81e36e21d9263f4d1e866": "1616051683,1616119623,1616120584",
            "PSTM": "1611911994"
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

    # 插入数据库操作
    @staticmethod
    def db_insert(data):
        db = pymysql.connect(host="showmew.cn", database="spiders", user="root", password="123456", port=3306)
        table = "model_data"
        cloum = ",".join(data.keys())
        values = ",".join(['%s'] * len(data))
        db_cursor = db.cursor()
        sql = "INSERT INTO {table} ({cloums}) VALUES ({values}) ".format(table=table, cloums=cloum, values=values)
        print(sql)
        try:
            print(data)
            db_cursor.execute(sql, tuple(data.values()))
            print("SUCCESSFUL->")
            db.commit()
        except Exception:
            print("FAILED")
            traceback.print_exc()
            db.rollback()
        db.close()

    # 查询品牌列表
    @staticmethod
    def db_select():
        db = pymysql.connect(host="showmew.cn", database="spiders", user="root", password="123456", port=3306)
        table2 = "model_data"
        db_cursor = db.cursor()
        select = "SELECT brand FROM {table}".format(table=table2)  # where chexi IS NULL
        try:
            print(select)
            db_cursor.execute(select)
            list = db_cursor.fetchall()
            print("SUCCESSFUL->")
            return list
            db.commit()
        except Exception:
            print("FAILED")
            traceback.print_exc()
            db.rollback()
        db.close()


def main():
    # 去浏览器获取token粘贴过来
    tokenStr = "1_526c1239fc0b0512a2bd13ac6b962f5f"
    itemUrl = f"https://youjia.baidu.com/getseriesmodels?token={tokenStr}&series_id={}&sell_stat={}"
    list = Youjia.db_select()
    # 循环获取相应字段
    for brand in list:
        youjia = Youjia(tokenStr, re.utils.quote(brand[0]))
        print(youjia.chexiget)
        response = re.get(youjia.chexiget, None, cookies=youjia.cookie, headers=youjia.headers)
        jsonObj = json.loads(response.text)
        logourl = jsonObj.get("Result").get("logo")
        brandName = jsonObj.get("Result").get("brandName")
        shoumaiList = jsonObj.get("Result").get("tabs")
        for shoumai in shoumaiList:
            for list in shoumai.get("list"):
                for chexi_list in list.get("groupList"):
                    for sell_stat in [0, 1]:
                        itemId = chexi_list.get("id")
                        itemUrl_new = itemUrl.format(itemId, sell_stat)
                        print(itemUrl_new)
                        response = re.get(itemUrl_new, None, cookies=youjia.cookie, headers=youjia.headers)
                        jsonObj2 = json.loads(response.text)
                        models = jsonObj2.get("Result").get("models")
                        if len(models) != 0:
                            for model in models.values():
                                for item in model:
                                    data = {}
                                    data["brand"] = brandName
                                    data["logo"] = logourl
                                    data["chexi"] = chexi_list.get("name")
                                    data["image"] = chexi_list.get("image")
                                    data["price"] = chexi_list.get("price")
                                    data["status"] = chexi_list.get("statusDesc")
                                    data["model"] = item.get("modelName")
                                    data["engine"] = item.get("engine")
                                    data["year"] = item.get("modelYear")
                                    try:
                                        youjia.db_insert(data=data)
                                    except Exception:
                                        traceback.print_exc()


if __name__ == '__main__':
    main()
