from flask import Flask, request, Response
import os
import json
from datetime import datetime
from urllib import request as urllib_request, parse as urllib_parse
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
AT_USERNAME = os.environ.get('AT_USERNAME')
AT_API_KEY = os.environ.get('AT_API_KEY')

def supabase_get(endpoint):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    req = urllib_request.Request(
        f'{SUPABASE_URL}/rest/v1/{endpoint}',
        headers=headers,
        method='GET'
    )
    try:
        with urllib_request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Supabase GET error: {e}")
        return []

def save_farmer(name, phone_number, region, crop, growth_stage):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    data = json.dumps({
        'name': name,
        'phone_number': phone_number,
        'region': region,
        'crop': crop,
        'growth_stage': growth_stage,
        'registered_at': datetime.utcnow().isoformat()
    }).encode('utf-8')

    req = urllib_request.Request(
        f'{SUPABASE_URL}/rest/v1/farmer_profiles',
        data=data,
        headers=headers,
        method='POST'
    )
    try:
        with urllib_request.urlopen(req) as response:
            return response.status
    except Exception as e:
        print(f"Supabase save error: {e}")
        return 500

def craft_sms(farmer, market_prices, input_rec):
    prompt = f"""
You are an agricultural advisor sending an SMS to a Ghanaian farmer.
Keep the message under 160 characters, plain language, actionable.

Farmer details:
- Name: {farmer['name']}
- Crop: {farmer['crop']}
- Region: {farmer['region']}
- Growth Stage: {farmer['growth_stage']}

Market price data:
{json.dumps(market_prices, indent=2)}

Input recommendation:
{json.dumps(input_rec, indent=2)}

Write a single SMS combining the most relevant market price insight
and input recommendation for this farmer. Be specific and helpful.
"""

    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    data = json.dumps({
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 1000,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode('utf-8')

    req = urllib_request.Request(
        'https://api.anthropic.com/v1/messages',
        data=data,
        headers=headers,
        method='POST'
    )
    try:
        with urllib_request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text']
    except Exception as e:
        print(f"Claude API error: {e}")
        return None

def send_sms(phone_number, message):
    data = urllib_parse.urlencode({
        'username': AT_USERNAME,
        'to': phone_number,
        'message': message,
    }).encode('utf-8')

    headers = {
        'apiKey': AT_API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    req = urllib_request.Request(
        'https://api.sandbox.africastalking.com/version1/messaging',
        data=data,
        headers=headers,
        method='POST'
    )
    try:
        with urllib_request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"SMS sent: {result}")
            return result
    except Exception as e:
        print(f"AT SMS error: {e}")
        return None

def scheduled_sms():
    print("Running scheduled SMS job...")
    farmers = supabase_get('farmer_profiles')
    for farmer in farmers:
        market_prices = supabase_get(
            f"market_prices?crop=eq.{farmer['crop']}&region=eq.{farmer['region']}"
        )
        input_rec = supabase_get(
            f"input_recommendations?crop=eq.{farmer['crop']}&growth_stage=eq.{farmer['growth_stage']}"
        )
        sms = craft_sms(farmer, market_prices, input_rec)
        if sms:
            send_sms(farmer['phone_number'], sms)
            print(f"Scheduled SMS sent to {farmer['name']}: {sms}")

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_sms, 'interval', minutes=2)
scheduler.start()

@app.route('/', methods=['POST'])
def ussd():
    phone_number = request.form.get('phoneNumber')
    text = request.form.get('text', '')

    inputs = text.split('*')
    level = len([i for i in inputs if i != ''])

    if text == '':
        response = "CON Welcome to AgriAdvisory\nYour agricultural advisory system.\n\nPlease enter your name:"

    elif level == 1:
        response = "CON Select your region:\n1. Ashanti\n2. Brong-Ahafo\n3. Northern Region"

    elif level == 2:
        response = "CON Select your crop:\n1. Maize\n2. Cocoa\n3. Tomato"

    elif level == 3:
        response = "CON Select your growth stage:\n1. Planting\n2. Growing\n3. Harvesting"

    elif level == 4:
        name = inputs[0]
        region_map = {'1': 'Ashanti', '2': 'Brong-Ahafo', '3': 'Northern Region'}
        crop_map = {'1': 'Maize', '2': 'Cocoa', '3': 'Tomato'}
        stage_map = {'1': 'Planting', '2': 'Growing', '3': 'Harvesting'}

        region = region_map.get(inputs[1], 'Unknown')
        crop = crop_map.get(inputs[2], 'Unknown')
        stage = stage_map.get(inputs[3], 'Unknown')

        farmer = {
            'name': name,
            'phone_number': phone_number,
            'region': region,
            'crop': crop,
            'growth_stage': stage
        }

        save_farmer(name, phone_number, region, crop, stage)

        market_prices = supabase_get(
            f'market_prices?crop=eq.{crop}&region=eq.{region}'
        )
        input_rec = supabase_get(
            f'input_recommendations?crop=eq.{crop}&growth_stage=eq.{stage}'
        )

        sms = craft_sms(farmer, market_prices, input_rec)
        if sms:
            send_sms(phone_number, sms)
            print(f"SMS sent to {phone_number}: {sms}")

        response = f"END Registration successful!\nName: {name}\nRegion: {region}\nCrop: {crop}\nStage: {stage}\n\nYou will receive SMS updates shortly. Thank you."

    else:
        response = "END Invalid input. Please try again."

    return Response(response, mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
