#!/usr/bin/env python3
from bs4 import BeautifulSoup
import copy
import datetime
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning


class GetParkData(object):
    #
    # attractions_list: list of attraction
    # renew_timelist: list of renew time
    # renew_timetable: table of renew time table
    #
    def __init__(self, year, month, day,
                 url='https://usjreal.asumirai.info/today'):
        self.year = year
        self.month = month
        self.day = day

        # to be disable to display SSL Error Warnings.
        urllib3.disable_warnings(InsecureRequestWarning)

        # set url from which you get infomation via internet.
        self.prefix = url
        self.parse_original_webpage('{0}/usj-{1}-{2}-{3}.html'.
                                    format(url, year, month, day))

        # in this case, self.url is gotten in `parse_original_webpage'
        self.main()

    def parse_original_webpage(self, url):
        html = requests.get(url, verify=False)
        soup = BeautifulSoup(html.content, 'html.parser')

        #  this is the url to be checked webpage for us.
        self.url = (self.prefix + soup.find(class_='yoso-link').get('href')).\
            replace('today/', '')
        #
        # rank is rank on the day
        #
        self.rank = soup.find(class_='rank-col rank').text[-1].lower()

    def main(self):
        self.check()
        self.parse()

    def show_info(self):
        #
        # debug method
        #
        print('*** INFO: {0}/{1}/{2}'.format(self.year, self.month, self.day))

        print(self.attractions_list)
        print(self.renew_timelist)
        print(self.renew_timetable)
        print('-------------------------')
        print()

    def check(self):
        html = requests.get(self.url, verify=False)
        self.soup = BeautifulSoup(html.content, 'html.parser')
        self.get_tagname()

    def get_tagname(self):
        self.tagname = None
        #
        # get encrypted tag name
        #
        data_region = False
        n = 0
        for line in str(self.soup).split('\n'):
            if data_region:
                if line.strip() == '':
                    continue
                n += 1
                if n == 8:
                    self.tagname = line.replace('"', ' ').replace("'", ' ').\
                                        split('=')[1].split()[0]
                    return
            else:
                if 'class' in line and 'read_cat' in line:
                    data_region = True
                    continue
        if self.tagname is None:
            print('tagname is undefined.')
            exit()

    def get_total_data_array(self):
        # common data to parse attractions list and time tables
        total_data_array = []
        for (i, x) in enumerate(self.soup.find_all(class_=self.tagname)):
            if len(str(x).split('\n')) > 20:
                total_data_array.append(x)
        return total_data_array

    def parse_each_category(self, total_data):
        # common data to parse attractions list and time tables
        tag_attr = None
        for (i, line) in enumerate(str(total_data).split('\n')):
            if i == 1:
                tag_attr = line.split()[0].strip().replace('<', '')
                break

        time_list = total_data.find(class_=self.tagname)

        #  subtag is used to extract attractions list
        subtag = str(time_list.span).replace('"', ' ').split()[2]
        table_data = total_data.find_all(tag_attr)
        renew_timetable = []
        renew_timelist = []
        attractions_list = []
        for (i, data) in enumerate(table_data):
            if i == 0:
                # 1st row is attraction list
                attractions_list = \
                    [x.text for x in data.find_all(class_=subtag)]
                attractions_list.pop(0)
            else:
                # tbl is temporary data about timetable
                tbl = data.text.split('\n')
                tbl.pop(0)
                tbl.pop(-1)
                schedule = []
                for (i, x) in enumerate(tbl):
                    if i == 0:
                        renew_timelist.append(x)
                    else:
                        if x == '-' or x == '':
                            #  `-' means no data
                            schedule.append(None)
                        else:
                            schedule.append(int(x))
                renew_timetable.append(schedule)
        return {'attractions_list': attractions_list,
                'timetable': renew_timetable,
                'timelist': renew_timelist}

    def get_ntime(self):
        total_data = self.get_total_data_array()[0]
        return len(self.parse_each_category(total_data)['timelist'])

    def parse(self):
        self.ntime = self.get_ntime()
        self.attractions_list = []
        self.renew_timetable = [[] for _ in range(self.ntime)]
        self.renew_timelist = []
        for total_data in self.get_total_data_array():
            park_data = self.parse_each_category(total_data)
            attractions_list = park_data['attractions_list']
            renew_timetable = park_data['timetable']
            if len(self.renew_timelist) == 0:
                self.renew_timelist = park_data['timelist']
            for i in range(self.ntime):
                self.renew_timetable[i] += renew_timetable[i]
            self.attractions_list += attractions_list


