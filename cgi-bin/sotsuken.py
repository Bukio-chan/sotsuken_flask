#!/usr/bin/python
# -*- coding: utf-8 -*-
import cgi
import os
import numpy as np
import random
import operator
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib import pyplot
import requests
from bs4 import BeautifulSoup
import sys
import datetime

# 現在のタイムスタンプを取得
now = datetime.datetime.now()

# デバッグ用
import cgitb
cgitb.enable()

print ("Content-Type: text/html")
print()

print ("<html><head>")
print ('<link href="../style.css" media="all" rel="stylesheet"/>')
print ("</head><body>")
form = cgi.FieldStorage()
form_check = 2

attraction_num = []
if "sp" in form:
  attraction_num.append(int(form["sp"].value))
if "mn" in form:
  attraction_num.append(int(form["mn"].value))
if "fl" in form:
  attraction_num.append(int(form["fl"].value))
if "jw" in form:
  attraction_num.append(int(form["jw"].value))
if "hr" in form:
  attraction_num.append(int(form["hr"].value))
if "hl" in form:
  attraction_num.append(int(form["hl"].value))
if "bk" in form:
  attraction_num.append(int(form["bk"].value))
if "hp" in form:
  attraction_num.append(int(form["hp"].value))
if "jr" in form:
  attraction_num.append(int(form["jr"].value))
if "gr" in form:
  attraction_num.append(int(form["gr"].value))
if "fs" in form:
  attraction_num.append(int(form["fs"].value))
if "el" in form:
  attraction_num.append(int(form["el"].value))

# formでの変数有無チェック
if len(attraction_num) <= 1:
  print ("<h2>ERROR </h2>")
  print ('<div class="exclamation1"><font size="5">　アトラクションは必ず2つ以上選択してください！</div>')
  form_check = 1

elif (form["START"].value or form["END"].value or form["start_time"].value) == "NONE":
  print ("<h2>ERROR </h2>")
  print ('<div class="exclamation1"><font size="5">　未選択項目があります！</div>')
  form_check = 1


url = 'https://usjportal.net/'
html = requests.get(url)
soup = BeautifulSoup(html.content,"html.parser")
table = soup.find_all(class_="waittime")

def remove_td(td): #tdを取り除く
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

def wait_time(table_num,line): #stringをintに変換
    attraction = []
    for i in range(len(table_num)):
        if i % (len(table_num)/29) == line:
            attraction.append(int(table_num[i]))
    return attraction


def wait_time_total(order,attraction_list,time_):
    wait = 0
    flag = True
    for i in range(len(order)):
        if time_ < 29:
            for j in range(len(attraction_list)):
                if order[i] == attraction_list[j]:
                    wait += att_for_loop[j][time_]
                    time_ += round(wait / 30)
        else:
            flag = False
            break
    global form_check
    if flag:
        form_check = 0
        return wait
    else:
        return wait*10

img = imread(" https://bukio-chan.herokuapp.com/image/USJ_map.png")

generation = 50 #世代数
population = generation
elite = int(population/5)

#優先取得
if form["priority"].value == "True":
  distance_flag = True
elif form["priority"].value == "False":
  distance_flag = False

"""
def setting_distance(from_city,to_city): #入力した距離データで計算
  for j in range(len(city_list)):
    for k in range(len(city_list)):
      if from_city == city_list[j] and to_city == city_list[k]:
        distance = distance_list[j][k]
  return distance
"""
class City:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance(self, city): #二点間の距離の計算
        distance = np.sqrt((self.x - city.x) ** 2 + (self.y - city.y) ** 2)
        return distance
    
    
    def __repr__(self):
        return f'({self.x},{self.y})'


class Fitness:
    def __init__(self, route):
        self.route = route
        self._distance = 0
        self._time = 0
        self._fitness = 0

    @property
    def distance(self): #総距離(時間)の計算
        if self._distance == 0:
            path_distance = 0

            for i in range(len(self.route)-1): #距離
                from_city = self.route[i]
                to_city = self.route[(i + 1) % len(self.route)]
                #path_distance += setting_distance(from_city,to_city) #どっちか
                path_distance += from_city.distance(to_city) #どっちか

            #path_distance += setting_distance(start,self.route[0])#最初の地点
            path_distance += start.distance(self.route[0]) #最初の地点
            path_distance += end.distance(self.route[-1]) #最後の地点
            self._distance = path_distance
        return self._distance


    @property
    def time(self):  # 時間の計算
        if self._time == 0:
            path_time = 0
            path_time += wait_time_total(self.route, city_list,time)
            self._time = path_time
        return self._time

    @property
    def fitness(self):
        if self._fitness == 0:
            if distance_flag:
                self._fitness = 1 / float(self.distance)
            else:
                self._fitness = 1 / float(self.time)
        return self._fitness


def create_route(city_list):
    route = random.sample(city_list, len(city_list))
    return route


def create_initial_population(population_size, city_list):
    population = []
    for i in range(population_size):
        population.append(create_route(city_list))
    return population


