# -*- coding: utf-8 -*-
from flask import Flask, flash, redirect, url_for, request, render_template
import os
import re
from flask_jsglue import JSGlue
import psycopg2
from psycopg2 import sql

app = Flask(__name__)
jsglue = JSGlue(app)
conn = psycopg2.connect(host="localhost",database="frio1", user="frio1", password="amanda")

actual_position = ''
globalDistance = 500
globalSelect = ''

def iter_row(cursor, size=10):
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

def find_services(cur):
	cur.execute("SELECT COUNT(osm_id), amenity FROM planet_osm_point GROUP BY amenity")
	services = []
	for row in iter_row(cur, 10):
		services.append(row[1])
	return services

def find_only_services(cur, new_service, distance):
	actual_position = set_actual_position()
	lat = actual_position[0]
	lng = actual_position[1]
	geometry = cur.execute("SELECT body.name, ST_AsText(body.cesta) FROM( SELECT name, ST_Transform (way, 4326) as cesta " + 
		"FROM planet_osm_point WHERE amenity=%s)  as body " + 
		"WHERE ST_Distance_Sphere(ST_setSRID(ST_MakePoint(%s, %s), 4326), body.cesta) < %s", (new_service, lng, lat, distance))

	suradnice = []
	suradnica = []
	for row in iter_row(cur, 10):
		row = row[1]
		# print(row)
		temp = re.split('\(', row)
		lat = re.split(' ', temp[1])
		# print(lat[0])
		long = re.split('\)', lat[1])
		# print(lat[0])
		# print(long[0])
		suradnica.append(float(long[0]))
		suradnica.append(float(lat[0]))
		suradnice.append(suradnica)
		suradnica = []

	return suradnice

def find_names(cur, new_service):
	cur.execute("SELECT name, ST_AsText (ST_Transform (way, 4326)) FROM planet_osm_point WHERE amenity=%s", [new_service])
	names = []
	for row in iter_row(cur, 10):
		name = row[0]
		if name is None:
			name = 'Zial, toto miesto nie je zadefinovane.';
			# print(name)
		names.append(str(name))
		
	return names

def show_rivers(cur):
	rivers = cur.execute("SELECT ST_AsText (ST_Transform (way, 4326)) FROM planet_osm_line WHERE waterway='river'")
	all_polyLines = []
	for row in iter_row(cur, 10):
		print(type(row))
		new_row = ''.join(row)
		print(type(new_row))
		temp = re.split("\(", new_row)
		coordinates = re.split('\)', temp[1])
		print(coordinates)
		all_coordinates = re.split(',', coordinates[0])
		print(all_coordinates)
		polyLines = []
		polyLine = []
		for coordinate in all_coordinates:
			print(coordinate)
			coordinate = re.split(' ', coordinate)
			polyLine.append(float(coordinate[1]))
			polyLine.append(float(coordinate[0]))
			polyLines.append(polyLine)
			print(polyLines)
			polyLine = []
		all_polyLines.append(polyLines)
		polyLines = []
	return all_polyLines

def set_actual_position():
	actual_template = []
	global actual_position
	print('actual_position', actual_position)
	if actual_position == '':
		actual_position_array = [49.1390668, 20.2096027]
	else: 
		actual_position_array = []
		temp = re.split(',', actual_position)
		print(temp)
		temp_actual_position = re.split(' ', temp[1])
		actual_position_array.append(float(temp[0]))
		actual_position_array.append(float(temp_actual_position[1]))
	return actual_position_array


@app.route('/', methods=['GET', 'POST'])
def index():
	new_service = ''
	all_points = []

	if new_service == '':
		new_service = 'school'

	cur = conn.cursor()
	cur.execute('SELECT version()')
	cur.execute("SELECT COUNT(osm_id), highway FROM planet_osm_line GROUP BY highway")

	services = cur.execute("SELECT COUNT(osm_id), amenity FROM planet_osm_point GROUP BY amenity")
	names = []
	suradnice = []
	services = []

	services = find_services(cur)
	suradnice = find_only_services(cur, new_service, 500)
	names = find_names(cur, new_service)

	all_polyLines = []

	actual_position_array = actual_template = set_actual_position()



	print("The number of parts: ", cur.rowcount)
	cur.close()
	return render_template('index.html', services=services, suradnice=suradnice, new_service=new_service, names=names, 
											all_polyLines=all_polyLines, actual_position=actual_position_array, actual_template=actual_template, all_points=all_points, distance=0)

@app.route('/distance', methods=['GET', 'POST'])
def show_distance():
	cur = conn.cursor()
	cur.execute('SELECT version()')
	service = ''
	all_points = []

	new_service = ''
	select = request.form.get('comp_select')
	distance = request.form.get('distance')
	print('distance', distance)
	print('select', select)
	# print(select)

	global globalDistance
	global globalSelect

	if distance is None:
		distance = globalDistance
	else:
		distance = int(distance)
		globalDistance = distance

	# print(new_service)

	if select == '':
		new_service = globalSelect
	else:
		new_service = str(select)
		globalSelect = new_service

	print('select', select)
	print('new_service', new_service)
	print('globalSelect', globalSelect)

	names = []
	suradnice = []
	services = []

	actual_position_array = actual_template = set_actual_position()

	services = find_services(cur)
	suradnice = find_only_services(cur, new_service, distance)
	names = find_names(cur, new_service)
	# print(names)
	all_polyLines = []

	cur.close()
	return render_template('index.html', services=services, suradnice=suradnice, names=names, new_service=new_service, all_polyLines=all_polyLines,
											actual_position=actual_position_array, select=select, actual_template=actual_template, all_points=all_points, distance=distance)

