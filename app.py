import os
# import datetime
# import json
# from amadeus import Client, ResponseError

# amadeus = Client(client_id='GNEZjAg0tkEbPkWGGvvRteWxSBbSAXKU', client_secret='wYFTeSAIy0vAJIbq')
# data = amadeus.shopping.flight_offers_search.get(
#     originLocationCode=request.values['origin_code'],
#     destinationLocationCode=request.values['destination_code'],
#     departureDate=request.value['departure_date'],
#     adults=request.value['num_tickets']
# )
from flask import Flask, render_template, request
from google.cloud import bigquery       

import json
from datetime import datetime

f = open('flight_offer_data_example.json')
  
# returns JSON object as 
# a dictionary
flight_api_data = json.load(f)
big_data = []

values = """"""
flightNumber = 0
ticketNumber = 0
for flight_offer in flight_api_data:
    for segment in flight_offer['itineraries'][0]['segments']:
        # "2023-11-01T15:20:00"
        depature_datetime = datetime.strptime(segment['departure']['at'], "%Y-%m-%dT%H:%M:%S")
        big_data.append({'flightNumber': flightNumber,
                         'ticketNumber': ticketNumber,
                         'Price': flight_offer['price']['total'], 
                         'Month': depature_datetime.month, 
                         'DayofMonth': depature_datetime.day, 
                         'DayOfWeek': depature_datetime.weekday(), 
                         'Origin': segment['departure']['iataCode'], 
                         'Dest': segment['arrival']['iataCode'], 
                         'IATA_Code_Operating_Airline': segment['carrierCode']})
        values += "(%s, %s, %s, %s, %s, %s, \"%s\", \"%s\", \"%s\")," % (flightNumber, ticketNumber, flight_offer['price']['total'], depature_datetime.month,  depature_datetime.day, depature_datetime.weekday(), segment['departure']['iataCode'], segment['arrival']['iataCode'], segment['carrierCode'])
        flightNumber += 1
    ticketNumber += 1
values = values[:-1]


f.close()
client = bigquery.Client(project = "flightadvisor-379602")  # Setting client to correct projectID

CREATE_TABLE_QUERY = (
    """CREATE OR REPLACE TABLE flightadvisor-379602.flight_delays.big_data(
        flightNumber INT64,
        ticketNumber INT64,
        Price FLOAT64,
        Month INT64,
        DayofMonth INT64,
        DayOfWeek INT64,
        Origin STRING,
        Dest STRING,
        IATA_Code_Operating_Airline STRING
    );
    INSERT INTO flightadvisor-379602.flight_delays.big_data (
        flightNumber,
        ticketNumber,
        Price,
        Month,
        DayofMonth,
        DayOfWeek,
        Origin,
        Dest,
        IATA_Code_Operating_Airline
    )
    VALUES %s;
    """ % (values)
)

query_job = client.query(CREATE_TABLE_QUERY)  # API request
success = query_job.result()
print(success)

QUERY = (
"""SELECT
  predicted_Delayed,
  predicted_Delayed_probs,
  flightNumber,
  ticketNumber
FROM 
  ML.PREDICT(MODEL `flightadvisor-379602.flight_delays.delay_predictions_4`, (
    SELECT
      Month,
      IATA_Code_Operating_Airline,
      Origin,
      Dest,
      DayofMonth,
      DayOfWeek,
      flightNumber,
      ticketNumber
    FROM
      flightadvisor-379602.flight_delays.big_data
  ), STRUCT(0.33 AS threshold))""")



# Perform a query.
query_job = client.query(QUERY)  # API request
rows = query_job.result()  # Waits for query to finish
big_data.sort(key=lambda x: x['flightNumber'])

for row in rows:
    big_data[row.flightNumber]['predicted_Delayed'] = row.predicted_Delayed
    #print(row.Index)
    #print(row.predicted_Delayed)
    #print(row.predicted_Delayed_probs)                                      

from collections import defaultdict


grouped_big_data = defaultdict(list)

for flight in big_data:
    grouped_big_data[flight['ticketNumber']].append(flight)

# for ticket in grouped_big_data:       
#   for flight in ticket:
#                 print("%s | %s |$%s | %s -> %s | %s | %s" % (flight['flightNumber'], flight['ticketNumber'], flight['Price'], flight['Origin'], flight['Dest'], flight['IATA_Code_Operating_Airlin'], flight['predicted_Delayed']))

app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html", data=grouped_big_data.values())

@app.route('/update', methods=['POST', 'GET'])
def update():
    airline = ""
    date = ""
    price = ""
    delay = ""


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