def rank_routes(population):
    fitness_results = {}
    for i in range(len(population)):
        fitness_results[i] = Fitness(population[i]).fitness
    return sorted(fitness_results.items(), key=operator.itemgetter(1), reverse=True)


def selection(population_ranked, elite_size):
    selection_results = []
    df = pd.DataFrame(np.array(population_ranked), columns=['Index', 'Fitness'])
    df['cum_sum'] = df['Fitness'].cumsum()
    df['cum_perc'] = 100 * df['cum_sum'] / df['Fitness'].sum()

    for i in range(elite_size):
        selection_results.append(population_ranked[i][0])

    for i in range(len(population_ranked) - elite_size):
        pick = 100 * random.random()
        satisfying = df[df['cum_perc'] >= pick]
        picked_idx = int(satisfying['Index'].iloc[0])
        selection_results.append(picked_idx)

    return selection_results


def mating_pool(population, selection_results):
    pool = [population[idx] for idx in selection_results]
    return pool


def breed(parent1, parent2):

    gene_a = int(random.random() * len(parent1))
    gene_b = int(random.random() * len(parent2))

    start_gene = min(gene_a, gene_b)
    end_gene = max(gene_a, gene_b)

    child_p1 = []
    for i in range(start_gene, end_gene):
        child_p1.append(parent1[i])

    child_p2 = [item for item in parent2 if item not in child_p1]
    child = child_p1 + child_p2
    return child


def breed_population(mating_pool, elite_size):
    children = []
    length = len(mating_pool) - elite_size
    pool = random.sample(mating_pool, len(mating_pool))

    for i in range(elite_size):
        children.append(mating_pool[i])

    for i in range(length):
        child = breed(pool[i], pool[-i-1])
        children.append(child)

    return children


def mutate(individual, mutation_rate): #突然変異
    # This has mutation_rate chance of swapping ANY city, instead of having mutation_rate chance of doing
    # a swap on this given route...
    for swapped in range(len(individual)):
        if random.random() < mutation_rate:
            swap_with = int(random.random() * len(individual))

            individual[swapped], individual[swap_with] = individual[swap_with], individual[swapped]

    return individual


def mutate_population(population, mutation_rate):
    mutated_pop = []

    for ind in population:
        mutated = mutate(ind, mutation_rate)
        mutated_pop.append(mutated)
    return mutated_pop


def next_generation(current_gen, elite_size, mutation_rate):
    pop_ranked = rank_routes(current_gen)
    selection_results = selection(pop_ranked, elite_size)
    mate_pool = mating_pool(current_gen, selection_results)
    children = breed_population(mate_pool, elite_size)
    next_gen = mutate_population(children, mutation_rate)

    return next_gen


def plot_route(route, title=None): #表示
  if form_check == 0:
    for i in range(len(route)):
        city = route[i]
        next_city = route[(i+1) % len(route)]
        bbox_dict = dict(boxstyle='round', facecolor='#00bfff', edgecolor='#0000ff', alpha=0.75, linewidth=2.5, linestyle='-')
        pyplot.text(city.x, city.y-10, i+1, bbox=bbox_dict) #番号の表示
        plt.scatter(city.x, city.y, c='red')
        if i >= len(route)-1:
          break
        plt.plot((city.x, next_city.x), (city.y, next_city.y), c='black')
        if title:
            plt.title(title, fontname="MS Gothic")

    attraction_order = [] #アトラクションの名前の順番
    for i in range(len(route)):
        for j in range(len(city_list)):
            if route[i] == city_list[j]:
                attraction_order.append(attraction_name[j])

    #print('<div class="result">')
    for i in range(len(attraction_order)): #アトラクション名の表示
        print(f'<br> {i+1}番目: {attraction_order[i]}')
    print('</div>')
    plt.imshow(img)
    #plt.show()
    plt.tick_params(labelbottom=False, labelleft=False, labelright=False, labeltop=False) #ラベル消す
    plt.tick_params(bottom=False, left=False, right=False, top=False) #ラベル消す
    plt.subplots_adjust(left=0, right=0.975, bottom=0.1, top=0.9) #余白調整
    plt.savefig("image/USJ_route.png", facecolor="azure") #画像で保存

    print ('<br><img src=" https://bukio-chan.herokuapp.com/image/USJ_route.png"/>')

def supple_dist(route): #おまけの距離の計算
    path_distance = 0
    for i in range(len(route)-1):  # 距離
        from_city = route[i]
        to_city = route[(i + 1) % len(route)]
        #path_distance += setting_distance(from_city,to_city) #どっちか
        path_distance += from_city.distance(to_city)  # どっちか
    #path_distance += setting_distance(start,route[0])  # 最初の地点
    path_distance += start.distance(route[0]) #最初の地点
    path_distance += end.distance(route[-1]) #最後の地点
    return path_distance

def supple_time(time_route):  # おまけの時間の計算
    path_time = 0
    path_time += wait_time_total(time_route, city_list,time)
    return path_time

def start_time(hour,minute): #スタート時間取得
  time_ = 0
  num = 1
  for i in range(8,21):
    if hour <= i:
      time_ = num
      if minute >= 30:
        time_ += 1
    num += 2
  return time_