class GetDateList(object):
    def __init__(self, year, month, day, width):
        #
        # calculate date and listize date data
        #
        self.year = year
        self.month = month
        self.day = day
        self.width = width
        self.main()

    def main(self):
        reference_date = datetime.datetime(self.year,
                                           self.month,
                                           self.day,
                                           0,  # hour
                                           0,  # min
                                           0,  # sec
                                           0)  # other
        self.date_list = []
        for delta_day in range(self.width+1):
            dt = reference_date + datetime.timedelta(days=-delta_day)
            dayinfo = {'year': dt.year,
                       'month': dt.month,
                       'day': dt.day}
            self.date_list.append(dayinfo)


class StatisticalQueue(object):
    #
    # main class for statistical process for all attractions
    #
    def __init__(self, year, month, day, width):
        self.year = year
        self.month = month
        self.day = day
        self.width = width
        self.main()

    def main(self):
        self.getdata()
        self.statistical_proc()
        self.write_csv()

    def statistical_proc(self):
        ref_attractions_list = self.reference_dateinfo.attractions_list
        ref_time_list = self.reference_dateinfo.renew_timelist
        ntime = len(ref_time_list)

        self.attractions_data = []
        for target in ref_attractions_list:
            self.attractions_data.append(AttractionData(target, ref_time_list))

        for dateinfo in self.dateinfo:
            attractions_list = dateinfo.attractions_list
            timetable = dateinfo.renew_timetable
            rank = dateinfo.rank
            for (jattraction, target) in enumerate(ref_attractions_list):
                #
                #  jattraction: index for attraction in `ref_attractions_list'
                #               which is the attractions list in refernce date
                #
                # target is not included previous data
                if target not in attractions_list:
                    break
                #
                # check for index at previous data
                #  iattraction: index of attracion in previous data
                #
                iattraction = attractions_list.index(target)
                for itime in range(ntime):
                    time = ref_time_list[itime]
                    # wait time in previous data
                    value = timetable[itime][iattraction]
                    self.attractions_data[jattraction].add_data(time, value,
                                                                rank)

        #
        # calculate variance and average
        #
        for jattraction in range(len(ref_attractions_list)):
            self.attractions_data[jattraction].get_categorize_timetable()

    def getdata(self):
        date_list = GetDateList(self.year,
                                self.month,
                                self.day,
                                self.width).date_list
        self.dateinfo = []
        for (i, datedata) in enumerate(date_list):
            year = datedata['year']
            month = datedata['month']
            day = datedata['day']
            if i == 0:  # reference day
                self.reference_dateinfo = GetParkData(year, month, day)
            self.dateinfo.append(GetParkData(year, month, day))

    def write_csv(self, prefix='rank-'):
        suffix = '.csv'
        symbols = ['a', 'b', 'c', 'd', 'e', 'f', 's']
        fouts_var = []
        fouts_ave = []
        for (i, sym) in enumerate(symbols):
            filename = 'static/csv/TimeList/{0}{1}-variance{2}'.format(prefix, sym, suffix)
            fouts_var.append(open(filename, mode='w'))
            filename = 'static/csv/TimeList/{0}{1}-average{2}'.format(prefix, sym, suffix)
            fouts_ave.append(open(filename, mode='w'))

        attractions_list = self.reference_dateinfo.attractions_list
        time_list = self.reference_dateinfo.renew_timelist
        nattr = len(attractions_list)

        #
        # write header
        #
        for fout in fouts_var + fouts_ave:
            fout.write(' ,')
            for iattr in range(nattr):
                fout.write(attractions_list[iattr])
                if iattr < nattr - 1:
                    fout.write(', ')
                else:
                    fout.write('\n')

        #
        # write averages
        #
        for isym in range(len(symbols)):
            symbol = symbols[isym]
            fout = fouts_ave[isym]
            for (itime, ptime) in enumerate(time_list):
                fout.write('{}, '.format(ptime))
                for iattr in range(nattr):
                    wait_time = self.attractions_data[iattr].\
                        categorized_average[itime][symbol]
                    #  fout.write('{}'.format(wait_time))
                    if wait_time is None:
                        fout.write('{}'.format(wait_time))
                    else:
                        fout.write('{}'.format(round(wait_time, 0)))
                    if iattr < nattr - 1:
                        fout.write(' ,')
                    else:
                        fout.write('\n')
        #
        # write variances
        #
        for isym in range(len(symbols)):
            symbol = symbols[isym]
            fout = fouts_var[isym]
            for (itime, ptime) in enumerate(time_list):
                fout.write('{}, '.format(ptime))
                for iattr in range(nattr):
                    wait_time = self.attractions_data[iattr].\
                        categorized_variance[itime][symbol]
                    #  fout.write('{}'.format(wait_time))
                    if wait_time is None:
                        fout.write('{}'.format(wait_time))
                    else:
                        fout.write('{}'.format(round(wait_time, 0)))
                    if iattr < nattr - 1:
                        fout.write(' ,')
                    else:
                        fout.write('\n')

        #
        # finalize
        #
        for fout in fouts_var + fouts_ave:
            fout.close()


