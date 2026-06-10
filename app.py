import serial
import time
import threading
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)




PORT_SERIAL = 'COM6'
BAUD_RATE = 9600
EMAIL_TRIMITATOR = "ndeaconu03@gmail.com"
PAROLA_APLICATIE = "jftlrgptobwnmyii"
EMAIL_DESTINATAR = "ndeaconu03@gmail.com"


date_sistem = {
    "temperatura": 0.0,
    "nivel_apa": 0,
    "inundatie": "NU",
    "led_status": "Stins",
    "ultimele_mesaje": [],      
    "ultimele_inundatii": []    
}

arduino = None


def trimite_email_alerta():
    try:
        mesaj = MIMEText(" ALERTĂ INUNDAȚIE! Senzorul a detectat apă în sistem.")
        mesaj['Subject'] = ' ALERTĂ INUNDAȚIE - Sistem Azure IoT'
        mesaj['From'] = EMAIL_TRIMITATOR
        mesaj['To'] = EMAIL_DESTINATAR

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_TRIMITATOR, PAROLA_APLICATIE)
        server.sendmail(EMAIL_TRIMITATOR, EMAIL_DESTINATAR, mesaj.as_string())
        server.quit()
        print("[EMAIL] Alertă trimisă cu succes!")
    except Exception as e:
        print(f"[EMAIL EROARE] {e}")


def citeste_arduino():
    global arduino, date_sistem
    try:
        arduino = serial.Serial(PORT_SERIAL, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(" Conexiune cu Arduino stabilită cu succes în fundal!")
    except Exception as e:
        print(f" Eroare conectare Arduino: {e}")
        return

    while True:
        try:
            if arduino.in_waiting > 0:
                rand = arduino.readline().decode('utf-8').strip()
                if rand.startswith("DATA:"):
                    
                    parti = rand.replace("DATA: ", "").split("|")
                    temp = float(parti[0].split("=")[1])
                    apa = int(parti[1].split("=")[1])
                    inundatie = parti[2].split("=")[1]

                    date_sistem["temperatura"] = temp
                    date_sistem["nivel_apa"] = apa
                    
                    
                    if inundatie == "DA" and date_sistem["inundatie"] == "NU":
                        print("💦 Inundație detectată!")
                        trimite_email_alerta()
                        
                        date_sistem["ultimele_inundatii"].append(time.strftime("%Y-%m-%d %H:%M:%S") + f" (Nivel: {apa})")
                        if len(date_sistem["ultimele_inundatii"]) > 10:
                            date_sistem["ultimele_inundatii"].pop(0)

                    date_sistem["inundatie"] = inundatie
                
                elif rand.startswith("STATUS:"):
                    if "LED_Aprins" in rand:
                        date_sistem["led_status"] = "Aprins"
                    elif "LED_Stins" in rand:
                        date_sistem["led_status"] = "Stins"

        except Exception as e:
            print(f"Eroare buclă citire: {e}")
        time.sleep(0.1)

# ==========================================
# INTERFAȚA WEB (HTML + CSS direct în Python)
# ==========================================
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
        <h2> Panou de Control IoT - Cloud Azure</h2>
        <hr>
        
        <div class="card">
             Temperatură Sistem: <strong>{{ date.temperatura }} °C</strong>
        </div>

        <div class="card {% if date.inundatie == 'DA' %} alert {% endif %}">
             Status Inundație: <strong>{{ date.inundatie }}</strong> (Valoare senzor: {{ date.nivel_apa }})
        </div>

        <div class="card">
             Status Lumină: <strong>{{ date.led_status }}</strong>
            <br><br>
            <form action="/control-led" method="POST" style="display:inline;">
                <button name="comanda" value="A" class="btn btn-on">Aprinde LED</button>
            </form>
            <form action="/control-led" method="POST" style="display:inline;">
                <button name="comanda" value="S" class="btn btn-off">Stinge LED</button>
            </form>
        </div>

        <div class="card">
            ✉️ Trimite mesaj către Arduino (EEPROM):
            <br><br>
            <form action="/trimite-mesaj" method="POST">
                <input type="text" name="mesaj" placeholder="Scrie mesajul aici..." required maxlength="19">
                <button class="btn btn-send">Trimite</button>
            </form>
        </div>

        <h3> Ultimele 10 mesaje stocate (Cloud/EEPROM):</h3>
        <ul>
        {% for m in date.ultimele_mesaje %}
            <li>{{ m }}</li>
        {% else %}
            <li>Niciun mesaj trimis încă.</li>
        {% endfor %}
        </ul>

        <h3> Ultimele 10 evenimente de Inundație:</h3>
        <ul>
        {% for i in date.ultimele_inundatii %}
            <li>{{ i }}</li>
        {% else %}
            <li>Niciun eveniment înregistrat.</li>
        {% endfor %}
        </ul>
    </div>
    
    <script>
        // Auto-refresh la pagină la fiecare 4 secunde pentru a actualiza temperaturile live
        setTimeout(function(){ location.reload(); }, 4000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(PAGINA_HTML, date=date_sistem)

@app.route('/control-led', methods=['POST'])
def control_led():
    comanda = request.form.get('comanda')
    if arduino and comanda in ['A', 'S']:
        arduino.write(f"{comanda}\n".encode('utf-8'))
        time.sleep(0.5) # Așteptăm răspunsul de la Arduino
    return f"<script>window.location.href='/';</script>"

@app.route('/trimite-mesaj', methods=['POST'])
def trimite_mesaj():
    mesaj = request.form.get('mesaj')
    if arduino and mesaj:
        comanda_msg = f"MSG:{mesaj}\n"
        arduino.write(comanda_msg.encode('utf-8'))
        
        
        date_sistem["ultimele_mesaje"].append(mesaj)
        if len(date_sistem["ultimele_mesaje"]) > 10:
            date_sistem["ultimele_mesaje"].pop(0)
            
        time.sleep(0.5)
    return f"<script>window.location.href='/';</script>"

if __name__ == '__main__':
    # Pornim firul de execuție secundar pentru citirea Arduino-ului
    fir_fundal = threading.Thread(target=citeste_arduino, daemon=True)
    fir_fundal.start()
    
    try:
        # REPARAT: Schimbăm host în '127.0.0.1' (doar pt laptopul tău) și portul în 5001
        print("⏳ Se pornește serverul web Flask...")
        app.run(host='127.0.0.1', port=5001, debug=False)
    except Exception as e:
        print(f"❌ Serverul Flask a dat eroare la pornire: {e}")