def solve(cities, population_size, elite_size, mutation_rate, generations):
    pop = create_initial_population(population_size, cities)
    best_route_index, best_distance = rank_routes(pop)[0]
    best_route = pop[best_route_index]
    #print(f'<br>\nInitial distance: {round(1 / rank_routes(pop)[0][1],2)}')
    #plot_route(best_route, 'Initial')

    for g in range(generations):
        pop = next_generation(pop, elite_size, mutation_rate)

    best_route_index = rank_routes(pop)[0][0]
    best_route = pop[best_route_index]
    
    t = supple_time(best_route)
    global form_check
    if distance_flag:
        print ("<h2>結果</h2>")
        print('<div class="box11">')
        if form_check == 0:
          print(f'<font size="4">予想待ち時間:約{t}分')
        else:
          print('<font size="4">多分時間が足りないよ！')
        print(f'<br><font size="4">総移動距離:約{round(1 / rank_routes(pop)[0][1], 2)}m<br>')
        form_check = 0
    elif distance_flag == False and form_check == 0:
        print ("<h2>結果</h2>")
        print('<div class="box11">')
        print(f'<font size="4">予想待ち時間:約{round(1/rank_routes(pop)[0][1])}分')
        print(f'<br><font size="4">総移動距離:約{round(supple_dist(best_route),2)}m<br>')
    else:
      print ("<h2>ERROR </h2>")
      print ('<div class="exclamation1">　多分時間が足りないよ！</div>')
    return best_route


#スタート時間取得
time = 0 #スタート時間
if form["start_time"].value == "100":
  if now.hour >= 8 and now.hour <= 21:
    time = start_time(now.hour,now.minute)
  elif form_check == 2:
    print ("<h2>ERROR </h2>")
    print ('<div class="exclamation1">　時間を選択してね！</div>')
    form_check = 1
else:
  for i in range(29):
    if int(form["start_time"].value) == i:
      time = i

if __name__ == '__main__'  and form_check != 1:
    city,city_list = [],[]
    attraction,attraction_name = [],[]
    att_for_loop = []

    entrance_point = City(x=int(80), y=int(190))

    city.append(City(x=int(120), y=int(60)))
    attraction.append('スパイダーマン')
    att_for_loop.append(wait_time(table_2,3))

    city.append(City(x=int(170), y=int(50)))
    attraction.append('ミニオンパーク')
    att_for_loop.append(wait_time(table_5, 5))

    city.append(City(x=int(230), y=int(80)))
    attraction.append('フライングダイナソー')
    att_for_loop.append(wait_time(table_2, 2))

    city.append(City(x=int(200), y=int(150)))
    attraction.append('ジョーズ')
    att_for_loop.append(wait_time(table_2, 5))

    city.append(City(x=int(200), y=int(270)))
    attraction.append('ハリーポッター')
    att_for_loop.append(wait_time(table_1, 1))
    
    city.append(City(x=int(130), y=int(170)))
    attraction.append('ハリウッドドリームザライド')
    att_for_loop.append(wait_time(table_1, 4))

    city.append(City(x=int(120), y=int(175)))
    attraction.append('バックドロップ')
    att_for_loop.append(wait_time(table_1, 3))

    city.append(City(x=int(190), y=int(240)))
    attraction.append('ヒッポグリフ')
    att_for_loop.append(wait_time(table_1, 2))

    city.append(City(x=int(230), y=int(90)))
    attraction.append('ジュラシックパークザライド')
    att_for_loop.append(wait_time(table_2, 1))

    city.append(City(x=int(180), y=int(190)))
    attraction.append('スヌーピーのグレートレース')
    att_for_loop.append(wait_time(table_3, 2))

    city.append(City(x=int(160), y=int(180)))
    attraction.append('フライングスヌーピー')
    att_for_loop.append(wait_time(table_3, 3))

    city.append(City(x=int(150), y=int(220)))
    attraction.append('エルモのバブルバブル')
    att_for_loop.append(wait_time(table_4, 5))

    for i in range(len(city)):
        for j in range(len(attraction_num)):
            if i == attraction_num[j]:
                city_list.append(city[i])
                attraction_name.append(attraction[i])
    
    start = 0 #スタート位置
    end = 0 #終わり位置

    #スタート・ゴール地点取得
    if form["START"].value == "100":
      start = entrance_point
    else:
      for i in range(len(city)):
        if int(form["START"].value) == i:
          start = city[int(form["START"].value)]

    if form["END"].value == "100":
      end = entrance_point
    else:
      for i in range(len(city)):
        if int(form["END"].value) == i:
          end = city[int(form["END"].value)]

    

    distance_list = [[0,150,340,360,680,380],
                             [150,0,200,310,670,390],
                             [340,200,0,230,590,420],
                             [360,310,230,0,370,220],
                             [680,670,590,370,0,370],
                             [380,390,420,220,370,0]]

    best_route = solve(city_list, population, elite, 0.01, generation)
    plot_route(best_route, '地図')

print ("<br><b></b>".format(os.environ['REQUEST_METHOD']))
print ("</body></html>")