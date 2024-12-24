from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import joblib
import pandas as pd
app = Flask(__name__)
CORS(app)
geolocator = Nominatim(user_agent="flood_monitoring_app")
API_KEY = 'ede1f9002e7a44558da162543242312'
BASE_URL = 'http://api.weatherapi.com/v1/history.json'
WEATHER_API_URL = "http://api.weatherapi.com/v1/forecast.json"
model = joblib.load("flood_prediction_model.pkl")
scaler = joblib.load("scaler.pkl")


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
    # Nhận dữ liệu từ front-end
    data = request.get_json()
    rainfall_mm = data.get("rainfall_mm")

    if rainfall_mm is None:
        return jsonify({"error": "Missing rainfall_mm parameter"}), 400

    # Tạo DataFrame với tên cột để phù hợp với scaler
    rainfall_df = pd.DataFrame([[rainfall_mm]], columns=["rainfall_mm"])
    
    # Chuẩn hóa dữ liệu
    rainfall_scaled = scaler.transform(rainfall_df)
    
    # Dự đoán
    prediction = model.predict(rainfall_scaled)[0]
    probability = model.predict_proba(rainfall_scaled)[0][1]

    return jsonify({
        "rainfall_mm": rainfall_mm,
        "flood_prediction": bool(prediction),
        "flood_probability": round(probability, 2)
    })


if __name__ == "__main__":
    app.run(debug=True)
