from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

date_sistem = {
    "temperatura": 0.0,
    "nivel_apa": 0,
    "inundatie": "NU",
    "led_status": "Stins",
    "conexiune_arduino": "ONLINE - Conectat prin laptop",
    "ultimele_mesaje": [],      
    "ultimele_inundatii": []    
}

comanda_in_asteptare = None

PAGINA_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sistem Control IoT - Azure</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f9; text-align: center; margin: 0; padding: 20px; }
        .container { max-width: 600px; background: white; margin: 0 auto; padding: 20px; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); border-radius: 8px; }
        .card { background: #eef2f7; padding: 15px; margin: 10px 0; border-radius: 6px; font-size: 18px; }
        .status-bar { padding: 10px; font-weight: bold; border-radius: 4px; margin-bottom: 15px; background: #d4edda; color: #155724; }
        .btn { padding: 10px 25px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; border-radius: 4px; margin: 5px; text-transform: uppercase; }
        .btn-on { background: #28a745; color: white; }
        .btn-off { background: #dc3545; color: white; }
        .btn-send { background: #007bff; color: white; }
        input[type="text"] { width: 70%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; }
        .alert { background: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; font-weight: bold; }
        ul { text-align: left; background: #fff; padding: 10px 25px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Panou de Control IoT - Cloud Azure</h2>
        <hr>
        
        <div class="status-bar">
            Status Sistem: {{ date.conexiune_arduino }}
        </div>
        
        <div class="card">
            Temperatura Sistem: <strong>{{ date.temperatura }} °C</strong>
        </div>

        <div class="card {% if date.inundatie == 'DA' %} alert {% endif %}">
            Status Inundatie: <strong>{{ date.inundatie }}</strong> (Valoare senzor: {{ date.nivel_apa }})
        </div>

        <div class="card">
            Status Lumina: <strong>{{ date.led_status }}</strong>
            <br><br>
            <form action="/control-led" method="POST" style="display:inline;">
                <button name="comanda" value="A" class="btn btn-on">Aprinde LED</button>
            </form>
            <form action="/control-led" method="POST" style="display:inline;">
                <button name="comanda" value="S" class="btn btn-off">Stinge LED</button>
            </form>
        </div>

        <div class="card">
            Trimite mesaj catre Arduino (EEPROM):
            <br><br>
            <form action="/trimite-mesaj" method="POST">
                <input type="text" name="mesaj" placeholder="Scrie mesajul aici..." required maxlength="19">
                <button class="btn btn-send">Trimite</button>
            </form>
        </div>

        <h3>Ultimele 10 mesaje stocate (Cloud/EEPROM):</h3>
        <ul>
        {% for m in date.ultimele_mesaje %}
            <li>{{ m }}</li>
        {% else %}
            <li>Niciun mesaj trimis inca.</li>
        {% endfor %}
        </ul>

        <h3>Ultimele 10 evenimente de Inundatie:</h3>
        <ul>
        {% for i in date.ultimele_inundatii %}
            <li>{{ i }}</li>
        {% else %}
            <li>Niciun eveniment inregistrat.</li>
        {% endfor %}
        </ul>
    </div>
    <script>setTimeout(function(){ location.reload(); }, 3000);</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(PAGINA_HTML, date=date_sistem)

@app.route('/api/update', methods=['POST'])
def update_from_laptop():
    global date_sistem
    date_noi = request.json
    if date_noi:
        date_sistem.update(date_noi)
    return jsonify({"status": "ok"})

@app.route('/api/get-command', methods=['GET'])
def get_command():
    global comanda_in_asteptare
    cmd = comanda_in_asteptare
    comanda_in_asteptare = None
    return jsonify({"comanda": cmd})

@app.route('/control-led', methods=['POST'])
def control_led():
    global comanda_in_asteptare
    comanda_in_asteptare = request.form.get('comanda')
    return f"<script>window.location.href='/';</script>"

@app.route('/trimite-mesaj', methods=['POST'])
def trimite_mesaj():
    global comanda_in_asteptare
    mesaj = request.form.get('mesaj')
    if mesaj:
        date_sistem["ultimele_mesaje"].append(mesaj)
        if len(date_sistem["ultimele_mesaje"]) > 10:
            date_sistem["ultimele_mesaje"].pop(0)
        comanda_in_asteptare = f"MSG:{mesaj}"
    return f"<script>window.location.href='/';</script>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
