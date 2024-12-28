from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import joblib
import pandas as pd
import mysql.connector
from flask_bcrypt import Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)
geolocator = Nominatim(user_agent="flood_monitoring_app")
API_KEY = 'ede1f9002e7a44558da162543242312'
BASE_URL = 'http://api.weatherapi.com/v1/history.json'
WEATHER_API_URL = "http://api.weatherapi.com/v1/forecast.json"
model = joblib.load("flood_prediction_model.pkl")
scaler = joblib.load("scaler.pkl")

db_config = {
    'host': 'localhost',        
    'port': 3306,               
    'user': 'root',
    'password': 'thanh0123456789',
    'database': 'flood_monitoring'
}


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required"}), 400

        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Query user data
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user["password_hash"], password):
            return jsonify({"success": False, "error": "Invalid username or password"}), 401

        # Close the connection
        cursor.close()
        conn.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route('/api/add-user', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        cursor.execute(query, (username, hashed_password))
        connection.commit()

        return jsonify({'message': 'User added successfully'}), 201

    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry
            return jsonify({'error': 'Username already exists'}), 409
        return jsonify({'error': f'Database error: {err}'}), 500

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def get_coordinates(city_name):
    location = geolocator.geocode(city_name + ", Vietnam")
    if location:
        return location.latitude, location.longitude
    else:
        return None

@app.route("/api/flood-data", methods=["GET"])
def get_flood_data():
    location = request.args.get("location", None)  
    if not location:
        return jsonify({"error": "Location parameter is required"}), 400

    latitude, longitude = get_coordinates(location)
    monthly_data = get_monthly_precipitation(latitude, longitude, API_KEY)
    return jsonify(monthly_data), 200


def get_monthly_precipitation(lat, lon, api_key):
    precipitation_data = []
    for days_ago in range(30):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        params = {
            'key': api_key,
            'q': f"{lat},{lon}",  
            'dt': date,
        }
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            daily_rain = data.get('forecast', {}).get('forecastday', [])[0].get('day', {}).get('totalprecip_mm', 0)
            precipitation_data.append({
                'date': date,
                'rain': daily_rain
            })
        else:
            print(f"Failed to fetch data for {date}: {response.status_code}")
    return precipitation_data

@app.route("/api/weather-forecast", methods=["GET"])
def weather_forecast():
    location = request.args.get("location")
    if not location:
        return jsonify({"error": "Location parameter is required"}), 400
    latitude, longitude = get_coordinates(location)
    params = {
        "key": API_KEY,
        'q': f"{latitude},{longitude}", 
        "days": 2  
    }
    try:
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()

        if "forecast" in weather_data and "forecastday" in weather_data["forecast"]:
            tomorrow_forecast = weather_data["forecast"]["forecastday"][1]
            forecast = {
                "date": tomorrow_forecast["date"],
                "temp": tomorrow_forecast["day"]["avgtemp_c"],
                "condition": tomorrow_forecast["day"]["condition"]["text"],
                "humidity": tomorrow_forecast["day"]["avghumidity"],
                "wind": tomorrow_forecast["day"]["maxwind_kph"]
            }
            return jsonify(forecast), 200
        else:
            return jsonify({"error": "No forecast data available"}), 404

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Weather API request failed: {str(e)}"}), 500
    
@app.route("/api/predict-flood", methods=["POST"])
def predict_flood():
    data = request.get_json()
    rainfall_mm = data.get("rainfall_mm")
    if rainfall_mm is None:
        return jsonify({"error": "Missing rainfall_mm parameter"}), 400

    rainfall_df = pd.DataFrame([[rainfall_mm]], columns=["rainfall_mm"])
    rainfall_scaled = scaler.transform(rainfall_df)

    prediction = model.predict(rainfall_scaled)[0]
    probability = model.predict_proba(rainfall_scaled)[0][1]

    return jsonify({
        "rainfall_mm": rainfall_mm,
        "flood_prediction": bool(prediction),
        "flood_probability": round(probability, 2)
    })


if __name__ == "__main__":
    app.run(debug=True)
