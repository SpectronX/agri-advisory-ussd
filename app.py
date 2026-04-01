from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/ussd', methods=['POST'])
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

        response = f"END Registration successful!\nName: {name}\nRegion: {region}\nCrop: {crop}\nStage: {stage}\n\nYou will receive SMS updates shortly. Thank you."

    else:
        response = "END Invalid input. Please try again."

    return Response(response, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
