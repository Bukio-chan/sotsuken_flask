#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import random
import operator
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib import pyplot
import csv


# 徒歩時間の追加
def add_walk_time(route, start_place, end_place):
    # foot = [round(start_place.setting_distance(route[0]) / 80)]  # 最初の地点
    foot = [round(start_place.distance(route[0]) / 80)]  # 最初の地点
    for i in range(len(route) - 1):  # 距離
        from_city = route[i]
        to_city = route[(i + 1) % len(route)]
        # foot.append(round(from_city.setting_distance(to_city) / 80))  # どっちか
        foot.append(round(from_city.distance(to_city) / 80))  # どっちか
    # foot.append(round(end_place.setting_distance(route[-1]) / 80))  # 最後の地点
    foot.append(round(end_place.distance(route[-1]) / 80))  # 最後の地点
    return foot


# 待ち時間の合計
def wait_time_total(route, start_place, end_place, start_time, attraction_list):
    fixed_time = start_time
    walk_time = add_walk_time(route, start_place, end_place)
    wait_time = 0
    flag = True
    each_wait_time = []
    for i in range(len(route)):
        if start_time < 29:
            wait_time += walk_time[i]  # 徒歩時間
            for j in range(len(attraction_list)):
                if route[i] == attraction_list[j]:
                    each_wait_time.append(attraction_list[j].wait_time_list[start_time])
                    wait_time += attraction_list[j].wait_time_list[start_time]
                    wait_time += attraction_list[j].ride_time  # 乗車時間
                    if wait_time >= 30:
                        start_time = fixed_time + round(wait_time / 30)
        else:
            flag = False
            break
    wait_time += walk_time[-1]  # 最後のアトラクションからゴール位置までの時間
    if flag:
        return wait_time, each_wait_time, walk_time
    else:
        return wait_time * 10000, each_wait_time, walk_time


class Attraction:
    # distance.csvのデータを2次元配列distance_listに格納
    with open("static/csv/distance.csv", 'r', encoding="utf-8")as f:
        reader = csv.reader(f)
        distance_list = [row for row in reader]

    def __init__(self, x, y, name=None, wait_time_list=None, ride_time=None, num=None):
        self.x = x
        self.y = y
        self.name = name
        self.wait_time_list = wait_time_list
        self.ride_time = ride_time
        self.num = num

    def distance(self, attraction):  # 二点間の距離の計算
        distance = np.sqrt((self.x - attraction.x) ** 2 + (self.y - attraction.y) ** 2)
        return distance

    # 設定した距離データで計算
    def setting_distance(self, attraction):
        distance = int(self.distance_list[self.num][attraction.num])
        return distance

    def __repr__(self):
        return f'{self.name}'


class Calculation:
    def __init__(self, route, ga):
        self.route = route
        self.start_place = ga.start_place
        self.end_place = ga.end_place
        self.start_time = ga.start_time
        self.attraction_list = ga.attraction_list
        self._time = 0
        self._each_time = 0  # 待ち時間list
        self.walk_time = 0  # 徒歩時間list
        self._distance = 0
        self._fitness = 0

    @property
    def time(self):  # 時間の計算
        if self._time == 0:
            path_time = wait_time_total(self.route, self.start_place, self.end_place,
                                        self.start_time, self.attraction_list)
            self._time = path_time[0]
            self._each_time = path_time[1]
            self.walk_time = path_time[2]
        return self._time, self._each_time, self.walk_time

    @property
    def distance(self):  # 総距離の計算
        if self._distance == 0:
            path_distance = 0
            # path_distance += self.start_place.setting_distance(self.route[0])  # 最初の地点
            path_distance += self.start_place.distance(self.route[0])  # 最初の地点

            for i in range(len(self.route) - 1):  # 距離
                from_city = self.route[i]
                to_city = self.route[(i + 1) % len(self.route)]
                # path_distance += from_city.setting_distance(to_city)  # どっちか
                path_distance += from_city.distance(to_city)  # どっちか

            # path_distance += self.end_place.setting_distance(self.route[-1])  # 最後の地点
            path_distance += self.end_place.distance(self.route[-1])  # 最後の地点
            self._distance = path_distance
        return self._distance

    @property
    def time_fitness(self):
        if self._fitness == 0:
            self._fitness = 1 / float(self.time[0])
        return self._fitness

    @property
    def distance_fitness(self):
        if self._fitness == 0:
            self._fitness = 1 / float(self.distance)
        return self._fitness


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


