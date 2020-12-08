#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import random
import operator
import pandas as pd
import matplotlib.pyplot as plt
import string
from matplotlib.image import imread
from matplotlib import pyplot
import csv


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

    # 距離の計算
    def distance(self, attraction):
        distance = np.sqrt((self.x - attraction.x) ** 2 + (self.y - attraction.y) ** 2)  # 二点間の距離の計算
        # distance = int(self.distance_list[self.num][attraction.num])  # 設定した距離データで計算
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
        self.walk_speed = 40  # 歩く速さ
        self._each_wait_time = 0  # 待ち時間list
        self._each_walk_time = 0  # 徒歩時間list
        self._time = 0
        self._distance = 0
        self._fitness = 0

    # 徒歩時間の追加
    def add_walk_time(self, route):
        walk_time = [round(self.start_place.distance(route[0]) / self.walk_speed)]  # 最初の地点

        for i in range(len(route) - 1):  # 距離
            from_attraction = route[i]
            to_attraction = route[(i + 1) % len(route)]
            walk_time.append(round(from_attraction.distance(to_attraction) / self.walk_speed))  # どっちか

        walk_time.append(round(self.end_place.distance(route[-1]) / self.walk_speed))  # 最後の地点
        return walk_time

    # 所要時間の合計
    def calculate_total_time(self, route):
        start_time = self.start_time
        fixed_time = start_time  # スタート時間の固定
        each_walk_time = self.add_walk_time(route)
        total_time = 0
        flag = True
        each_wait_time = []
        for i in range(len(route)):
            if start_time < 29:
                total_time += each_walk_time[i]  # 徒歩時間
                for j in range(len(self.attraction_list)):
                    if route[i] == self.attraction_list[j]:
                        each_wait_time.append(self.attraction_list[j].wait_time_list[start_time])
                        total_time += self.attraction_list[j].wait_time_list[start_time]
                        total_time += self.attraction_list[j].ride_time  # 乗車時間
                        if total_time >= 30:
                            start_time = fixed_time + round(total_time / 30)
            else:
                flag = False
                break
        total_time += each_walk_time[-1]  # 最後のアトラクションからゴール位置までの時間
        if flag:
            return total_time, each_wait_time, each_walk_time
        else:
            return total_time * 10000, each_wait_time, each_walk_time

    @property
    def time(self):  # 時間の計算
        if self._time == 0:
            path_time = self.calculate_total_time(self.route)
            self._time, self._each_wait_time, self._each_walk_time = path_time
        return self._time, self._each_wait_time, self._each_walk_time

    @property
    def distance(self):  # 総距離の計算
        if self._distance == 0:
            path_distance = 0
            path_distance += self.start_place.distance(self.route[0])  # 最初の地点

            for i in range(len(self.route) - 1):  # 距離
                from_attraction = self.route[i]
                to_attraction = self.route[(i + 1) % len(self.route)]
                path_distance += from_attraction.distance(to_attraction)  # どっちか

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


def mutate(individual):  # 突然変異
    # This has mutation_rate chance of swapping ANY city, instead of having mutation_rate chance of doing
    # a swap on this given route...
    for swapped in range(len(individual)):
        if random.random() < 0.01:  # 突然変異率
            swap_with = int(random.random() * len(individual))
            individual[swapped], individual[swap_with] = individual[swap_with], individual[swapped]
    return individual


def mutate_population(population):
    mutated_pop = []
    for ind in population:
        mutated = mutate(ind)
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


def create_route(attraction_list):
    route = random.sample(attraction_list, len(attraction_list))
    return route


def create_initial_population(population_size, attraction_list):
    population = []
    for i in range(population_size):
        population.append(create_route(attraction_list))
    return population


class GeneticAlgorithm:
    def __init__(self, attraction_list, distance_flag, start_place, end_place, start_time):
        self.attraction_list = attraction_list
        self.distance_flag = distance_flag
        self.start_place = start_place
        self.end_place = end_place
        self.start_time = start_time

    def rank_routes(self, population):
        fitness_results = {}
        for i in range(len(population)):
            calc = Calculation(population[i], self)
            if self.distance_flag:
                fitness_results[i] = calc.distance_fitness
            else:
                fitness_results[i] = calc.time_fitness
        return sorted(fitness_results.items(), key=operator.itemgetter(1), reverse=True)

    def next_generation(self, current_gen, elite_size):
        pop_ranked = self.rank_routes(current_gen)
        selection_results = selection(pop_ranked, elite_size)
        mate_pool = mating_pool(current_gen, selection_results)
        children = breed_population(mate_pool, elite_size)
        next_gen = mutate_population(children)
        return next_gen

    def plot_route(self, route, title=None):  # 表示
        img = imread("static/USJ_map.png")

        # 画像ファイル名のランダム文字列
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(6)])
        img_filename = f"static/result/USJ_route_{random_string}.png"

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
        plt.scatter(self.start_place.x, self.start_place.y, c='blue')
        plt.scatter(self.end_place.x, self.end_place.y, c='blue')
        plt.plot((self.start_place.x, route[0].x), (self.start_place.y, route[0].y), c='black')
        plt.plot((self.end_place.x, route[-1].x), (self.end_place.y, route[-1].y), c='black')

        plt.imshow(img)
        # plt.show()
        plt.tick_params(labelbottom=False, labelleft=False, labelright=False, labeltop=False)  # ラベル消す
        plt.tick_params(bottom=False, left=False, right=False, top=False)  # ラベル消す
        # plt.subplots_adjust(left=0, right=0.975, bottom=0.1, top=0.9)  # 余白調整
        plt.savefig(img_filename, bbox_inches='tight', pad_inches=0)  # 画像で保存
        return img_filename

    def solve(self, generation, population_size, elite):
        pop = create_initial_population(population_size, self.attraction_list)

        for g in range(generation):
            pop = self.next_generation(pop, elite)

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

    def main(self, generation):
        population_size = generation
        elite = int(population_size / 5)

        best_route = self.solve(generation, population_size, elite)
        order_result, time_result, distance_result = best_route
        img_filename = self.plot_route(order_result)

        return order_result, time_result, distance_result, img_filename
