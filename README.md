# Raspi-SIM7600-Fire-IoT: Akıllı Yangın Tespit ve Bildirim Sistemi 🔥📡

Bu proje, **Raspberry Pi**, **SIM7600X 4G modülü** ve **YOLO tabanlı görüntü işleme** teknolojisini birleştirerek yangınları **gerçek zamanlı** olarak tespit eden ve **SMS, arama ve Firebase** üzerinden anında uyarılar gönderen **akıllı bir IoT yangın izleme sistemidir**.

---

## Proje Hakkında

Bu sistem özellikle **ormanlar, endüstriyel alanlar** ve **uzak bölgeler** gibi yerlerde erken yangın tespiti ve müdahale sağlamak amacıyla tasarlanmıştır.

### 🔧 Kullanılan Temel Bileşenler

- **Raspberry Pi** – Ana işlem birimi  
- **Arducam 64MP Kamera** – Yüksek çözünürlüklü görüntüleme  
- **SIM7600X Modülü** – Hücresel iletişim (SMS, arama) ve GPS  
- **YOLO Nesne Algılama** – Yangınları yüksek doğrulukla tespit  
- **Firebase Realtime Database** – Bulut temelli durum izleme ve veri günlüğü  

---

## Özellikler

### Tespit & Uyarılar

- **Gerçek Zamanlı Yangın Tespiti** – YOLO ile anlık kare analizi  
- **3 Seviyeli Güvenilirlik Sınıflandırması**  
  - `ALARM` – Yüksek doğruluk  
  - `DIKKAT` – Orta seviye  
  - `AZ_ONEMLI` – Düşük seviye  
- **Kümülatif Alarm Sistemi** – Belirli eşik üstü tespit sayısında ana alarm tetiklenir  
- **SMS Bildirimi** – Kritik eşikte SMS gönderimi  
- **Sesli Arama** – En yüksek eşik durumunda otomatik arama başlatma  

### Veri Yönetimi

- **Görüntü Kayıtları** – Tespit edilen kareler klasörlerde saklanır  
- **Firebase Güncellemesi** – Anlık olay verileri ve sistem durumu  
- **GPS Konum Bilgisi** – Tespitlerle eş zamanlı koordinat paylaşımı  

### ⚙️ Donanım Yönetimi

- **SIM7600 Güç Kontrolü** – GPIO ile güvenli açma/kapama  
- **GPIO Tabanlı Etkileşim** – Raspberry Pi ile modül arası kontrol  

---

## 🛠️ Gereksinimler

### 📦 Donanım

| Bileşen | Açıklama |
|--------|----------|
| Raspberry Pi | 3B+ veya 4 (tercihen 64-bit) |
| **Arducam 64MP Kamera Modülü** | Raspberry Pi ile uyumlu yüksek çözünürlüklü kamera (CSI arayüzlü) |
| SIM7600X | Waveshare 4G/LTE modülü |
| Güç Kaynağı | 5V 3A (kaliteli kabloyla) |
| Antenler | 4G + GPS |
| SIM Kart | Aktif, SMS ve arama özellikli |

> 📷 **Arducam Hawk-eye 64MP** modeli kullanılmıştır. Bu kamera, düşük ışık koşullarında dahi net görüntü sunarak yangın tespiti için daha hassas veri sağlar. CSI arayüzü üzerinden Raspberry Pi ile doğrudan bağlantı kurulur ve `libcamera` altyapısıyla uyumludur.

### 💾 Yazılım

- **Raspberry Pi OS (64-bit)**
- **Python 3.9+**
- Gerekli Paketler:
  ```bash
  sudo apt install -y libcamera-tools git screen python3-venv

# 🔥 Raspi-SIM7600-Fire-IoT

Raspberry Pi, SIM7600 4G modülü ve YOLO görüntü işleme teknolojisini kullanarak **gerçek zamanlı yangın tespiti**, **SMS/arama bildirimi** ve **Firebase entegrasyonu** sağlayan akıllı sistemdir.

---

## 🚀 Kurulum

### 1. Raspberry Pi Hazırlığı

```bash
sudo apt update
sudo apt full-upgrade -y
```

### 2. Kamera ve Seri Port Ayarları

```bash
sudo raspi-config
```

- Arayüz Seçenekleri > Kamera > **Etkinleştir**  
- Arayüz Seçenekleri > Seri Port > **Oturum açmayı kapat / Donanım portunu aç**

### 3. Kullanıcıyı `dialout` grubuna ekleyin

```bash
sudo adduser $USER dialout
```

🔁 **Raspberry Pi’yi yeniden başlatın**

### 4. (İsteğe Bağlı) ModemManager'ı devre dışı bırakın

```bash
sudo systemctl stop ModemManager
sudo systemctl disable ModemManager
```

---

## 📁 Proje Kurulumu

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/your-username/Raspi-SIM7600-Fire-IoT.git
cd Raspi-SIM7600-Fire-IoT
```

