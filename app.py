from flask import Flask, request, Response
import os
import requests
from datetime import datetime

app = Flask(__name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

def save_farmer(name, phone_number, region, crop, growth_stage):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': name,
        'phone_number': phone_number,
        'region': region,
        'crop': crop,
        'growth_stage': growth_stage,
        'registered_at': datetime.utcnow().isoformat()
    }
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/farmer_profiles',
        headers=headers,
        json=data
    )
    return response.status_code

@app.route('/', methods=['POST'])
def ussd():
    session_id = request.form.get('sessionId')
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

        save_farmer(name, phone_number, region, crop, growth_stage=stage)

        response = f"END Registration successful!\nName: {name}\nRegion: {region}\nCrop: {crop}\nStage: {stage}\n\nYou will receive SMS updates shortly. Thank you."

    else:
        response = "END Invalid input. Please try again."

    return Response(response, mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

Also update `requirements.txt` to:
```
flask
srequests
