import cv2
import os
import time
from ultralytics import YOLO
import sys
import subprocess
import numpy as np
import requests
import json
import random
from datetime import datetime
import serial
import RPi.GPIO as GPIO


# --- CONFIGURASYON AYARLARI ---
CONFIG = {
    "camera_width": 640,
    "camera_height": 480,
    "detection_count_threshold": 50,      # Yangın ilan etmek için kümülatif yüksek doğruluklu tespit sayısı
    "output_base_folder": "./Output",     # Tüm çıktıların kaydedileceği ana klasör
    "photo_capture_delay_seconds": 1,      # Her fotoğraf çekimi arasındaki gecikme (saniye)
    "fire_alert_filename_prefix": "YANGIN_ALARM", # Yangın alarmı verildiğinde kaydedilen fotoğrafların öneki
    "buffer_max_size": 100,               # Bellekte tutulacak maksimum tespit edilmiş kare sayısı

    # Güvenirlik Eşikleri ve İlgili Klasörler/Önekler
    "confidence_levels": [
        {"threshold": 0.50, "folder": "ALARM", "prefix": "YANGIN_ALARM", "firebase_tag": "fire_alarm_high"}, # %50 ve üzeri
        {"threshold": 0.25, "folder": "DIKKAT", "prefix": "DIKKAT_EDILMELI", "firebase_tag": "fire_attention"}, # %25 - %50 arası
        {"threshold": 0.10, "folder": "AZ_ONEMLI", "prefix": "AZ_ONEMLI", "firebase_tag": "fire_low_importance"} # %10 - %25 arası
    ],

    # --- İletişim Ayarları ---
    "phone_number": os.getenv("PHONE_NUMBER", "+901234567"),
    "sms_message": "UYARI: Yuksek dogrulukta yangin tespit edildi! Konum bilgisi Firebase'de.",
    "pin_code": os.getenv("SIM_PIN", ""),
    "call_threshold": 0.80,         # Arama tetiklemek için güvenirlik eşiği
    "sms_threshold": 0.70           # SMS tetiklemek için güvenirlik eşiği
}
# ------------------------------

# --- Firebase ve GPS Ayarları ---
FIREBASE_URL = os.getenv("FIREBASE_RTDB_URL", "https://your-project-id-default-rtdb.firebaseio.com/veri")
GPS_PORT = '/dev/ttyS0'
GPS_BAUDRATE = 115200
ser = None # Global seri port objesi
power_key = 6 # SIM7600X güç anahtarı GPIO pini

# --- YOLO Modeli Yükle ---
model = YOLO("best.pt")

# --- Ortak Fonksiyonlar ---
def setup_directories():
    """Gerekli 'Output' ve alt klasörlerini oluşturur."""
    base_folder = CONFIG["output_base_folder"]
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
        print(f"'{base_folder}' klasörü oluşturuldu.")
    else:
        print(f"'{base_folder}' klasörü zaten mevcut.")

    for level in CONFIG["confidence_levels"]:
        folder_path = os.path.join(base_folder, level["folder"])
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"'{folder_path}' klasörü oluşturuldu.")
        else:
            print(f"'{folder_path}' klasörü zaten mevcut.")

