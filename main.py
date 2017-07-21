#! -*- coding:utf-8 -*-
from CHT import Preprocess
from CHT import Mode_Detection
from CHT import External
import os, errno
import csv
import time
import pandas
import argparse


def csv_output(result, file_name_list=['od.csv', 'stop.csv']):
	file_list = list()
	writer_list = list()

	try:
		os.makedirs('output/')
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	for name in file_name_list:
		temp = open('output/'+name, 'w')
		temp_writer = csv.writer(temp, delimiter=',')
		writer_list.append(temp_writer)
		file_list.append(temp)
	for data in result:
		#print(data)
		for i in range(len(file_name_list)):
			for temp_d in data[i]:
				writer_list[i].writerow(temp_d)
	for i in range(len(file_name_list)):
		file_list[i].close()
		print "Result has been write into output/"+file_name_list[i]


def mrt_main(date):
	user_data_path = "./data/user_data/"+date+"/"
	rf_sys_path = "./data/reference system/entrance_tower_to_subway_k_1.csv"
	mrt_route_file = "./data/mrt_route.csv"
	mrt_entrance_file = "./data/mrt_station_entrance.csv"
	travel_time_file = "./data/mrt_travel_time.csv"
	result = []
	for file_name in os.listdir(user_data_path):
		#new part
		f = open(os.path.join(user_data_path,file_name),"r")
		user_raw_data = [[row[0], row[4], row[2], row[3]] for row in
						 csv.reader(f, delimiter='|')]  # [imsi, unix_time, lon, lat]
		raw_data_df = pandas.DataFrame(user_raw_data, columns=['imsi', 'unix_time', 'lon', 'lat'])
		raw_data_df = raw_data_df.sort_values(['unix_time'])
		user_raw_data_sorted = raw_data_df.values.tolist()
                f.close()
                user_data = Preprocess.preprocessing(user_raw_data_sorted) #[imsi, start_time, end_time, lon, lat]
		# print(user_data)
		r = Mode_Detection.MRT_trip_detection(user_data,rf_sys_path,mrt_route_file,mrt_entrance_file,travel_time_file)
		if len(r) == 0:
			continue
		if len(r[0]) == 0:
			continue
		result.append(r)
	csv_output(result, ['mrt_'+date+'.csv', 'mrt_path_'+date+'.csv'])

def bus_main(date):
    user_data_path = "./data/user_data/"+date+"/"

    all_user_data = dict()
    for file_name in os.listdir(user_data_path):
        f = open(os.path.join(user_data_path, file_name),"r")
        user_raw_data = [[row[0], row[4], row[2], row[3]] for row in csv.reader(f, delimiter='|')] #[imsi, unix_time, lon, lat]
        raw_data_df = pandas.DataFrame(user_raw_data, columns=['imsi', 'time', 'lon', 'lat'])
        raw_data_df = raw_data_df.sort_values(['time'])
        user_raw_data_sorted = raw_data_df.values.tolist()
        user_data = Preprocess.preprocessing(user_raw_data_sorted) #[imsi, start_time, end_time, lon, lat]
        all_user_data[user_data[0][0]] = user_data
        f.close()

    TPE_route = External.bus_route('taipei')
    NWT_route = External.bus_route('newtaipei')
    route = TPE_route
    for key in NWT_route.keys():
        route[key] = NWT_route[key]

    #route = pickle.load(open("bus_route.pickle", "rb"))

    rid2user,user2rid,route2rid = Preprocess.bus_spatial_index(route, all_user_data)
    SpeedDis = [20]*24
    result = Mode_Detection.bus_trip_detection(rid2user, user2rid, route2rid, route, SpeedDis)

    output_result = [(result,)]
    #print result
    csv_output(output_result, ['bus_'+date+'.csv'])

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("mode", type=str, help='(mrt/bus/hsr/train)')
	parser.add_argument("date", type=str, help='(yyyymmdd)')
	args = parser.parse_args()
	print "Detection mode: ", args.mode
	print "Date: ", args.date
	print "Start processing..."

	if args.mode == "mrt" or args.mode == "MRT":
		start_time = time.time()
		mrt_main(args.date)
		end_time = time.time()
		print "================"
		print "time: {:.2f} seconds".format(end_time - start_time)
	elif args.mode == "bus" or args.mode == "Bus":
		start_time = time.time()
		bus_main(args.date)
		end_time = time.time()
		print "================"
		print "time: {:.2f} seconds".format(end_time - start_time)
	else:
		pass
