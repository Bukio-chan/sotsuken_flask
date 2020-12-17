#!/usr/bin/python
import requests
from bs4 import BeautifulSoup
import datetime
import os
import glob
import csv
from flask import Flask, render_template, request
from calc import Attraction, GeneticAlgorithm

app = Flask(__name__)

url = 'https://usjreal.asumirai.info/'
html = requests.get(url, verify=False)
soup = BeautifulSoup(html.content, "html.parser")
opening = soup.find(class_="wave").string
opening_time = int(opening[0:2])
closing_time = int(opening[8:10])

# data.csvのデータを2次元配列dataに格納
with open("static/csv/data.csv", 'r', encoding="utf-8")as f:
    reader = csv.reader(f)
    data = [row for row in reader]
    data.pop(0)

all_attraction = []
# スタート地点・ゴール地点の座標配列all_attraction[]
for j in range(len(data)):
    all_attraction.append(Attraction(name=data[j][0], x=int(data[j][1]), y=int(data[j][2]), num=j))


def now_wait_time_extraction(attraction_url):
    attraction_html = requests.get(attraction_url, verify=False)
    attraction_soup = BeautifulSoup(attraction_html.content, "html.parser")
    now_wait_time = attraction_soup.find(class_="realtime")
    now_wait_time = now_wait_time.find("td").string
    if now_wait_time is None:
        now_wait_time = 'None'
    return now_wait_time


# csvから読み取り、stringをintに変換
def load_from_csv(line, today_csv):
    csv_file = open(today_csv, 'r', encoding="utf-8")
    df = []
    for row in csv.reader(csv_file):
        df.append((row[line]))
    csv_file.close()
    df.pop(0)
    a = []
    for i in range(len(df)):
        if df[i] == 'None ' or df[i] == 'None' or df[i] == ' None ':
            a.append(0)
        else:
            float_n = float(df[i])
            a.append(int(float_n))
    return a


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


def time_for_index():  # index.html用
    csv_file = open('static/csv/TimeList/rank-a-average.csv', 'r', encoding="utf-8")
    df = []
    for row in csv.reader(csv_file):
        df.append((row[0]))
    csv_file.close()
    df.pop(0)
    value = list(range(len(df)))
    for i in range(6):  # 終了時刻まで削る
        df.pop(-1)
        value.pop(-1)
    if opening_time <= 9:  # 開始時刻まで削る
        for i in range(4):
            df.pop(0)
            value.pop(0)
    if opening_time >= 10:  # 開始時刻まで削る
        for i in range(6):
            df.pop(0)
            value.pop(0)
    return df, value


@app.route("/")
def search():
    # 画像の削除
    for x in glob.glob('static/result/*.png'):
        os.remove(x)
    index_time, value = time_for_index()
    return render_template("index.html", city=all_attraction, index_time=index_time, value=value)


@app.route("/result", methods=['POST'])
def result():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # 日本時間取得
    if now.hour <= 9:
        yoso = soup.find(class_="rank-yoso a")
        rank = yoso.string  # A,B,C,D,E,F,S
    else:
        yoso = soup.find(class_="rank-col rank")
        rank = yoso.contents[1]  # A,B,C,D,E,F,S
    rank = rank.lower()  # 小文字に変換
    today_csv = f'static/csv/TimeList/rank-{rank}-average.csv'

    attraction_number = request.form.getlist('attraction')  # 選択されたアトラクションの取得
    selected_start_place = int(request.form.get('START'))  # スタート位置
    selected_end_place = int(request.form.get('END'))  # 終わり位置
    start_time = int(request.form.get('start_time'))  # スタート時間
    priority = request.form.get("priority")  # 優先
    generation = int(request.form.get("generation"))  # 世代数

    # スタート・ゴール地点取得
    start_place = all_attraction[selected_start_place]
    end_place = all_attraction[selected_end_place]

    if len(attraction_number) < 1:
        comment = "アトラクションを選んでください！"
        return render_template('error.html', comment=comment)

    # 選択されたアトラクションのデータをappendしていく
    attraction_list = []
    for i in range(len(attraction_number)):
        num = int(attraction_number[i])
        attraction_list.append(Attraction(name=data[num][0], x=int(data[num][1]), y=int(data[num][2]),
                                          wait_time_list=load_from_csv(int(data[num][4]), today_csv),
                                          ride_time=int(data[num][3]), num=num,
                                          now_wait_time=now_wait_time_extraction(f"{data[num][5]}")))

    start_time_result = now

    if start_time == 100:  # スタート時間
        if opening_time <= now.hour < closing_time:
            start_time = get_start_time(now.hour, now.minute)
            for i in range(len(attraction_list)):
                attraction_list[i].now_wait_time = int(attraction_list[i].now_wait_time)
        else:
            comment = '時間を選択してください！'
            return render_template('error.html', comment=comment)
    else:
        start_time_result = get_selected_time(datetime.datetime(now.year, now.month, now.day, 7, 15),
                                              start_time)

    # 優先取得
    if priority == "距離優先":
        distance_flag = True
    else:
        distance_flag = False

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
        end_hour = end_time_result.hour
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
    else:
        end_hour = "??"
        end_minute = "??"

    # htmlへ出力
    return render_template('result.html', priority=priority, time_result=time_result,
                           time_hour=time_hour, time_minute=time_minute,
                           distance=distance_result, order=order_result, img_filename=img_filename,
                           start_hour=start_time_result.hour, start_minute=start_minute,
                           end_hour=end_hour, end_minute=end_minute,
                           start_place=start_place, end_place=end_place,
                           elapsed_hour=elapsed_hour, elapsed_minute=elapsed_minute)


if __name__ == "__main__":
    app.run(debug=False)
