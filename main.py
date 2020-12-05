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

class_City = calc.City  # calc.pyのCityクラス

# data.csvのデータを2次元配列dataに格納
with open("static/csv/data.csv", 'r', encoding="utf-8")as f:
    reader = csv.reader(f)
    data = [row for row in reader]
    data.pop(0)

city = []
# スタート地点・ゴール地点の座標配列city[]
for j in range(len(data)):
    city.append(class_City(name=data[j][0], x=int(data[j][1]), y=int(data[j][2]), num=j))


# csvから読み取り、stringをintに変換
def wait_time(table_num, line):
    csv_file = open(table_num, 'r')
    df = []
    for row in csv.reader(csv_file):
        df.append(int(row[line]))
    csv_file.close()
    return df


# 現在時刻からスタート時間取得
def get_start_time(hour, minute):
    num_result = 0
    num = 1
    for i in range(8, 21):
        if hour == i:
            num_result = num
            if minute >= 30:
                num_result += 1
        num += 2
    return num_result


# 選択された時間を取得
def get_input_time(set_time, time_num):
    set_time += datetime.timedelta(minutes=time_num * 30)
    return set_time


# random文字列生成
def random_name(n):
    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(n)])


@app.route("/")
def search():
    # 画像の削除
    for x in glob.glob('static/result/*.png'):
        os.remove(x)
    return render_template("index.html", city=city)


@app.route("/result", methods=['POST'])
def result():
    city_list = []

    attraction_num = request.form.getlist('attraction')  # 選択されたアトラクションの取得
    get_start = int(request.form.get('START'))  # スタート位置
    get_end = int(request.form.get('END'))  # 終わり位置
    start_time = int(request.form.get('start_time'))  # スタート時間

    if len(attraction_num) < 2:
        comment = "アトラクションは2つ以上選んでください！"
        return render_template('error.html', comment=comment)

    # 選択されたアトラクションのデータをappendしていく
    for i in range(len(attraction_num)):
        num = int(attraction_num[i])
        city_list.append(class_City(name=data[num][0], x=int(data[num][1]), y=int(data[num][2]),
                                    time_list=wait_time(f'static/csv/table_{data[num][3]}.csv', int(data[num][4])),
                                    ride_time=int(data[num][5]), num=i))

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # 日本時間取得
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
        start_result = get_input_time(datetime.datetime(now.year, now.month, now.day, 7, 45),
                                      start_time)

    # 優先取得
    if request.form.get("priority") == "True":
        distance_flag = True
    else:
        distance_flag = False

    # スタート・ゴール地点取得
    start_place = city[get_start]
    end_place = city[get_end]

    random_url = f"static/result/USJ_route_{random_name(6)}.png"

    ga = calc.GeneticAlgorithm(city_list, distance_flag, start_place, end_place,
                               start_time, random_url)
    result_output = ga.main()

    img_url = result_output[0]
    order_result = result_output[1]
    time_result = result_output[2]
    distance_result = result_output[3]

    if time_result == 0:
        comment = "時間が足りないかも！"
        return render_template('error.html', comment=comment)
    else:
        end_result = start_result + datetime.timedelta(minutes=time_result[0])

    time_hour = int(time_result[0] / 60)
    time_minute = time_result[0] % 60
    # 0埋め
    start_minute = format(start_result.minute, '02')
    end_minute = format(end_result.minute, '02')

    # htmlへ出力
    return render_template('result.html', time=time_result, time_hour=time_hour, time_minute=time_minute,
                           distance=distance_result, order=order_result, img_url=img_url,
                           start_hour=start_result.hour, start_minute=start_minute,
                           end_hour=end_result.hour, end_minute=end_minute,
                           start_place=start_place, end_place=end_place)


if __name__ == "__main__":
    app.run(debug=False)
