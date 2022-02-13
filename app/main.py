# main.py
import json, requests, sqlite3
from flask import Flask, jsonify
from datetime import date

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

database = "database.db"

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def get_db(db):
	conn = sqlite3.connect(db)
	conn.row_factory = dict_factory # treat rows as dictionaries
	return conn

def save_company_info(data):
	conn = get_db(database)
	cur = conn.cursor()

	company = cur.execute("SELECT * FROM companies WHERE businessid = ?", (data['business_id'],)).fetchone()

	# insert company into db if it doesn't exist
	if company is None:
		conn.execute("INSERT INTO companies (businessid, name, address, phone, website) VALUES (?, ?, ?, ?, ?)", (data['business_id'], data['name'], data['address'][0], data['phone'][0], data['website'][0]))
		conn.commit()
		conn.close()
	# update only if data from prh is newer
	else:
		if data['address'][1] > company['saved']:
			conn.execute("UPDATE companies SET address = ?, saved = ? WHERE businessid = ?", (data['address'][0], date.today(), data['business_id']))
		if data['phone'][1] > company['saved']:
			conn.execute("UPDATE companies SET phone = ?, saved = ? WHERE businessid = ?", (data['phone'][0], date.today(), data['business_id']))
		if data['website'][1] > company['saved']:
			conn.execute("UPDATE companies SET website = ?, saved = ? WHERE businessid = ?", (data['website'][0], date.today(), data['business_id']))
		conn.commit()
		conn.close()

@app.get("/api/company/<string:id>")
def get_company_info(id):
	try:
		response = requests.get("https://avoindata.prh.fi/bis/v1/" + id)
		response.raise_for_status()
	except requests.exceptions.HTTPError as error:
		return str(error), response.status_code
		
	result = response.json()['results'][0]

	data = {
		"business_id": result['businessId'],
		"name": result['name'],
		"address": ("", ""),
		"phone": ("", ""),
		"website": ("", "")
	}

	# parse valid contact info with registration date(s)
	for address in result['addresses']:
		if address['endDate'] is None and address['street'] != "":
			data['address'] = (address['street'] + ", " + address['postCode'] + " " + address['city'], address['registrationDate'])

	for contactdetail in result['contactDetails']:
		if contactdetail['endDate'] is None and "puhelin" in contactdetail['type'].lower() and contactdetail['value'] != "":
			data['phone'] = (contactdetail['value'], contactdetail['registrationDate'])
		if contactdetail['endDate'] is None and "www" in contactdetail['type'].lower() and contactdetail['value'] != "":
			data['website'] = (contactdetail['value'], contactdetail['registrationDate'])

	try:
		save_company_info(data)
	except sqlite3.Error as error:
		print(error)

	# omit registration dates from resulting json
	data['address'] = data['address'][0]
	data['phone'] = data['phone'][0]
	data['website'] = data['website'][0]

	return jsonify(data)

@app.get("/api/company/list")
def company_info_list():
	companies = {}
	
	try:
		conn = get_db(database)
		cur = conn.cursor()
		companies = cur.execute("SELECT * FROM companies").fetchall()
	except sqlite3.Error as error:
		return str(error), 404
		
	conn.close()

	return jsonify(companies)

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, port=80)
