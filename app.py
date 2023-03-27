import os
# from amadeus import Client, ResponseError
from flask import Flask, render_template, request
from google.cloud import bigquery       
import json
from datetime import datetime
from collections import defaultdict
from appHelperFunctions import *

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
    drop_down_data_fixed = getDropDownData()
    return render_template("index.html", drop_down_data=drop_down_data_fixed)

@app.route('/update/', methods=['POST', 'GET'])
def update():
    origin = request.form['origins'].split('| ')[1]
    dest = request.form['destinations'].split('| ')[1]
    date = request.form['flight-date']
    number_tickets = request.form['quantity']
    data = getTicketDataFromAPI(origin, dest, date, number_tickets)         # make API call
    grouped_big_data = getGroupedData(data)                                 # set big_data from API results
    drop_down_data_fixed = getDropDownData()

    return render_template("index.html", ticket_data=grouped_big_data.values(), drop_down_data=drop_down_data_fixed)

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')