### 2. Sanal Ortam ve Gerekli Kütüphaneler

```bash
python3 -m venv venv
source venv/bin/activate
pip install opencv-python ultralytics numpy requests pyserial RPi.GPIO
```

### 3. YOLO Modeli

`best.pt` model dosyasını proje kök dizinine yerleştirin.

---

## 🔥 Firebase Entegrasyonu

1. Firebase Console üzerinden yeni proje oluşturun.  
2. **Build > Realtime Database** menüsünden veritabanı oluşturun.  
3. Veritabanı URL’sini kopyalayın:

```text
https://your-project-id-default-rtdb.firebaseio.com
```

---

## 🔌 Donanım Bağlantısı

| SIM7600X Pini | Raspberry Pi GPIO |
|---------------|-------------------|
| TX            | GPIO15 (RXD)      |
| RX            | GPIO14 (TXD)      |
| GND           | GND               |
| PWRKEY        | GPIO6             |

---

## ⚙️ Konfigürasyon

`main.py` dosyasında ayarları şu şekilde yapılandırın:

```python
CONFIG = {
    "phone_number": "+905051234567",
    "sms_message": "UYARI: Yuksek dogrulukta yangin tespit edildi!",
    "pin_code": "1234",
    "call_threshold": 0.80,
    "sms_threshold": 0.70
}

FIREBASE_URL = "https://your-project-id-default-rtdb.firebaseio.com/veri"
GPS_PORT = '/dev/ttyS0'
GPS_BAUDRATE = 115200
```

---

## 🧪 Kullanım

```bash
source venv/bin/activate
python3 main.py
```

- YOLO ile görüntü analizi yapılır  
- Tespit edilen görüntüler `./Output` klasörüne kaydedilir  
- Firebase'e sistem durumu ve tespit verisi gönderilir  
- Belirli eşiklerde SMS ve arama tetiklenir

---

## 📷 Kamera & YOLO İşleme

- Arducam 64MP kamera kullanılır
- libcamera ile uyumludur
- Her kare YOLO modeline gönderilir:

```python
import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    # işleme devam
```

📌 Bazı Arducam modelleri özel libcamera sürücüleri gerektirir. Gerekirse [Arducam Resmi Sitesi](https://www.arducam.com) üzerinden uygun sürücüyü kurun.

---

## 🗂️ Ekran Çıktısı Yapısı

```
./Output/
├── ALARM/
│   └── YANGIN_ALARM_20250727_163000_0.95.jpg
├── DIKKAT/
│   └── DIKKAT_EDILMELI_20250727_163100_0.40.jpg
└── AZ_ONEMLI/
    └── AZ_ONEMLI_20250727_163200_0.15.jpg
```

---

## ☁️ Firebase Veri Yapısı

```json
veri/
├── current_system_status/
│   ├── system_time
│   ├── last_processed_frame_confidence
│   ├── last_processed_frame_category
│   ├── fire_detected_in_last_frame
│   ├── gps: {latitude, longitude, timestamp}
│   ├── cumulative_fire_detections
│   └── fire_alert_triggered
├── fire_detections/
│   ├── -UniqueKey1/
│   │   ├── detection_time
│   │   ├── confidence
│   │   ├── category
│   │   └── gps
├── system_alerts/
│   ├── -UniqueKey2/
│   │   ├── alarm_time
│   │   ├── message
│   │   ├── final_confidence
│   │   └── gps
└── current_status/
    ├── system_alarm_status
    └── last_alarm_details
```

---

## 🧰 Sorun Giderme

### 🔌 Seri Port Hatası

- UART bağlantısını ve `raspi-config` ayarlarını kontrol edin  
- `dialout` grubuna eklendiğinizden emin olun

### 📷 Kamera Açılmıyor

```bash
sudo apt install libcamera-tools
```

### 📶 SIM7600 Ağa Bağlanmıyor

- SIM kartın aktif ve PIN kodunun doğru olduğundan emin olun  
- Anten bağlantısını ve sinyal seviyesini kontrol edin

### 📡 GPS Verisi Alınamıyor

- Açık alanda olun (ilk sinyal birkaç dakika sürebilir)  
- GPS’i AT komutuyla etkinleştirin:

```bash
AT+CGPS=1,1
```
