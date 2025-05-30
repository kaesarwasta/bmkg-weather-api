from flask import Flask, jsonify, render_template, request, send_from_directory
import requests
import xml.etree.ElementTree as ET
from difflib import get_close_matches
import os

app = Flask(__name__)

PROVINCE_URLS = {
    "Jawa Barat": "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah_tingkat_iv}",
    "Jawa Tengah": "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah_tingkat_iv}",
    "Jawa Timur": "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah_tingkat_iv}",
    "DKI Jakarta": "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah_tingkat_iv}"
}

def get_client_city(ip):
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/")
        if res.status_code == 200:
            data = res.json()
            return data.get("city", None)
    except:
        pass
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/weather")
def get_weather():
    city = request.args.get("city")
    province = request.args.get("province", "Jawa Barat")

    if not city:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        city = get_client_city(ip)

    url = PROVINCE_URLS.get(province)
    if not url:
        return jsonify({"error": f"Province '{province}' not supported"}), 400

    response = requests.get(url)
    root = ET.fromstring(response.content)
    area_names = [a.attrib.get("description") for a in root.iter("area")]

    city_match = get_close_matches(city, area_names, n=1, cutoff=0.6)
    if not city_match:
        return jsonify({"error": f"City '{city}' not found in {province}."}), 404
    city = city_match[0]

    area = next((a for a in root.iter("area") if a.attrib.get("description") == city), None)
    weather = area.find(".//parameter[@id='weather']/timerange")
    temp = area.find(".//parameter[@id='t']/timerange/value")

    return jsonify({
        "location": city,
        "province": province,
        "weather": weather.find("value").text if weather is not None else "N/A",
        "datetime": weather.attrib.get("datetime") if weather is not None else "N/A",
        "temperature": temp.text if temp is not None else "N/A"
    })

@app.route('/manifest.json')
def manifest():
    return send_from_directory("static", "manifest.json")

@app.route('/sw.js')
def sw():
    return send_from_directory("static", "sw.js")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
