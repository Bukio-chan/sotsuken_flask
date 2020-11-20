#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import datetime
import random
import string
import calc
import os
import glob

app = Flask(__name__)

url = 'https://usjportal.net/'
html = requests.get(url)
soup = BeautifulSoup(html.content, "html.parser")
table = soup.find_all(class_="waittime")


def remove_td(td):  # tdを取り除く
    for i in range(len(td)):
        td[i] = td[i].string
        if td[i] == '-':
            td[i] = '0'
    return td


table_1 = remove_td(table[0].find_all("td"))
table_2 = remove_td(table[1].find_all("td"))
table_3 = remove_td(table[2].find_all("td"))
table_4 = remove_td(table[3].find_all("td"))
table_5 = remove_td(table[4].find_all("td"))


def wait_time(table_num, line):  # stringをintに変換
    att = []
    for i in range(len(table_num)):
        if i % (len(table_num) / 29) == line:
            att.append(int(table_num[i]))
    return att


class_City = calc.City


# 現在時刻からスタート時間取得メソッド
def get_start_time(hour, minute):
    time_ = 0
    num = 1
    for i in range(8, 21):
        if hour <= i:
            time_ = num
        if minute >= 30:
            time_ += 1
        num += 2
    return time_


# 入力された時間を取得
def get_input_time(set_time, time_num):
    set_time += datetime.timedelta(minutes=time_num*30)
    return set_time


# random文字列生成
def random_name(n):
    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(n)])


@app.route("/")
def search():
    render_page = render_template("index.html")
    for x in glob.glob('static/result/*.png'):
        os.remove(x)
    return render_page


@app.route("/result", methods=['POST'])
def result():
    city, city_list = [], []
    attraction, attraction_name = [], []
    att_for_loop = []

    entrance_point = class_City(x=int(80), y=int(190))

    city.append(class_City(x=int(120), y=int(60)))
    attraction.append('スパイダーマン')
    att_for_loop.append(wait_time(table_2, 3))

    city.append(class_City(x=int(170), y=int(50)))
    attraction.append('ミニオンパーク')
    att_for_loop.append(wait_time(table_5, 5))

    city.append(class_City(x=int(230), y=int(80)))
    attraction.append('フライングダイナソー')
    att_for_loop.append(wait_time(table_2, 2))

    city.append(class_City(x=int(200), y=int(150)))
    attraction.append('ジョーズ')
    att_for_loop.append(wait_time(table_2, 5))

    city.append(class_City(x=int(200), y=int(270)))
    attraction.append('ハリーポッター')
    att_for_loop.append(wait_time(table_1, 1))

    city.append(class_City(x=int(130), y=int(170)))
    attraction.append('ハリウッドドリームザライド')
    att_for_loop.append(wait_time(table_1, 4))

    city.append(class_City(x=int(120), y=int(175)))
    attraction.append('バックドロップ')
    att_for_loop.append(wait_time(table_1, 3))

    city.append(class_City(x=int(190), y=int(240)))
    attraction.append('ヒッポグリフ')
    att_for_loop.append(wait_time(table_1, 2))

    city.append(class_City(x=int(230), y=int(90)))
    attraction.append('ジュラシックパークザライド')
    att_for_loop.append(wait_time(table_2, 1))

    city.append(class_City(x=int(180), y=int(190)))
    attraction.append('スヌーピーのグレートレース')
    att_for_loop.append(wait_time(table_3, 2))

    city.append(class_City(x=int(160), y=int(180)))
    attraction.append('フライングスヌーピー')
    att_for_loop.append(wait_time(table_3, 3))

    city.append(class_City(x=int(150), y=int(220)))
    attraction.append('エルモのバブルバブル')
    att_for_loop.append(wait_time(table_4, 5))

    attraction_num = request.form.getlist('attraction')  # 選択されたアトラクションの取得
    get_start = int(request.form.get('START'))  # スタート位置
    get_end = int(request.form.get('END'))  # 終わり位置
    start_time = int(request.form.get('start_time'))

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    now_hour = now.hour
    now_minute = now.minute

    start_result = now

    if int(request.form.get('start_time')) == 100:  # スタート時間
        if 8 <= now_hour <= 21:
            start_time = get_start_time(now_hour, now_minute)
        else:
            comment = '時間を選択してね！'
            return render_template('error.html', comment=comment)
    else:
        start_result = get_input_time(datetime.datetime(now.year, now.month, now.day, 7, 45), start_time)

    for i in range(len(city)):
        for j in range(len(attraction_num)):
            if i == int(attraction_num[j]):
                city_list.append(city[i])
                attraction_name.append(attraction[i])
    # 優先取得
    if request.form.get("priority") == "True":
        distance_flag = True
    else:
        distance_flag = False

    # スタート・ゴール地点取得
    if get_start == 100:
        start = entrance_point
    else:
        start = city[get_start]

    if get_end == 100:
        end = entrance_point
    else:
        end = city[get_end]

    random_url = f"static/result/USJ_route_{random_name(6)}.png"

    result_output = calc.main_run(city_list, attraction_name, distance_flag, start, end, start_time,
                                  att_for_loop, random_url)

    img_url = result_output[0]
    time_result = result_output[1]
    distance_result = result_output[2]
    order_result = result_output[3]

    if time_result == 0:
        comment = "時間が足りないかも！"
        return render_template('error.html', comment=comment)
    else:
        end_result = start_result + datetime.timedelta(minutes=time_result)

        # htmlへ出力
        return render_template('result.html', time=time_result, distance=distance_result,
                               order=order_result, img_url=img_url,
                               start_hour=start_result.hour, start_minute=start_result.minute,
                               end_hour=end_result.hour, end_minute=end_result.minute)


if __name__ == "__main__":
    app.run(debug=False)
