#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import random
import operator
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib import pyplot

generation = 50  # 世代数
population_gene = generation
elite = int(population_gene / 5)
form_check = False


def wait_time_total(order, city_list, time_num, time_list, on_foot):
    wait = 0
    flag = True
    global form_check
    for i in range(len(order)):
        if time_num < 29:
            wait += on_foot[i]
            for j in range(len(city_list)):
                if order[i] == city_list[j]:
                    wait += time_list[j][time_num]
                    if wait >= 30:
                        time_num = round(wait / 30)
        else:
            flag = False
            break

    if flag:
        form_check = True
        return wait
    else:
        return wait * 10000


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

    def distance(self, city):  # 二点間の距離の計算
        distance = np.sqrt((self.x - city.x) ** 2 + (self.y - city.y) ** 2)
        return distance

    def __repr__(self):
        return f'({self.x},{self.y})'


class Calc:
    def __init__(self, route, city_list, start_time, time_list, start, end):
        self.route = route
        self.start = start
        self.end = end
        self.city_list = city_list
        self.start_time = start_time
        self.time_list = time_list
        self._time = 0
        self._distance = 0
        self._fitness = 0

    def on_foot(self):  # 徒歩時間の追加
        on_foot = [round(self.start.distance(self.route[0]) / 80)]  # 最初の地点
        for i in range(len(self.route) - 1):  # 距離
            from_city = self.route[i]
            to_city = self.route[(i + 1) % len(self.route)]
            # path_distance += setting_distance(from_city,to_city) #どっちか
            on_foot.append(round(from_city.distance(to_city) / 80))  # どっちか
        on_foot.append(round(self.end.distance(self.route[-1]) / 80))  # 最後の地点
        return on_foot

    @property
    def time(self):  # 時間の計算
        if self._time == 0:
            path_time = 0
            path_time += wait_time_total(self.route, self.city_list, self.start_time,
                                         self.time_list, self.on_foot())
            self._time = path_time
        return self._time

    @property
    def distance(self):  # 総距離(時間)の計算
        if self._distance == 0:
            path_distance = 0

            for i in range(len(self.route) - 1):  # 距離
                from_city = self.route[i]
                to_city = self.route[(i + 1) % len(self.route)]
                # path_distance += setting_distance(from_city,to_city) #どっちか
                path_distance += from_city.distance(to_city)  # どっちか

            # path_distance += setting_distance(start,self.route[0])#最初の地点
            path_distance += self.start.distance(self.route[0])  # 最初の地点
            path_distance += self.end.distance(self.route[-1])  # 最後の地点
            self._distance = path_distance
        return self._distance

    @property
    def time_fitness(self):
        if self._fitness == 0:
            self._fitness = 1 / float(self.time)
        return self._fitness

    @property
    def distance_fitness(self):
        if self._fitness == 0:
            self._fitness = 1 / float(self.distance)
        return self._fitness


def create_route(city_list):
    route = random.sample(city_list, len(city_list))
    return route


def create_initial_population(population_size, city_list):
    population = []
    for i in range(population_size):
        population.append(create_route(city_list))
    return population


def rank_routes(population, distance_flag, start, end, city_list, start_time, time_list):
    fitness_results = {}
    for i in range(len(population)):
        calc = Calc(population[i], city_list, start_time, time_list, start, end)
        if distance_flag:
            fitness_results[i] = calc.distance_fitness
        else:
            fitness_results[i] = calc.time_fitness
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
        child = breed(pool[i], pool[-i - 1])
        children.append(child)

    return children


def mutate(individual, mutation_rate):  # 突然変異
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


def next_generation(current_gen, elite_size, mutation_rate, distance_flag, start, end,
                    city_list, start_time, time_list):
    pop_ranked = rank_routes(current_gen, distance_flag, start, end, city_list, start_time, time_list)
    selection_results = selection(pop_ranked, elite_size)
    mate_pool = mating_pool(current_gen, selection_results)
    children = breed_population(mate_pool, elite_size)
    next_gen = mutate_population(children, mutation_rate)
    return next_gen


def plot_route(route, attraction_name, city_list, url, title=None):  # 表示
    attraction_order = []
    img = imread("static/USJ_map.png")
    plt.figure()
    for i in range(len(route)):
        city = route[i]
        next_city = route[(i + 1) % len(route)]
        bbox_dict = dict(boxstyle='round', facecolor='#00bfff', edgecolor='#0000ff', alpha=0.75, linewidth=2.5,
                         linestyle='-')
        pyplot.text(city.x, city.y - 10, i + 1, bbox=bbox_dict)  # 番号の表示
        plt.scatter(city.x, city.y, c='red')
        if i >= len(route) - 1:
            break
        plt.plot((city.x, next_city.x), (city.y, next_city.y), c='black')
        if title:
            plt.title(title, fontname="MS Gothic")

    for i in range(len(route)):
        for j in range(len(city_list)):
            if route[i] == city_list[j]:
                attraction_order.append(attraction_name[j])
    attraction_order_result = attraction_order

    plt.imshow(img)
    # plt.show()
    plt.tick_params(labelbottom=False, labelleft=False, labelright=False, labeltop=False)  # ラベル消す
    plt.tick_params(bottom=False, left=False, right=False, top=False)  # ラベル消す
    # plt.subplots_adjust(left=0, right=0.975, bottom=0.1, top=0.9)  # 余白調整
    plt.savefig(url, bbox_inches='tight', pad_inches=0)  # 画像で保存
    return attraction_order_result, url


def solve(cities, population_size, elite_size, mutation_rate, generations,
          distance_flag, start, end, start_time, time_list):
    pop = create_initial_population(population_size, cities)

    for g in range(generations):
        pop = next_generation(pop, elite_size, mutation_rate, distance_flag, start, end,
                              cities, start_time, time_list)

    best_route_index = rank_routes(pop, distance_flag, start, end, cities, start_time, time_list)[0][0]
    best_route = pop[best_route_index]

    calc = Calc(best_route, cities, start_time, time_list, start, end)
    if distance_flag:
        time_result = calc.time
        distance_result = round(1 / rank_routes(pop, distance_flag, start, end,
                                                cities, start_time, time_list)[0][1], 2)
    else:
        time_result = round(1 / rank_routes(pop, distance_flag, start, end,
                                            cities, start_time, time_list)[0][1])
        distance_result = round(calc.distance, 2)

    if not form_check and not distance_flag:
        time_result = 0

    return best_route, time_result, distance_result


def main(city_list, attraction_name, distance_flag, start, end, start_time, time_list, url):
    best_route = solve(city_list, population_gene, elite, 0.01, generation, distance_flag,
                       start, end, start_time, time_list)
    result = plot_route(best_route[0], attraction_name, city_list, url, '')

    time_result = best_route[1]
    distance_result = best_route[2]
    order_result = result[0]
    url_result = result[1]

    return url_result, time_result, distance_result, order_result
