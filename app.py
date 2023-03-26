import os
import datetime

from google.cloud import bigquery       
client = bigquery.Client(project = "flightadvisor-379602")  # Setting client to correct projectID

# Perform a query.
QUERY = (
    'SELECT Airline FROM `flight_delays.delays_2020` '      # Selecting first 100 airlines
    'LIMIT 100')
query_job = client.query(QUERY)  # API request
rows = query_job.result()  # Waits for query to finish

for row in rows:
    print(row.Airline)                                      # Printing first 100 rows

from flask import Flask, render_template, request
app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
