import json
import time
from datetime import datetime

import numpy
import requests


def miaomiao():
    nums = []
    data = []

    for i in range(100):
        start_time = time.time()
        response = requests.get(url="https://miaomiao.scmttec.com")
        end_time = time.time()
        data.append(json.loads(response.text)['data'])
        # time_start_time = end_time - start_time
        # nums.append(time_start_time)
        print("耗费时间" + str((end_time - start_time) * 1000) + "ms" "==" + response.text)
        # print("服务器时间差" + ser_time.__str__() + "ms")

    print("平均" + numpy.average(nums).__str__())
    print("最大" + numpy.max(nums).__str__())
    print("最小" + numpy.min(nums).__str__())
    print("中位数" + numpy.median(nums).__str__())


if __name__ == '__main__':
    miaomiao()
