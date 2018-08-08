# -*- coding: utf-8 -*-
"""
爬取去哪儿网站的所有城市自由行的数据
反反爬策略:设置cookies池和ip代理池以及延长爬虫休眠时间
"""

import requests
import time
from urllib.parse import quote
from multiprocessing import Pool
import pymongo

def begin():
    """
    获取去哪儿网出发点站点列表
    :return:
    """
    depurl = 'https://touch.dujia.qunar.com/depCities.qunar'
    response = requests.get(depurl)
    deps = response.json()
    for dep_item in deps['data']:
        for dep in deps['data'][dep_item]:
            yield dep#出发城市

def main(dep):
    """
    获取获取去哪儿网出发地可到达的目的地列表
    :param dep:出发地 
    :return: 目的地列表
    """

    a = []
    desurl = 'https://touch.dujia.qunar.com/golfz/sight/arriveRecommend?dep={}&exclude=&extensionImg=255,175'.format(
        quote(dep))
    time.sleep(4)
    response = requests.get(desurl)
    des = response.json()
    for des_item in des['data']:
        for des_item_1 in des_item['subModules']:
            for query in des_item_1['items']:
                if query['query'] not in a:#去重
                    a.append(query['query'])#目的地列表
    get(a,dep)

def get(array,dep):
    """
    得到去哪儿网自由行数据搜索结果
    :param array: 目的地列表
    :param dep: 出发城市
    :return: 出发城市到目的地的自由行结果
    """
    for item in array:
        # 头文件 防止反爬
        headers = {
            'cookie': 'QN48=tc_ccae3300ce8e35ac_1650ef39d6c_d500; QN300=organic; QN1=O5cv7FtoLfuqk1jAFIK4Ag==; _RSG=nXKcCZAa8QCKV6LBIBftmA; _RDG=28a9c8257d385c22543c4b440392b3a9f3; _RGUID=c68890a8-cc99-4871-ac37-a4b48b5467d4; QN668=51%2C55%2C53%2C53%2C55%2C55%2C54%2C51%2C59%2C50%2C54%2C59%2C57; QN601=14625155bab478ac3c9dbf842e88fc9e; QN621=fr%3Dtouch_index; SC1=0f3e6ac13e6ab3505eecaa6a4820bf6c; SC18=; SC102=30b9d3a1225274660268; QN205=organic; QN233=FreetripTouchin; QN234=home_free_t; csrfToken=7bf38a28d34207186293bcff94cc106f; _RF1=163.125.22.191; DJ12=eyJxIjoi5Li95rGf6Ieq55Sx6KGMIiwic3UiOiJodHRwOi8vZmh0b3VjaC5kdWppYS5xdW5hci5jb20vcmVkaXJlY3Q_cm91dGVJZD0xODA1MzU2NCIsImQiOiLmt7HlnLMiLCJlIjoiQiIsImwiOiIwLDI4IiwidHMiOiI0YTAzYjJiZC0zMDlmLTQxM2YtYmQ5ZC0xMzY2ZWEyODcxODEifQ; _pk_ref.1.8600=%5B%22%22%2C%22%22%2C1533629980%2C%22http%3A%2F%2Ftouch.qunar.com%2F%22%5D; _pk_ses.1.8600=*; _pk_id.1.8600=04ab07664bf4d248.1533554230.3.1533630047.1533627348.; QN243=185',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            '(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Referer': 'https://touch.dujia.qunar.com/p/list?cfrom=zyx&dep={}&query={}&it=FreetripTouchin&et=home_free_t'.format(quote(dep),quote(item))
        }
        resulturl = 'https://touch.dujia.qunar.com/list?modules=list%2CbookingInfo%2CactivityDetail&dep={}&query={}&dappDealTrace=false&mobFunction=%E6%89%A9%E5%B1%95%E8%87%AA%E7%94%B1%E8%A1%8C&cfrom=zyx&it=FreetripTouchin&date=&configDepNew=&needNoResult=true&originalquery={}&limit=0,28&includeAD=true&qsact=search'.format\
            (quote(dep),quote(item),quote(item))
        time.sleep(4)
        response = requests.get(resulturl, headers=headers).json()

        #容错处理,防止json文件中有不存在的项引起报错
        try:
            routecount = int(response['data']['limit']['routeCount'])#获取
            for limit in range(0, routecount, 28):
                resulturl = 'https://touch.dujia.qunar.com/list?modules=list%2CbookingInfo%2CactivityDetail&dep={}&query={}' \
                            '&dappDealTrace=false&mobFunction=%E6%89%A9%E5%B1%95%E8%87%AA%E7%94%B1%E8%A1%8C&cfrom=zyx&' \
                            'it=FreetripTouchin&date=&configDepNew=&needNoResult=true&originalquery={}&limit={},28&' \
                            'includeAD=true&qsact=search'.format(quote(dep), quote(item), quote(item), limit)
                time.sleep(4)
                response = requests.get(resulturl, headers=headers)
                items = response.json()['data']['list']['results'][0]
                result = {
                    '时间': time.strftime('%Y-%m-%d', time.localtime(time.time())),
                    '出发地': dep,
                    '目的地': item,
                    '价格':items['price'],
                    '天数': items['accomInclude'],
                    '亮点': items['brightspots'],
                    '出行工具':items['backtraffic'],
                    '类别':items['ttsRouteType']
                }
                print(result)
                savetomongo(result)
                time.sleep(2)
        except:
            return


mongo_uri = '27010'#mongodb端口号
mongo_db = 'qunar'#mongodb数据库
collection = 'travel'#mongodb集合
client = pymongo.MongoClient(mongo_uri)#连接mongodb
db = client[mongo_db]#创建qunar.travel

def savetomongo(result):
    """
    保存到mongodb数据库
    :param result: 出发城市到目的城市自由行搜索结果
    :return:
    """
    db[collection].insert(result)#插入数据到mongodb


if __name__ == '__main__':
    deps = begin()
    #开启多线程
    pool = Pool()
    pool.map(main,[dep for dep in deps])
    client.close()