def mating_pool(population, selection_results):
    pool = [population[idx] for idx in selection_results]
    return pool


def breed_population(pool, elite_size):
    children = []
    length = len(pool) - elite_size
    pool = random.sample(pool, len(pool))

    for i in range(elite_size):
        children.append(pool[i])

    for i in range(length):
        child = breed(pool[i], pool[-i - 1])
        children.append(child)

    return children


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


def plot_route(route, start_place, end_place, img_filename, title=None):  # 表示
    img = imread("static/USJ_map.png")
    plt.figure()
    for i in range(len(route)):
        attraction = route[i]
        next_attraction = route[(i + 1) % len(route)]
        bbox_dict = dict(boxstyle='round', facecolor='#00bfff', edgecolor='#0000ff', alpha=0.75, linewidth=2.5,
                         linestyle='-')
        pyplot.text(attraction.x, attraction.y - 15, i + 1, bbox=bbox_dict)  # 番号の表示
        plt.scatter(attraction.x, attraction.y, c='red')
        if i >= len(route) - 1:
            break
        plt.plot((attraction.x, next_attraction.x), (attraction.y, next_attraction.y), c='black')
        if title:
            plt.title(title, fontname="MS Gothic")
    # スタート地点・ゴール地点のplot
    plt.scatter(start_place.x, start_place.y, c='blue')
    plt.scatter(end_place.x, end_place.y, c='blue')
    plt.plot((start_place.x, route[0].x), (start_place.y, route[0].y), c='black')
    plt.plot((end_place.x, route[-1].x), (end_place.y, route[-1].y), c='black')

    plt.imshow(img)
    # plt.show()
    plt.tick_params(labelbottom=False, labelleft=False, labelright=False, labeltop=False)  # ラベル消す
    plt.tick_params(bottom=False, left=False, right=False, top=False)  # ラベル消す
    # plt.subplots_adjust(left=0, right=0.975, bottom=0.1, top=0.9)  # 余白調整
    plt.savefig(img_filename, bbox_inches='tight', pad_inches=0)  # 画像で保存
    return img_filename


class GeneticAlgorithm:
    def __init__(self, attraction_list, distance_flag, start_place, end_place, start_time, random_string):
        self.attraction_list = attraction_list
        self.distance_flag = distance_flag
        self.start_place = start_place
        self.end_place = end_place
        self.start_time = start_time
        self.random_string = random_string

        self.generation = 50  # 世代数
        self.population_size = self.generation
        self.elite = int(self.population_size / 5)
        self.mutation_rate = 0.01

    def create_route(self):
        route = random.sample(self.attraction_list, len(self.attraction_list))
        return route

    def create_initial_population(self):
        population = []
        for i in range(self.population_size):
            population.append(self.create_route())
        return population

    def rank_routes(self, population):
        fitness_results = {}
        for i in range(len(population)):
            calc = Calculation(population[i], self)
            if self.distance_flag:
                fitness_results[i] = calc.distance_fitness
            else:
                fitness_results[i] = calc.time_fitness
        return sorted(fitness_results.items(), key=operator.itemgetter(1), reverse=True)

    def next_generation(self, current_gen, elite_size, mutation_rate):
        pop_ranked = self.rank_routes(current_gen)
        selection_results = selection(pop_ranked, elite_size)
        mate_pool = mating_pool(current_gen, selection_results)
        children = breed_population(mate_pool, elite_size)
        next_gen = mutate_population(children, mutation_rate)
        return next_gen

    def solve(self):
        pop = self.create_initial_population()

        for g in range(self.generation):
            pop = self.next_generation(pop, self.elite, self.mutation_rate)

        best_route_index = self.rank_routes(pop)[0][0]
        best_route = pop[best_route_index]
        calc = Calculation(best_route, self)
        if self.distance_flag:
            time_result = calc.time
            distance_result = round(1 / self.rank_routes(pop)[0][1], 2)
        else:
            time_result = calc.time
            distance_result = round(calc.distance, 2)

        if not self.distance_flag and time_result[0] > 10000:
            time_result = 0

        return best_route, time_result, distance_result

    def main(self):
        best_route = self.solve()
        img_name = plot_route(best_route[0], self.start_place, self.end_place, self.random_string)

        order_result = best_route[0]
        time_result = best_route[1]
        distance_result = best_route[2]

        return img_name, order_result, time_result, distance_result
