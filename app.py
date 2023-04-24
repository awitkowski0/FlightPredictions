import os
# from amadeus import Client, ResponseError
from flask import Flask, render_template, request
from google.cloud import bigquery       
import json
from datetime import date
from collections import defaultdict
from appHelperFunctions import *

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
    drop_down_data_fixed = getDropDownData()
    return render_template("index.html", drop_down_data=drop_down_data_fixed, today=date.today())

@app.route('/update/', methods=['POST', 'GET'])
def update():
    print(request.form["submission"])

    if request.form["submission"] == "submit":
        origin = request.form['origins'].split('| ')[1]
        dest = request.form['destinations'].split('| ')[1]
        submit_date = request.form['flight-date']
        number_tickets = request.form['quantity']
        data = getTicketDataFromAPI(origin, dest, submit_date, number_tickets)         # make API call
        grouped_big_data = getGroupedData(data)                                 # set big_data from API results
        drop_down_data_fixed = getDropDownData()

        origin_kept = request.form['origins']
        dest_kept = request.form['destinations']
        date_kept = request.form['flight-date']
        quantity_kept = request.form['quantity']

        return render_template("index.html", ticket_data=grouped_big_data.values(), today=date.today(), drop_down_data=drop_down_data_fixed, override_origin=origin_kept, override_date=date_kept, override_quantity=quantity_kept, override_destination=dest_kept)

    else:
        f = open('airport_codes_and_cities.json')
        city_data = json.load(f)
        random_city = random.choice(city_data)
        drop_down_data_fixed = getDropDownData()
        random_city_dropdown_string = "{city}, {full_state}, United States | {airport_code}".format(city=random_city['DestCityName'].split(',')[0], full_state=random_city['DestStateName'], airport_code=random_city['Dest'])

        while random_city_dropdown_string == request.form['origins']:
            random_city_dropdown_string = "{city}, {full_state}, United States | {airport_code}".format(city=random_city['DestCityName'].split(',')[0], full_state=random_city['DestStateName'], airport_code=random_city['Dest'])

            random_city = random.choice(city_data)

        random_city_dropdown_string = "{city}, {full_state}, United States | {airport_code}".format(city=random_city['DestCityName'].split(',')[0], full_state=random_city['DestStateName'], airport_code=random_city['Dest'])

        origin = request.form['origins']
        submit_date = request.form['flight-date']
        quantity = request.form['quantity']

        return render_template("index.html", drop_down_data=drop_down_data_fixed, today=date.today(), override_origin=origin, override_date=submit_date, override_quantity=quantity, override_destination=random_city_dropdown_string)

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')