@app.route('/polygons', methods=['GET', 'POST'])
def show_best():
	service = ''

	new_distance = ''
	select = request.form.get('distance_select')
	print(select)
	if select is None:
		select = 1000000
	else:
		if(select != 'all'):
			select = int(select)
		else:
			select = 1000000

	actual_position_array = actual_template = set_actual_position()

	if select:
		new_distance = int(select)
	else:
		new_distance = 10
	cur = conn.cursor()
	cur.execute('SELECT version()')

	# latlng = "49.1390668, 20.2096027"
	latlng = ''
	latlng = str(actual_position_array[0]) + ', ' + str(actual_position_array[1])
	print(latlng)
	print(type(select))

	cur.execute("SELECT polygons.coordinaty, polygons.cesta, polygons.name FROM (" + 
		"SELECT ST_AsText (ST_Transform (way, 4326)) AS coordinaty, name, tourism, " + 
		"ST_Distance_Sphere(ST_setSRID(ST_MakePoint(%s, %s), 4326), " + 
		"ST_Transform(ST_Centroid(way), 4326))  AS cesta " + "FROM planet_osm_polygon WHERE tourism!='null') AS polygons " + 
		"ORDER BY polygons.cesta LIMIT %s", (actual_position_array[1], actual_position_array[0], new_distance))
	

	names = []
	all_polygones = []
	for row in iter_row(cur, 10):
		# print(row[2])
		coordinates = row[0]
		distance = str(row[1])
		name = str(row[2])
		names.append(name)
		# print('Udaje: ', distance, name)
		temp = re.split('\(\(', coordinates)
		# print(temp)
		temp1 = re.split('\)\)', temp[1])
		# print(temp1)
		temp = re.split(',', temp1[0])
		# print(temp)
		polygones = []
		polygone = []
		for coordinate in temp:
			# print(coordinate)
			coordinate = re.split(' ', coordinate)
			# print(coordinate)
			if(coordinate[0][0] == '('):
				temp_c = re.split('\(', coordinate[0])
				coordinate[0] = temp_c[1]
			if(coordinate[1][len(coordinate[1]) - 1] == ')'):
				temp_c = re.split('\)', coordinate[1])
				coordinate[1] = temp_c[0]
			polygone.append(float(coordinate[1]))
			polygone.append(float(coordinate[0]))
			polygones.append(polygone)
			# print(polygones)
			polygone = []
		all_polygones.append(polygones)
		polygones = []

	services = find_services(cur)

	cur.close()
	return render_template('polygons.html', services=services, service='parking', new_service='parking', 
											all_polygones=all_polygones, names=names, actual_position=actual_position_array,
											actual_template=actual_template, select=select)

@app.route('/set_position/<position>', methods=['GET', 'POST'])
def set_position(position):
	latlng = ""
	print('position', position)
	new_position = re.split('\(', str(position))
	position = re.split(',', new_position[1])
	new_position = re.split(' ', position[1])
	temp_position = re.split('\)', new_position[1])
	
	latlng = latlng + position[0] + ", " + temp_position[0]
	service = ''
	global actual_position
	actual_position = latlng
	print('global_new', actual_position)
	return actual_position

@app.route('/lets-go-bicycle', methods=['GET', 'POST'])
def lets_go_bicycle():
	cur = conn.cursor()
	cur.execute('SELECT version()')

	bicycle_roads = cur.execute("SELECT ST_AsText(ST_Transform(lines.way, 4326)), points.name, lines.name, ST_Intersects(ST_Transform(points.way, 4326), ST_Transform(lines.way, 4326)), " + 
		"ST_AsText(ST_Transform(points.way, 4326)) FROM planet_osm_line " + 
		"as lines INNER JOIN planet_osm_point AS points ON (lines.bicycle = points.bicycle) " + 
		"WHERE lines.bicycle='yes' and points.name!='null' and ST_Intersects(ST_Transform(points.way, 4326), ST_Transform(lines.way, 4326))='true'")

	# bicycle_roads = cur.execute("SELECT ST_AsText (ST_Transform (way, 4326)) FROM planet_osm_roads WHERE bicycle='yes'")
	all_polyLines = []
	all_points = []
	for row in iter_row(cur, 10):
		points = []
		print(row[4])
		point = re.split('\(', row[4])
		temp = re.split(' ', point[1])
		temp_point = re.split('\)', temp[1])
		points.append(float(temp_point[0]))
		points.append(float(temp[0]))
		print(points)
		all_points.append(points)

		new_row = row[0]
		# print(type(new_row))
		temp = re.split("\(", new_row)
		coordinates = re.split('\)', temp[1])
		# print(coordinates)
		all_coordinates = re.split(',', coordinates[0])
		# print(all_coordinates)
		polyLines = []
		polyLine = []
		for coordinate in all_coordinates:
			# print(coordinate)
			coordinate = re.split(' ', coordinate)
			polyLine.append(float(coordinate[1]))
			polyLine.append(float(coordinate[0]))
			polyLines.append(polyLine)
			# print(polyLines)
			polyLine = []
		all_polyLines.append(polyLines)
		polyLines = []

	new_service = 'parking'
	# all_polyLines = show_bicycle_roads(cur)
	suradnice = []
	names = []

	global globalDistance
	distance = globalDistance
	global globalSelect

	actual_position_array = actual_template = set_actual_position()

	services = find_services(cur)
	return render_template('index.html', services=services, actual_template=actual_template, all_polyLines=all_polyLines, names=names, suradnice=suradnice, all_points=all_points, distance=distance)

if __name__ == '__main__':
   app.run(debug = True)




