#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from calc import Attraction, GeneticAlgorithm
import datetime
import os
import glob
import csv

app = Flask(__name__)

# data.csvのデータを2次元配列dataに格納
with open("static/csv/data.csv", 'r', encoding="utf-8")as f:
    reader = csv.reader(f)
    data = [row for row in reader]
    data.pop(0)

all_attraction = []
# スタート地点・ゴール地点の座標配列all_attraction[]
for j in range(len(data)):
    all_attraction.append(Attraction(name=data[j][0], x=int(data[j][1]), y=int(data[j][2]), num=j))


# csvから読み取り、stringをintに変換
def load_from_csv(table_num, line):
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
def get_selected_time(set_time, time_num):
    set_time += datetime.timedelta(minutes=time_num * 30)
    return set_time


@app.route("/")
def search():
    # 画像の削除
    for x in glob.glob('static/result/*.png'):
        os.remove(x)
    return render_template("index.html", city=all_attraction)


@app.route("/result", methods=['POST'])
def result():
    attraction_number = request.form.getlist('attraction')  # 選択されたアトラクションの取得
    selected_start_place = int(request.form.get('START'))  # スタート位置
    selected_end_place = int(request.form.get('END'))  # 終わり位置
    start_time = int(request.form.get('start_time'))  # スタート時間
    priority = request.form.get("priority")  # 優先
    generation = int(request.form.get("generation"))  # 世代数

    if len(attraction_number) < 2:
        comment = "アトラクションは2つ以上選んでください！"
        return render_template('error.html', comment=comment)

    # 選択されたアトラクションのデータをappendしていく
    attraction_list = []
    for i in range(len(attraction_number)):
        num = int(attraction_number[i])
        attraction_list.append(Attraction(name=data[num][0], x=int(data[num][1]), y=int(data[num][2]),
                                          wait_time_list=load_from_csv(f'static/csv/table_{data[num][3]}.csv',
                                                                       int(data[num][4])),
                                          ride_time=int(data[num][5]), num=num))

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # 日本時間取得

    start_time_result = now

    if start_time == 100:  # スタート時間
        if 8 <= now.hour <= 21:
            start_time = get_start_time(now.hour, now.minute)
        else:
            comment = '時間を選択してね！'
            return render_template('error.html', comment=comment)
    else:
        start_time_result = get_selected_time(datetime.datetime(now.year, now.month, now.day, 7, 45),
                                              start_time)

    # 優先取得
    if priority == "距離優先":
        distance_flag = True
    else:
        distance_flag = False

    # スタート・ゴール地点取得
    start_place = all_attraction[selected_start_place]
    end_place = all_attraction[selected_end_place]

    ga = GeneticAlgorithm(attraction_list, distance_flag, start_place, end_place, start_time)
    output_result = ga.main(generation)  # main()を実行

    order_result, time_result, distance_result, img_filename = output_result

    if time_result == 0:
        comment = "時間が足りないかも！"
        return render_template('error.html', comment=comment)
    else:
        end_time_result = start_time_result + datetime.timedelta(minutes=time_result[0])

    # ?分を?時間?分の形に変更
    time_hour = int(time_result[0] / 60)
    time_minute = time_result[0] % 60

    # 0埋め
    start_minute = format(start_time_result.minute, '02')
    end_minute = format(end_time_result.minute, '02')

    elapsed_hour = []
    elapsed_minute = []
    add = start_time_result
    if time_result[0] <= 10000:
        # 経過時間毎の時刻
        for i in range(len(attraction_list)):
            arrival = add + datetime.timedelta(minutes=time_result[2][i])
            elapsed_hour.append(arrival.hour)
            elapsed_minute.append(format(arrival.minute, '02'))
            depart = arrival + datetime.timedelta(minutes=time_result[1][i]) + datetime.timedelta(
                minutes=order_result[i].ride_time)
            elapsed_hour.append(depart.hour)
            elapsed_minute.append(format(depart.minute, '02'))
            add = depart

    # htmlへ出力
    return render_template('result.html', priority=priority, time_result=time_result,
                           time_hour=time_hour, time_minute=time_minute,
                           distance=distance_result, order=order_result, img_filename=img_filename,
                           start_hour=start_time_result.hour, start_minute=start_minute,
                           end_hour=end_time_result.hour, end_minute=end_minute,
                           start_place=start_place, end_place=end_place,
                           elapsed_hour=elapsed_hour, elapsed_minute=elapsed_minute)


if __name__ == "__main__":
    app.run(debug=False)
