from flask import Flask, render_template, jsonify, request, Response
import pandas as pd
import requests
from datetime import date
import numpy as np

app = Flask(__name__)

def fetch_nasa_power_data(lat, lon, start_year, end_year):
    """ Fetches all required variables in a single API call, now including humidity. """
    parameters = "T2M_MAX,PRECTOTCORR,WS10M_MAX,RH2M"
    start_str, end_str = f"{start_year}0101", f"{end_year}1231"
    api_url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parameters}&community=RE&longitude={lon}&latitude={lat}&start={start_str}&end={end_str}&format=JSON"
    try:
        response = requests.get(api_url, timeout=30); response.raise_for_status(); data = response.json()
        return data['properties']['parameter']
    except Exception as e:
        print(f"An error occurred during fetch: {e}")
        return None

def process_variable(all_data, var_name, target_day_of_year):
    """ Processes a single variable from the fetched dataset. """
    param_data = all_data.get(var_name, {})
    if not param_data: return None, None
    sorted_dates = sorted(param_data.keys())
    times = pd.to_datetime(sorted_dates, format='%Y%m%d')
    values = [param_data[d] for d in sorted_dates if param_data[d] != -999]
    valid_times = [t for t, v in zip(times, values) if v is not None]
    if not values: return None, None
    df = pd.DataFrame({'value': values}, index=valid_times)
    start_day, end_day = target_day_of_year - 3, target_day_of_year + 3
    target_week_data = df[df.index.dayofyear.isin(range(start_day, end_day + 1))]
    return df, target_week_data['value'].tolist()

def suggest_alternative_dates(full_dfs, activity, current_month):
    """ Suggests a better month for an activity if current conditions are poor. """
    full_df = pd.DataFrame({
        'T2M_MAX': full_dfs['T2M_MAX']['value'],
        'PRECTOTCORR': full_dfs['PRECTOTCORR']['value'],
        'WS10M_MAX': full_dfs['WS10M_MAX']['value'] * 3.6
    })
    ideal_conditions = {
        'hiking': {'temp': (10, 25), 'precip': 0.1}, 'picnic': {'temp': (15, 28), 'precip': 0.1, 'wind': 15},
        'beach': {'temp': (25, 35), 'precip': 0.2}, 'skiing': {'temp': (-10, 0)},
        'fishing': {'precip': 0.5, 'wind': 20}, 'stargazing': {'precip': 0.1}
    }
    criteria = ideal_conditions.get(activity)
    if not criteria: return ""
    monthly_scores = {}
    for month in range(1, 13):
        month_data = full_df[full_df.index.month == month]
        if month_data.empty: continue
        score = 0
        if 'temp' in criteria: score += month_data['T2M_MAX'].between(criteria['temp'][0], criteria['temp'][1]).mean()
        if 'precip' in criteria: score += (month_data['PRECTOTCORR'] < criteria['precip']).mean()
        if 'wind' in criteria: score += (month_data['WS10M_MAX'] < criteria['wind']).mean()
        monthly_scores[month] = score
    best_month = max(monthly_scores, key=monthly_scores.get)
    if best_month != current_month and monthly_scores.get(best_month, 0) > monthly_scores.get(current_month, 0) * 1.25:
        best_month_name = date(2001, best_month, 1).strftime('%B')
        return f"For better conditions, the data suggests planning your {activity} around {best_month_name}."
    return ""

def generate_recommendation(activity, probs):
    """ Generates a rich, personalized recommendation with emojis. """
    temp_p, precip_p, wind_p = probs['temperature'], probs['precipitation'], probs['wind']
    if activity == 'hiking':
        if precip_p > 30: return f"🌧️ Heads up, Captain! There's a high chance of rain. Trails could be muddy and slippery. Pack waterproof gear."
        if temp_p > 60: return f"🥵 Warning: Extreme heat likely. Plan to hike early, bring extra water, and watch for signs of heat exhaustion."
        if wind_p > 40: return f"🌬️ It might get blustery on exposed ridges. A good windbreaker is recommended."
        return f"✅ Looks like a great window for a hike! Conditions seem cool, dry, and calm. Enjoy the journey."
    elif activity == 'picnic':
        if precip_p > 25: return f"🌦️ Watch out! Showers are a real possibility. Maybe plan for a covered pavilion just in case."
        if wind_p > 50: return f"🌬️ Hold onto your napkins! It's likely to be very windy, which could make for a tricky picnic."
        if temp_p > 70: return f"🥵 It's going to be very hot. Find a shady spot and pack lots of cool drinks."
        return f"🧺 Excellent conditions for a picnic! Expect pleasant weather. Don't forget the snacks."
    elif activity == 'beach':
        if temp_p < 20: return f"🥶 It might be too chilly for a proper beach day. The water will definitely be cold!"
        if precip_p > 20: return f"☔ Rain could spoil the fun and there's nowhere to hide. Check the short-term forecast before you go."
        if wind_p > 50: return f"🌊 High winds can make for rough surf and blowing sand. Be careful, especially with small children."
        return f"☀️ Looks perfect! Hot and dry conditions are historically likely. Don't forget the sunscreen!"
    elif activity == 'fishing':
        if wind_p > 60: return f"💨 Strong winds can make casting difficult and create choppy water. Be cautious."
        if precip_p > 50: return f"⛈️ Heavy downpours are a significant possibility. Stay safe and watch for lightning."
        return f"🎣 Conditions look favorable. Fish on!"
    elif activity == 'stargazing':
        if precip_p > 25: return f"☁️ Cloudy skies are likely with this chance of precipitation, which will block the stars. "
        return f"🔭 Clear skies are historically likely for this period. A great time to look up at the cosmos!"
    elif activity == 'skiing':
        if temp_p > 30: return f" slush alert! Temperatures are historically warm, which could mean poor snow quality."
        return f"❄️ Cold temperatures are likely, which is great for snow quality. Dress in layers!"
    return "Analyze the data to see if it's a good day for your activity!"

