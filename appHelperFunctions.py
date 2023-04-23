import os
from amadeus import Client, ResponseError
from flask import Flask, render_template, request, jsonify
from google.cloud import bigquery       
import json
from datetime import datetime
from collections import defaultdict
import random
import pytz

airlines = None
timezones = None

def getTicketDataFromAPI(origin, dest, date, number_tickets):
    # amadeus = Client(client_id='GNEZjAg0tkEbPkWGGvvRteWxSBbSAXKU', client_secret='wYFTeSAIy0vAJIbq')
    # response = amadeus.shopping.flight_offers_search.get(
    #     originLocationCode=origin,
    #     destinationLocationCode=dest,
    #     departureDate=date,
    #     adults=number_tickets
    # )

    # with open("last_query_result.json", 'w', encoding='utf-8') as f:
    #     json.dump(response.data, f, ensure_ascii=False, indent=4)

    # with open("last_query_result_string.json", 'w', encoding='utf-8') as f:
    #     f.write(response.body)

    # res_1 = json.dumps(response.data)
    # res = json.loads(res_1)
    # return res
    
    f = open("last_query_result.json")
    data = json.load(f)
    f.close()
    return data

def getDropDownData():
    f = open('airport_codes_and_cities.json')
    
    # returns JSON object as 
    # a dictionary
    drop_down_data_raw = json.load(f)

    drop_down_data_fixed = []

    for airport in drop_down_data_raw:
        fixed_data = "{city}, {full_state}, United States | {airport_code}".format(city=airport['DestCityName'].split(',')[0], full_state=airport['DestStateName'], airport_code=airport['Dest'])
        drop_down_data_fixed.append(fixed_data)

    f.close()
    
    return drop_down_data_fixed

def getGroupedData(data):
    # returns JSON object as 
    # a dictionary
    flight_api_data = data
    big_data = []

    values = """"""
    flightNumber = 0
    ticketNumber = 0

    global airlines
    if airlines is None:
        f = open('airline_codes.json')

        airline_codes = json.load(f)
        airlines = {}

        for airline in airline_codes:
            airlines[airline['IATA_Code_Operating_Airline']] = airline['Airline']

        f.close()

    global timezones
    if timezones is None:
        timezones_file = open('timezone_map.txt')

        timezones = {}

        for line in timezones_file:
            parts = line.split("\t")
            timezones[parts[0]] = parts[1].split("\n")[0]

        timezones_file.close()

    for flight_offer in flight_api_data:
        for segment in flight_offer['itineraries'][0]['segments']:
            depature_datetime = datetime.strptime(segment['departure']['at'], "%Y-%m-%dT%H:%M:%S")
            big_data.append({'flightNumber': flightNumber,
                            'ticketNumber': ticketNumber,
                            'Price': flight_offer['price']['total'], 
                            'Month': depature_datetime.month, 
                            'DayofMonth': depature_datetime.day, 
                            'DayOfWeek': depature_datetime.weekday(), 
                            'Origin': segment['departure']['iataCode'], 
                            'Dest': segment['arrival']['iataCode'],
                            'Origin_DateTime': segment['departure']['at'], 
                            'Dest_DateTime': segment['arrival']['at'], 
                            'IATA_Code_Operating_Airline': segment['carrierCode'],
                            'Airline': airlines[segment['carrierCode']],
                            'Origin_Timezone': timezones[segment['departure']['iataCode']],
                            'Dest_Timezone': timezones[segment['arrival']['iataCode']]})
            values += "(%s, %s, %s, %s, %s, %s, \"%s\", \"%s\", \"%s\")," % (flightNumber, ticketNumber, flight_offer['price']['total'], depature_datetime.month,  depature_datetime.day, depature_datetime.weekday(), segment['departure']['iataCode'], segment['arrival']['iataCode'], segment['carrierCode'])
            flightNumber += 1
        ticketNumber += 1
    values = values[:-1]

    # with open("big_data_dump.json", 'w', encoding='utf-8') as f:
    #     json.dump(big_data, f, ensure_ascii=False, indent=4)

    client = bigquery.Client(project = "flightadvisor-379602")  # Setting client to correct projectID

    CREATE_TABLE_QUERY = (
        """CREATE OR REPLACE TABLE flightadvisor-379602.flight_delays.big_data2(
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
        INSERT INTO flightadvisor-379602.flight_delays.big_data2 (
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
    # print("galkdjflkasjdflkasdjflkjdflksajdflkjs\n\n\n")
    print(success)

    QUERY = (
    """SELECT
    predicted_Delayed,
    predicted_Delayed_probs,
    flightNumber,
    ticketNumber
    FROM 
    ML.PREDICT(MODEL `flightadvisor-379602.flight_delays.delay_predictions_5`, (
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
        flightadvisor-379602.flight_delays.big_data2
    ), STRUCT(0.3044 AS threshold))""")

    # Perform a query.
    query_job = client.query(QUERY)  # API request
    rows = query_job.result()  # Waits for query to finish
    big_data.sort(key=lambda x: x['flightNumber'])

    for row in rows:
        big_data[row.flightNumber]['predicted_Delayed_probs'] = row.predicted_Delayed_probs[0]['prob']         # bucket the probabilities

        if row.predicted_Delayed_probs[0]['prob'] < 0.30:
            big_data[row.flightNumber]['predicted_Delayed_prob_status'] = 'Low'

        elif row.predicted_Delayed_probs[0]['prob'] < 0.40: 
            big_data[row.flightNumber]['predicted_Delayed_prob_status'] = 'Medium'

        else:
            big_data[row.flightNumber]['predicted_Delayed_prob_status'] = 'High'

        origin_datetime = datetime.strptime(big_data[row.flightNumber]['Origin_DateTime'], "%Y-%m-%dT%H:%M:%S")
        dest_datetime = datetime.strptime(big_data[row.flightNumber]['Dest_DateTime'], "%Y-%m-%dT%H:%M:%S")
        
        origin_datetime = origin_datetime.astimezone(pytz.timezone(big_data[row.flightNumber]['Origin_Timezone'])).strftime('%Y-%m-%d~%H:%M:%S %Z')
        dest_datetime = dest_datetime.astimezone(pytz.timezone(big_data[row.flightNumber]['Dest_Timezone'])).strftime('%Y-%m-%d~%H:%M:%S %Z')

        big_data[row.flightNumber]['Origin_DateTime'] = origin_datetime.split("~")[0].split("-")[1] + "/" + origin_datetime.split("~")[0].split("-")[2] + " @ " + origin_datetime.split("~")[1]
        big_data[row.flightNumber]['Dest_DateTime'] = dest_datetime.split("~")[0].split("-")[1] + "/" + dest_datetime.split("~")[0].split("-")[2] + " @ " + dest_datetime.split("~")[1]    

    grouped_big_data = defaultdict(list)

    for flight in big_data:
        grouped_big_data[flight['ticketNumber']].append(flight)
        
    return grouped_big_data