def capture_photo_to_memory(width, height):
    """
    libcamera-still komutunu kullanarak fotoğrafı doğrudan belleğe çeker.
    """
    command = [
        "libcamera-still",
        "-t", "1",
        "--nopreview",
        "--width", str(width),
        "--height", str(CONFIG["camera_height"]),
        "-o", "-"
    ]
    try:
        result = subprocess.run(command, capture_output=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Hata: Fotoğraf belleğe çekilemedi! Komut: {' '.join(e.cmd)}")
        print(f"Hata Kodu: {e.returncode}")
        print(f"Standart Çıkış: {e.stdout.decode(errors='ignore')}")
        print(f"Hata Çıkışı: {e.stderr.decode(errors='ignore')}")
        return None
    except FileNotFoundError:
        print("Hata: 'libcamera-still' komutu bulunamadı. Lütfen yüklü olduğundan emin olun.")
        print("Komut: sudo apt install libcamera-tools")
        return None

def send_to_firebase(path, data):
    """
    Belirtilen yola JSON verisi gönderir (PUT metodu ile).
    PUT, belirtilen yoldaki veriyi tamamen değiştirir.
    path parametresi FIREBASE_URL'den sonraki yolu temsil eder.
    Örn: FIREBASE_URL = "...", path = "current_system_status"
    """
    full_url = f"{FIREBASE_URL}/{path}.json"
    try:
        response = requests.put(full_url, json=data)
        response.raise_for_status()
        # print(f"Firebase'e PUT ile veri gönderildi: {path}")
    except requests.exceptions.RequestException as e:
        print(f"Firebase PUT veri gönderme hatası: {e}")
    except Exception as e:
        print(f"Firebase PUT sırasında beklenmedik bir hata oluştu: {e}")

def push_to_firebase(path, data):
    """
    Belirtilen yola yeni bir veri girişi ekler (POST metodu ile).
    POST, Firebase'de otomatik olarak benzersiz bir anahtar oluşturur.
    path parametresi FIREBASE_URL'den sonraki yolu temsil eder.
    Örn: FIREBASE_URL = "...", path = "fire_detections"
    """
    full_url = f"{FIREBASE_URL}/{path}.json"
    try:
        response = requests.post(full_url, json=data)
        response.raise_for_status()
        print(f"Firebase'e POST ile yeni veri eklendi: {path}")
    except requests.exceptions.RequestException as e:
        print(f"Firebase POST veri gönderme hatası: {e}")
    except Exception as e:
        print(f"Firebase POST sırasında beklenmedik bir hata oluştu: {e}")

# --- SIM7600 İletişim Fonksiyonları ---
def send_at(command, expected_response, timeout):
    """
    SIM7600X modülüne AT komutu gönderir ve belirli bir yanıtı bekler.
    Başarılı olursa yanıtı döndürür, aksi takdirde None.
    """
    rec_buff = ''
    if ser is None or not ser.is_open:
        print(f"Seri port {GPS_PORT} açık değil, AT komutu gönderilemiyor.")
        return None

    try:
        print(f"Gönderiliyor AT: {command}")
        ser.write((command + '\r\n').encode())
        time.sleep(timeout)

        if ser.inWaiting():
            time.sleep(0.05)
            rec_buff = ser.read(ser.inWaiting())

        decoded_rec_buff = rec_buff.decode(errors='ignore')
        print(f"Yanıt: {decoded_rec_buff.strip()}")

        if expected_response not in decoded_rec_buff:
            print(f"HATA: '{command}' komutu için '{expected_response}' yanıtı alınamadı.")
            return None
        else:
            return decoded_rec_buff
    except serial.SerialException as e:
        print(f"Seri port hatası send_at içinde: {e}")
        return None
    except Exception as e:
        print(f"send_at sırasında beklenmedik hata: {e}")
        return None

def parse_cgpsinfo(cgpsinfo_str):
    """
    AT+CGPSINFO yanıtını ayrıştırır ve enlem, boylam, zamanı döndürür.
    """
    if not cgpsinfo_str or '+CGPSINFO:' not in cgpsinfo_str:
        return None, None, None

    parts = cgpsinfo_str.strip().split('+CGPSINFO: ')[1].split(',')
    
    if len(parts) < 9:
        print(f"GPS ayrıştırma hatası: Beklenenden az parça ({len(parts)}). Cümle: {cgpsinfo_str}")
        return None, None, None

    try:
        lat_raw = parts[0]
        lat_hemi = parts[1]
        latitude = None
        if lat_raw and lat_hemi:
            lat_deg = float(lat_raw[0:2])
            lat_min = float(lat_raw[2:])
            latitude = lat_deg + (lat_min / 60)
            if lat_hemi == 'S':
                latitude *= -1

        lon_raw = parts[2]
        lon_hemi = parts[3]
        longitude = None
        if lon_raw and lon_hemi:
            lon_deg = float(lon_raw[0:3])
            lon_min = float(lon_raw[3:])
            longitude = lon_deg + (lon_min / 60)
            if lon_hemi == 'W':
                longitude *= -1

        date_raw = parts[4]
        time_raw = parts[5]
        
        timestamp = None
        if date_raw and time_raw:
            try:
                year = int(date_raw[4:6]) + 2000
                month = int(date_raw[2:4])
                day = int(date_raw[0:2])
                hour = int(time_raw[0:2])
                minute = int(time_raw[2:4])
                second = int(time_raw[4:6].split('.')[0])
                
                timestamp = datetime(year, month, day, hour, minute, second).isoformat()
            except ValueError as ve:
                print(f"Tarih/Zaman dönüştürme hatası: {ve} - Date: '{date_raw}', Time: '{time_raw}'")
                timestamp = datetime.now().isoformat()
        else:
            timestamp = datetime.now().isoformat()

        return latitude, longitude, timestamp

    except ValueError as e:
        print(f"GPS ayrıştırma hatası (ValueError): {e} - Cümle: {cgpsinfo_str}")
        return None, None, None
    except IndexError as e:
        print(f"GPS ayrıştırma hatası (IndexError): {e} - Cümle: {cgpsinfo_str}")
        return None, None, None
    except Exception as e:
        print(f"GPS ayrıştırma sırasında beklenmedik hata: {e} - Cümle: {cgpsinfo_str}")
        return None, None, None

def get_gps_position_from_module():
    """
    SIM7600'den GPS konumunu alır (GPS'in zaten açık olduğu varsayılır).
    """
    max_attempts = 5 # GPS kilidi için deneme sayısı
    attempts = 0
    while attempts < max_attempts:
        response = send_at('AT+CGPSINFO','+CGPSINFO: ',1) # Sadece bilgi sorgula
        if response:
            if ',,,,,,' in response: # Henüz konum kilitlenmedi
                print('GPS konum kilitlenmesi bekleniyor...')
                time.sleep(1)
            else:
                latitude, longitude, timestamp = parse_cgpsinfo(response)
                if latitude is not None and longitude is not None:
                    print(f"GPS verisi alındı: Lat={latitude}, Lon={longitude}, Time={timestamp}")
                    return latitude, longitude, timestamp
        else:
            print('AT+CGPSINFO komutuna yanıt alınamadı.')
            
        attempts += 1
        time.sleep(1) # Denemeler arasında bekle

    print(f"GPS konum kilitlenemedi veya {max_attempts} denemede veri alınamadı.")
    # GPS'i burada kapatmıyoruz, main döngüsünde açık kalacak
    return None, None, None

def power_on(power_key_pin):
    """
    SIM7600X modülünü açar.
    """
    print('SIM7600X başlatılıyor...')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key_pin, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key_pin, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(power_key_pin, GPIO.LOW)
    time.sleep(20) # Modülün tam olarak açılması için bekleme süresi artırıldı
    if ser and ser.is_open:
        ser.flushInput()
    print('SIM7600X hazır.')
    time.sleep(5) # Dahili sistemlerin başlaması için ek bekleme

def power_down(power_key_pin):
    """
    SIM7600X modülünü kapatır.
    """
    print('SIM7600X kapatılıyor...')
    if GPIO.getmode() == GPIO.BCM:
        GPIO.output(power_key_pin, GPIO.HIGH)
        time.sleep(3)
        GPIO.output(power_key_pin, GPIO.LOW)
        time.sleep(18)
    print('SIM7600X kapandı.')

def make_call(number):
    """
    Belirtilen numarayı arar.
    """
    print(f"Arama yapılıyor: {number}")
    if send_at(f'ATD{number};', 'OK', 10):
        print("Arama başlatıldı. 20 saniye bekliyor...")
        time.sleep(20)
        print("Aramayı sonlandırılıyor...")
        if send_at('AT+CHUP', 'OK', 3):
            print('Arama başarıyla sonlandırıldı.')
            return True
        else:
            print('Arama sonlandırılamadı.')
            return False
    else:
        print('Arama başlatılamadı.')
        return False

def send_short_message(number, message):
    """
    Belirtilen numaraya kısa mesaj gönderir.
    """
    print("SMS modunu ayarlanıyor...")
    if not send_at("AT+CMGF=1", "OK", 1):
        print("SMS modu ayarlanamadı.")
        return False
    
    print("Kısa Mesaj Gönderiliyor...")
    if not send_at(f'AT+CMGS="{number}"', '>', 5):
        print('Mesaj gönderme başlatılamadı (AT+CMGS).')
        return False

    ser.write(message.encode())
    ser.write(b'\x1A') # CTRL+Z karakteri (mesaj sonu)
    time.sleep(1) # CTRL+Z sonrası bekleme

    # Modülün mesajı işleyip "OK" dönmesini bekle
    # Bu kısımda daha detaylı yanıt takibi için bir döngü eklenebilir
    response_after_sms = ''
    start_time = time.time()
    while time.time() - start_time < 20: # 20 saniye bekle
        if ser.inWaiting():
            time.sleep(0.1)
            response_after_sms += ser.read(ser.inWaiting()).decode('utf-8', errors='ignore')
            if "OK" in response_after_sms:
                print(f"SMS gönderim yanıtı (OK): {response_after_sms.strip()}")
                print('Mesaj başarıyla gönderildi.')
                return True
            elif "ERROR" in response_after_sms or "+CMS ERROR" in response_after_sms:
                print(f"SMS gönderim yanıtı (ERROR): {response_after_sms.strip()}")
                print('Mesaj gönderme hatası (modül raporu).')
                return False
        time.sleep(0.5) # Kısa bekleme
    
    print(f"SMS gönderim yanıtı (timeout): {response_after_sms.strip()}")
    print('Mesaj gönderme hatası (zaman aşımı veya OK alınamadı).')
    return False

# --- Ana Entegrasyon Logiği ---
def main():
    global ser # ser objesini global olarak kullan

    setup_directories()

    # Seri portu başlatma
    try:
        ser = serial.Serial(GPS_PORT, GPS_BAUDRATE, timeout=1)
        print(f"Seri port {GPS_PORT} başarıyla açıldı.")
    except serial.SerialException as e:
        print(f"HATA: Seri port açılamadı: {e}")
        print("Lütfen:")
        print(f"1. SIM7600 modülünüzün {GPS_PORT} portuna bağlı olduğundan emin olun.")
        print("2. Portun başka bir program tarafından kullanılmadığından emin olun (örn: minicom, ModemManager).")
        print("3. Kullanıcınızın seri porta erişim izinlerinin olduğundan emin olun (örn: `sudo adduser $USER dialout`).")
        print("4. Gerekirse Raspberry Pi'nin dahili seri port ayarlarını kontrol edin (`sudo raspi-config`).")
        sys.exit(1) # Hata durumunda betikten çık

    try:
        # SIM7600 modülünü aç
        power_on(power_key)

        # SIM PIN Kodu Girişi
        print("SIM PIN durumunu sorguluyor...")
        if not send_at('AT+CPIN?', 'READY', 5):
            print("SIM PIN girilmesi gerekiyor...")
            if CONFIG["pin_code"]:
                if not send_at(f'AT+CPIN="{CONFIG["pin_code"]}"', 'OK', 5):
                    print("HATA: PIN kodu girişi BAŞARISIZ oldu. Lütfen doğru PIN kodunu girdiğinizden emin olun.")
                    power_down(power_key)
                    sys.exit(1)
                print("PIN kodu başarıyla girildi.")
                time.sleep(2)
            else:
                print("HATA: PIN kodu 'pin_code' değişkenine girilmemiş veya çevre değişkeninden okunamadı. Lütfen kodu düzenleyin veya çevre değişkenini ayarlayın.")
                power_down(power_key)
                sys.exit(1)
        else:
            print("SIM zaten READY durumunda, PIN kodu girişi gerekli değil.")

        # Ağ Kaydını Kontrol Etme
        print("Ağ kaydı kontrol ediliyor...")
        max_wait_time = 60
        start_time = time.time()
        registered = False
        while time.time() - start_time < max_wait_time:
            # +CREG: 0,1 -> Kayıtlı (ana ağ)
            # +CREG: 0,5 -> Kayıtlı (dolaşım)
            if send_at('AT+CREG?', '+CREG: 0,1', 3) or send_at('AT+CREG?', '+CREG: 0,5', 3):
                print("SIM7600X ağa başarıyla kayıtlı.")
                registered = True
                break
            print("Ağ kaydı bekleniyor... Lütfen bekleyin.")
            time.sleep(5)
        
        if not registered:
            print("HATA: SIM7600X zaman aşımı içinde ağa kaydolamadı. Lütfen SIM kartı, anteni ve sinyal gücünü kontrol edin.")
            power_down(power_key)
            sys.exit(1)
        
        time.sleep(2)

        # GPS'i bir kez etkinleştir (ana döngüden önce)
        print("GPS modülü etkinleştiriliyor...")
        # AT+CGPS=1,1: GPS'i aç, konum bilgilerini sorgulanabilir yap
        if not send_at('AT+CGPS=1,1','OK',10): # Daha uzun timeout verilebilir
            print("HATA: GPS modülü etkinleştirilemedi. GPS fonksiyonları çalışmayabilir.")
            # GPS etkinleşmese bile diğer fonksiyonlara devam edebiliriz, ancak bu bir uyarıdır.
        else:
            print("GPS modülü başarıyla etkinleştirildi.")
            time.sleep(5) # GPS'in ilk kilitlenmesi için biraz daha bekle

        # Konfigürasyon değerlerini değişkene ata
        camera_width = CONFIG["camera_width"]
        camera_height = CONFIG["camera_height"]
        detection_count_threshold = CONFIG["detection_count_threshold"]
        output_base_folder = CONFIG["output_base_folder"]
        photo_capture_delay_seconds = CONFIG["photo_capture_delay_seconds"]
        fire_alert_filename_prefix = CONFIG["fire_alert_filename_prefix"]
        buffer_max_size = CONFIG["buffer_max_size"]
        # Güvenirlik seviyelerini büyükten küçüğe sırala (öncelik sırası için)
        confidence_levels = sorted(CONFIG["confidence_levels"], key=lambda x: x["threshold"], reverse=True)
        
        call_threshold = CONFIG["call_threshold"]
        sms_threshold = CONFIG["sms_threshold"]
        phone_number = CONFIG["phone_number"]
        sms_message = CONFIG["sms_message"]

        cumulative_fire_detections = 0
        fire_alert_triggered = False
        call_triggered_for_current_alert = False
        sms_triggered_for_current_alert = False
        detected_frames_buffer = []

        while not fire_alert_triggered:
            jpeg_bytes = capture_photo_to_memory(camera_width, camera_height)
            
            if jpeg_bytes is None:
                print("Belleğe fotoğraf çekme hatası nedeniyle program sonlandırılıyor.")
                break

            # Bellekten alınan JPEG baytlarını OpenCV görüntüsüne dönüştür
            frame = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if frame is None:
                print("Hata: Bellekteki fotoğraf verisi okunamadı veya çözülemedi.")
                time.sleep(photo_capture_delay_seconds)
                continue

            # YOLO modeli ile tespiti gerçekleştir
            results = model(frame, verbose=False)

            current_frame_has_high_confidence_fire = False
            frame_to_save = frame.copy() # Orijinal kareyi değiştirmeden kopyala
            highest_confidence_in_frame = 0.0

            fire_detected_this_frame = False
            detection_category = "no_detection"
            
            for r in results:
                # Tespit kutularını ve etiketleri görüntüye çiz
                frame_to_save = r.plot()

                for box in r.boxes:
                    confidence = box.conf.item()
                    highest_confidence_in_frame = max(highest_confidence_in_frame, confidence)
                    
                    if confidence > 0:
                        fire_detected_this_frame = True

                    # Güvenirlik seviyelerine göre kategoriyi belirle
                    for level in confidence_levels:
                        if confidence >= level["threshold"]:
                            detection_category = level["firebase_tag"]
                            # En yüksek alarm seviyesi için tampona kaydet
                            if level["threshold"] == confidence_levels[0]["threshold"]:
                                current_frame_has_high_confidence_fire = True
                                detected_frames_buffer.append(frame_to_save.copy())
                                if len(detected_frames_buffer) > buffer_max_size:
                                    detected_frames_buffer.pop(0) # Tampon dolarsa en eski kareyi çıkar
                            break # En yüksek eşiğe ulaştığında diğer seviyeleri kontrol etmeye gerek yok
                
                if current_frame_has_high_confidence_fire:
                    break # Yüksek güvenirlikli yangın tespit edildiğinde diğer sonuçlara bakmaya gerek yok

            # Loglama ve Sayaç Güncelleme
            if current_frame_has_high_confidence_fire:
                cumulative_fire_detections += 1
                print(f"[{time.strftime('%H:%M:%S')}] ALARM seviyesi tespit! Güvenirlik: {highest_confidence_in_frame:.2f} | Kümülatif tespit: {cumulative_fire_detections}/{detection_count_threshold}")
            elif fire_detected_this_frame:
                print(f"[{time.strftime('%H:%M:%S')}] Tespit var ({detection_category})! Güvenirlik: {highest_confidence_in_frame:.2f} | Kümülatif tespit: {cumulative_fire_detections}/{detection_count_threshold}")
                # Düşük seviye tespitlerde kümülatif sayacı sıfırlayabiliriz.
                # Bu mantık, yüksek güvenirlikli tespit olmadığında sayacı sıfırlıyor.
                cumulative_fire_detections = 0
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Tespit yok veya düşük seviye. Kümülatif tespit: {cumulative_fire_detections}/{detection_count_threshold}")
                cumulative_fire_detections = 0


            # Tespit edilen kareyi doğruluk oranına göre ilgili klasöre kaydet
            timestamp_file = time.strftime("%Y%m%d_%H%M%S")
            saved_to_folder = False

            for level in confidence_levels:
                if highest_confidence_in_frame >= level["threshold"]:
                    target_folder = os.path.join(output_base_folder, level["folder"])
                    filename = os.path.join(target_folder, f'{level["prefix"]}_{timestamp_file}_{highest_confidence_in_frame:.2f}.jpg')
                    cv2.imwrite(filename, frame_to_save)
                    saved_to_folder = True
                    break # En uygun klasöre kaydedince döngüden çık

            # --- Arama ve SMS Tetikleme Mantığı ---
            if fire_detected_this_frame:
                # Arama eşiği aşıldıysa ve daha önce tetiklenmediyse arama yap
                if highest_confidence_in_frame >= call_threshold and not call_triggered_for_current_alert:
                    print(f"Güvenirlik {highest_confidence_in_frame:.2f} >= Arama Eşiği {call_threshold}. Arama başlatılıyor...")
                    if make_call(phone_number):
                        call_triggered_for_current_alert = True
                
                # SMS eşiği aşıldıysa ve daha önce tetiklenmediyse SMS gönder
                if highest_confidence_in_frame >= sms_threshold and not sms_triggered_for_current_alert:
                    print(f"Güvenirlik {highest_confidence_in_frame:.2f} >= SMS Eşiği {sms_threshold}. SMS gönderiliyor...")
                    if send_short_message(phone_number, sms_message):
                        sms_triggered_for_current_alert = True
            else:
                # Yangın tespit edilmediğinde iletişim tetikleme bayraklarını sıfırla
                call_triggered_for_current_alert = False
                sms_triggered_for_current_alert = False


            # --- Firebase'e Veri Gönderimi (Her Karede Güncel Durum ve Yangın Tespitinde Olay Kaydı) ---
            latitude, longitude, gps_timestamp = get_gps_position_from_module()
            
            # Her karede güncel sistem durumunu Firebase'e gönder (PUT)
            # path'ler FIREBASE_URL'ye göre göreceli olmalı (örn. "current_system_status")
            current_system_status_data = {
                "system_time": datetime.now().isoformat(),
                "last_processed_frame_confidence": f"{highest_confidence_in_frame:.2f}",
                "last_processed_frame_category": detection_category,
                "fire_detected_in_last_frame": fire_detected_this_frame,
                "gps": {
                    "latitude": latitude if latitude is not None else "N/A",
                    "longitude": longitude if longitude is not None else "N/A",
                    "timestamp": gps_timestamp if gps_timestamp else datetime.now().isoformat()
                },
                "cumulative_fire_detections": cumulative_fire_detections,
                "fire_alert_triggered": fire_alert_triggered
            }
            send_to_firebase("current_system_status", current_system_status_data)
            print(f"Firebase'e güncel sistem durumu gönderildi (yangın tespit: {fire_detected_this_frame}).")


            if fire_detected_this_frame: # Sadece yangın tespit edildiğinde ayrıca bir olay kaydı ekle (POST)
                firebase_event_data = {
                    "detection_time": datetime.now().isoformat(),
                    "confidence": f"{highest_confidence_in_frame:.2f}",
                    "category": detection_category,
                    "gps": {
                        "latitude": latitude if latitude is not None else "N/A",
                        "longitude": longitude if longitude is not None else "N/A",
                        "timestamp": gps_timestamp if gps_timestamp else datetime.now().isoformat()
                    }
                }
                push_to_firebase("fire_detections", firebase_event_data)
                # Eğer ALARM seviyesindeyse en son alarm detayını da güncelleyebiliriz
                if current_frame_has_high_confidence_fire:
                    send_to_firebase("current_status/last_alarm_details", firebase_event_data)

            # Kümülatif ALARM eşiğine ulaşıldı mı?
            if cumulative_fire_detections >= detection_count_threshold and not fire_alert_triggered:
                print("\n" + "="*60)
                print("!!! KÜMÜLATİF YÜKSEK GÜVENİLİRLİKLİ YANGIN ALARMI TETİKLENDİ! SİSTEM DURDURULUYOR. !!!")
                print(f"'{len(detected_frames_buffer)}' adet ALARM seviyesi tespit kaydediliyor...")
                print("="*60 + "\n")
                
                fire_alert_triggered = True
                
                alert_output_folder = os.path.join(output_base_folder, confidence_levels[0]["folder"])
                
                for idx, buffered_frame in enumerate(detected_frames_buffer):
                    alert_photo_filename = os.path.join(alert_output_folder, f'{fire_alert_filename_prefix}_ALARM_ANIT_part{idx+1}_{timestamp_file}.jpg')
                    cv2.imwrite(alert_photo_filename, buffered_frame)
                    print(f"Alarm anı fotoğrafı '{alert_photo_filename}' kaydedildi.")
                
                # Alarm tetiklendiğinde Firebase'e özel bir durum gönder
                latitude, longitude, gps_timestamp = get_gps_position_from_module()
                alarm_data = {
                    "alarm_time": datetime.now().isoformat(),
                    "message": "CUMULATIVE HIGH CONFIDENCE FIRE ALERT TRIGGERED!",
                    "final_confidence": f"{highest_confidence_in_frame:.2f}",
                    "gps": {
                        "latitude": latitude if latitude is not None else "N/A",
                        "longitude": longitude if longitude is not None else "N/A",
                        "timestamp": gps_timestamp if gps_timestamp else datetime.now().isoformat()
                    }
                }
                push_to_firebase("system_alerts", alarm_data) # Yeni bir alarm kaydı olarak ekle
                send_to_firebase("current_status/system_alarm_status", {"status": "ACTIVE", "last_alarm_time": datetime.now().isoformat(), "triggered_by_confidence": f"{highest_confidence_in_frame:.2f}"})

                break # Ana döngüden çık
            
            # cv2.imshow("Anlik Yangin Tespit Sistemi", frame_to_save)
            # # 'q' tuşuna basıldığında döngüyü sonlandır
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     print("Kullanıcı 'q' tuşuna basarak sistemi durdurdu.")
            #     break
            
            time.sleep(photo_capture_delay_seconds)

    except KeyboardInterrupt:
        print("\nSistem kullanıcı tarafından durduruldu (Ctrl+C).")
    except Exception as e:
        print(f"Ana döngü sırasında beklenmeyen bir hata oluştu: {e}")
    finally:
        # cv2.imshow kullanılıyorsa, pencereleri kapat
        # cv2.destroyAllWindows() 
        print("İşlem tamamlandı.")
        if ser and ser.is_open:
            try:
                ser.close()
                print("Seri port kapatıldı.")
            except Exception as e:
                print(f"Seri port kapatılırken hata: {e}")
        try:
            power_down(power_key)
        except Exception as e:
            print(f"SIM7600X kapatılırken hata: {e}")
        try:
            GPIO.cleanup()
            print("GPIO temizlendi.")
        except Exception as e:
            print(f"GPIO temizlenirken hata: {e}")

if __name__ == "__main__":
    main()