class AttractionData(object):
    #
    # store class for waiting timetable for each attraction
    #   among the term.
    #
    def __init__(self, attraction_name, time_list):
        #
        # rule to categorize
        #
        self.symbols = ['a', 'b', 'c', 'd', 'e', 'f', 's']
        self.threshold = [30, 60, 90, 110, 140, 160]

        self.attraction_name = attraction_name
        self.time_list = time_list
        self.table = [[] for _ in range(len(self.time_list))]
        self.rank_data = [[] for _ in range(len(self.time_list))]

    def add_data(self, time, value, rank):
        time_index = self.time_list.index(time)
        if value is not None:
            self.table[time_index].append(value)
            self.rank_data[time_index].append(rank)

    def _categorize(self, value):
        #
        # symbols: working symbol to categorize
        #
        symbols = copy.deepcopy(self.symbols)
        last_symbol = symbols.pop(-1)

        #
        # internal method for categorization
        #
        for (v, s) in zip(self.threshold, symbols):
            if value < v:
                return s
        return last_symbol

    def _get_categorized_array(self, array, ranks):
        #
        # internal method for catetorization to array component
        #
        categorized_array = [[] for _ in range(len(self.symbols))]
        for i in range(len(self.symbols)):
            for (j, x) in enumerate(array):
                if ranks[j] == self.symbols[i]:
                    categorized_array[i].append(x)
        return categorized_array

    def get_categorize_timetable(self):
        ntime = len(self.time_list)
        self.categorized_timetable = [[] for _ in range(ntime)]
        for itime in range(ntime):
            array = self.table[itime]
            ranks = self.rank_data[itime]
            self.categorized_timetable[itime] = \
                self._get_categorized_array(array, ranks)
        self._calc_statistical_quantities()

    def _calc_statistical_quantities(self):
        ntime = len(self.time_list)
        self.categorized_average = [{} for _ in range(ntime)]
        self.categorized_variance = [{} for _ in range(ntime)]
        for itime in range(ntime):
            time_data = self.categorized_timetable[itime]
            for isym in range(len(self.symbols)):
                symbol = self.symbols[isym]
                categorized_array = np.array(time_data[isym])
                if len(categorized_array) > 0:
                    average = np.average(categorized_array)
                    variance = np.var(categorized_array)
                else:
                    average = None
                    variance = None
                self.categorized_average[itime][symbol] = average
                self.categorized_variance[itime][symbol] = variance


if __name__ == '__main__':
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # 日本時間取得
    year = 2020
    month = 12
    day = now.day - 1
    width = 90
    StatisticalQueue(year, month, day, width)
