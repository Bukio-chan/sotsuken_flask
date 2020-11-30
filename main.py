#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
import datetime
import random
import string
import calc
import os
import glob
import csv

app = Flask(__name__)


# csvから読み取り、stringをintに変換
def wait_time(table_num, line):
    csv_file = open(table_num, 'r')
    df = []
    for row in csv.reader(csv_file):
        df.append(int(row[line]))
    csv_file.close()
    return df


class_City = calc.City  # calc.pyのCityクラス


# 現在時刻からスタート時間取得
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


# 選択された時間を取得
def get_input_time(set_time, time_num):
    set_time += datetime.timedelta(minutes=time_num * 30)
    return set_time


# random文字列生成
def random_name(n):
    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(n)])


@app.route("/")
def search():
    render_page = render_template("index.html")
    # 画像の削除
    for x in glob.glob('static/result/*.png'):
        os.remove(x)
    return render_page


@app.route("/result", methods=['POST'])
def result():
    city, city_list = [], []
    attraction, attraction_name = [], []
    time_list = []

    entrance_point = class_City(x=int(80), y=int(190))  # エントランスの座標

    # data.csvのデータを2次元配列dataに格納
    with open("static/csv/data.csv", 'r', encoding="utf-8")as f:
        reader = csv.reader(f)
        data = [row for row in reader]
        data.pop(0)

    # アトラクションのデータをappendしていく
    for i in range(len(data)):
        city.append(class_City(x=int(data[i][1]), y=int(data[i][2])))
        attraction.append(data[i][0])
        time_list.append(wait_time(f'static/csv/table_{data[i][3]}.csv', int(data[i][4])))

    attraction_num = request.form.getlist('attraction')  # 選択されたアトラクションの取得
    get_start = int(request.form.get('START'))  # スタート位置
    get_end = int(request.form.get('END'))  # 終わり位置
    start_time = int(request.form.get('start_time'))  # スタート時間

    if len(attraction_num) < 2:
        comment = "アトラクションは2つ以上選んでください！"
        return render_template('error.html', comment=comment)

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # 日本時間
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

    # 選択されたアトラクションをappend
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

    result_output = calc.main(city_list, attraction_name, distance_flag, start, end, start_time,
                              time_list, random_url)

    img_url = result_output[0]
    time_result = result_output[1]
    distance_result = result_output[2]
    order_result = result_output[3]

    if time_result == 0:
        comment = "時間が足りないかも！"
        return render_template('error.html', comment=comment)
    else:
        end_result = start_result + datetime.timedelta(minutes=time_result)

    time_hour = int(time_result / 60)
    time_minute = time_result % 60
    # 0埋め
    start_minute = format(start_result.minute, '02')
    end_minute = format(end_result.minute, '02')

    # htmlへ出力
    return render_template('result.html', time=time_result, time_hour=time_hour, time_minute=time_minute,
                           distance=distance_result, order=order_result, img_url=img_url,
                           start_hour=start_result.hour, start_minute=start_minute,
                           end_hour=end_result.hour, end_minute=end_minute)


if __name__ == "__main__":
    app.run(debug=False)