def calculate_comfort_index(avg_temp, avg_humidity):
    """ Calculates a robust comfort index where the score and label are directly linked. """
    raw_feels_like = avg_temp - 0.55 * (1 - (avg_humidity / 100)) * (avg_temp - 14)
    comfort_score = max(0, 100 - 3.5 * abs(raw_feels_like - 22))
    if comfort_score > 85: label = "Excellent"
    elif comfort_score > 70: label = "Comfortable"
    elif comfort_score > 50: label = "Tolerable"
    else: label = "Uncomfortable"
    return f"{int(comfort_score)}/100", label

@app.route('/')
def index(): return render_template('index.html')

@app.route('/get_weather_stats')
def get_weather_stats():
    lat, lon, activity, month, day = (request.args.get(k) for k in ['lat', 'lon', 'activity', 'month', 'day'])
    month, day = int(month), int(day)
    target_date = date(2001, month, day); target_day_of_year = target_date.timetuple().tm_yday

    all_data = fetch_nasa_power_data(float(lat), float(lon), 1994, 2023)
    if not all_data: return jsonify(None)

    results = {}; variables = {"temperature": "T2M_MAX", "precipitation": "PRECTOTCORR", "wind": "WS10M_MAX"}
    thresholds = {"temperature": 30.0, "precipitation": 1.0, "wind": 25.0}
    probabilities = {}; full_dfs = {}

    for var, var_name in variables.items():
        full_df, week_values = process_variable(all_data, var_name, target_day_of_year)
        if week_values is None: 
            probabilities[var] = 0
            continue
        full_dfs[var_name] = full_df
        if var == 'wind': week_values = [v * 3.6 for v in week_values]
        days_above = sum(1 for v in week_values if v > thresholds[var])
        probabilities[var] = (days_above / len(week_values)) * 100 if week_values else 0
        if var == 'temperature':
            yearly_probs = {}
            for year in range(full_df.index.year.min(), full_df.index.year.max() + 1):
                year_data = full_df[full_df.index.year == year]
                week_data = year_data[year_data.index.dayofyear.isin(range(target_day_of_year - 3, target_day_of_year + 3))]
                if not week_data.empty:
                    days_above_year = (week_data['value'] > thresholds['temperature']).sum()
                    yearly_probs[year] = (days_above_year / len(week_data)) * 100
            results['trend_data'] = yearly_probs

    _, temp_week_values = process_variable(all_data, 'T2M_MAX', target_day_of_year)
    _, humidity_week_values = process_variable(all_data, 'RH2M', target_day_of_year)
    if temp_week_values and humidity_week_values:
        avg_temp = np.mean(temp_week_values); avg_humidity = np.mean(humidity_week_values)
        score, label = calculate_comfort_index(avg_temp, avg_humidity)
        results['comfort_index'] = {'score': score, 'label': label}

    is_bad_weather = (activity in ['hiking', 'picnic', 'beach'] and (probabilities['precipitation'] > 30 or probabilities['temperature'] > 60)) or (activity == 'skiing' and probabilities['temperature'] > 30)
    suggestion = suggest_alternative_dates(full_dfs, activity, month) if is_bad_weather else ""
    recommendation = generate_recommendation(activity, probabilities)
    
    results.update({'probabilities': probabilities, 'recommendation': recommendation, 'suggestion': suggestion, 'date_str': target_date.strftime('%B %d')})
    return jsonify(results)

@app.route('/download')
def download_data():
    lat, lon = (request.args.get(k) for k in ['lat', 'lon'])
    all_data = fetch_nasa_power_data(float(lat), float(lon), 1994, 2023)
    if not all_data: return "Could not retrieve data.", 404
    df = pd.DataFrame({
        'date': pd.to_datetime(sorted(all_data['T2M_MAX'].keys()), format='%Y%m%d'),
        'max_temp_C': [v for k, v in sorted(all_data['T2M_MAX'].items()) if v != -999],
        'precipitation_mm': [v for k, v in sorted(all_data['PRECTOTCORR'].items()) if v != -999],
        'max_wind_speed_m_s': [v for k, v in sorted(all_data['WS10M_MAX'].items()) if v != -999],
        'relative_humidity_percent': [v for k, v in sorted(all_data['RH2M'].items()) if v != -999],
    }).dropna()
    csv_data = df.to_csv(index=False)
    return Response(csv_data, mimetype="text/csv", headers={"Content-disposition": f"attachment; filename=nasa_climate_data_{lat}_{lon}.csv"})

if __name__ == '__main__': app.run(debug=True)