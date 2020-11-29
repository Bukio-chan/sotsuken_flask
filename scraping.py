#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import csv

url = 'https://usjportal.net/'
html = requests.get(url)
soup = BeautifulSoup(html.content, "html.parser")
table = soup.find_all(class_="waittime")


# tdを取り除く
def remove_td(td):
    for i in range(len(td)):
        td[i] = td[i].string
        if td[i] == '-':
            td[i] = '0'
    return td


table_csv = []
for i in range(len(table)):
    table_csv.append(remove_td(table[i].find_all("td")))

csv_ = []
for i in range(len(table_csv)):
    csv_1 = []
    length = len(table_csv[i])
    n = 0
    s = int(len(table_csv[i]) / 29)
    for j in range(len(table_csv[i])):
        csv_1.append(table_csv[i][n:n + s:1])
        n += s
        if n >= length:
            break
    csv_.append(csv_1)

for j in range(len(table_csv)):
    file = open(f'static/csv/table_{j+1}.csv', 'w', newline='')
    w = csv.writer(file)
    for i in range(len(csv_[j])):
        w.writerow(csv_[j][i])

    file.close()
