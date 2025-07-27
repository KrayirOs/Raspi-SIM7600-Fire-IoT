# Raspi-SIM7600-Fire-IoT
An intelligent, Raspberry Pi and SIM7600X-based system that uses YOLO for fire detection, sending emergency notifications via SMS, calls, and Firebase.

FireNet-IoT: Raspberry Pi & SIM7600X Destekli Yangın Tespit ve Acil Durum Sistemi

https://via.placeholder.com/600x300?text=Sistem+Görüntüsü+Buraya" alt="Sistem Çalışma Görüntüsü veya Şeması">


Projenizin bir fotoğrafını veya mimari şemasını buraya ekleyebilirsiniz.

Proje Hakkında
Bu proje, Raspberry Pi üzerinde çalışan bir YOLO (You Only Look Once) modeli kullanarak canlı kamera akışından yangınları gerçek zamanlı olarak tespit eden, tespit durumuna göre görüntüleri kaydeden ve entegre bir SIM7600X 4G Modülü aracılığıyla Firebase Realtime Database'e veri gönderen, ayrıca belirli yangın eşiklerinde SMS ve arama bildirimi yapan akıllı bir yangın tespit ve acil durum bildirim sistemidir.

Amacımız, özellikle insan müdahalesinin zor veya tehlikeli olduğu alanlarda (örn. ormanlar, büyük depolar, kritik altyapılar) yangınları hızlıca belirleyerek erken uyarı ve hızlı müdahale imkanı sağlamaktır.

Özellikler
Gerçek Zamanlı Yangın Tespiti: Yüksek performanslı YOLO modeli ile kamera görüntülerinden yangın tespiti.

Akıllı Görüntü Kaydı: Tespit edilen yangınların güvenirlik düzeyine göre (Yüksek Alarm, Dikkat, Az Önemli) farklı klasörlere otomatik olarak kaydedilmesi.

Kümülatif Alarm Sistemi: Ardışık yüksek güvenilirlikli yangın tespitlerinde gerçek bir yangın alarmı tetiklenmesi ve sistemin bu durumda ek fotoğraflar kaydetmesi.

SIM7600X Modül Entegrasyonu:

SMS Bildirimi: Belirlenen güvenilirlik eşiği aşıldığında önceden tanımlanmış numaraya SMS gönderme.

Otomatik Arama: Daha yüksek güvenilirlik eşiği aşıldığında tanımlı numarayı otomatik olarak arama.

GPS Konum Takibi: Yangın tespit edildiğinde veya sistem durumu güncellendiğinde Firebase'e anlık konum verisi gönderme.

Firebase Realtime Database Entegrasyonu:

Sistem durumunun (en son tespit, güvenilirlik, GPS konumu vb.) anlık olarak güncellenmesi.

Yangın tespit olaylarının (zaman, güvenilirlik, kategori, GPS) ayrı bir liste olarak kaydedilmesi.

Kümülatif yangın alarmı tetiklendiğinde özel bildirim gönderimi.

GPIO Kontrolü: SIM7600X modülünün donanımsal olarak açılıp kapatılması için Raspberry Pi GPIO pinlerinin kullanımı.

Esnek Konfigürasyon: CONFIG sözlüğü aracılığıyla kamera çözünürlüğü, tespit eşikleri, dosya adlandırma kuralları ve iletişim bilgileri gibi parametrelerin kolayca ayarlanabilmesi.

Gereksinimler
Donanım
Raspberry Pi (Tavsiye edilen: Raspberry Pi 3B+ veya daha yenisi)

Raspberry Pi Kamera Modülü (CSI arayüzü)

Waveshare SIM7600X 4G DONGLE veya benzeri SIM7600 serisi modül (UART/USB üzerinden bağlanabilen)

Aktif SIM Kart (Arama ve SMS özelliği olan)

Güç Kaynağı (Raspberry Pi ve SIM7600X için yeterli akımı sağlayacak)

Antenler (SIM7600X için 4G/LTE ve GPS antenleri)

Yazılım ve Kütüphaneler
Raspberry Pi OS (64-bit Lite veya Desktop önerilir)

Python 3

pip (Python paket yöneticisi)

OpenCV (cv2)

Ultralytics YOLO (ultralytics)

NumPy (numpy)

Requests (requests)

PySerial (pyserial)

RPi.GPIO (RPi.GPIO)

libcamera-tools (Özellikle libcamera-still komutu için)

Kurulum
1. Raspberry Pi Hazırlığı
Raspberry Pi OS Kurulumu: Raspberry Pi Imager kullanarak SD kartınıza en güncel Raspberry Pi OS'u (64-bit Lite veya Desktop) yazın.

Güncelleme:

Bash

sudo apt update
sudo apt full-upgrade -y
Gerekli Araçları Kurulumu:

Bash

sudo apt install -y libcamera-tools git screen
Seri Port ve Kamera Etkinleştirme:

sudo raspi-config komutunu çalıştırın.

Interface Options -> P3 Camera -> Yes seçeneğini etkinleştirin.

Interface Options -> P6 Serial Port -> Login shell over serial NO ve Serial port hardware YES seçeneğini etkinleştirin.

Değişiklikleri kaydedip Raspberry Pi'yi yeniden başlatın.

Kullanıcıyı dialout Grubuna Ekleme: SIM7600X seri portuna erişim için kullanıcı izni:

Bash

sudo adduser $USER dialout
Bu komuttan sonra yeniden başlatmanız gerekebilir (sudo reboot).

2. Proje Dosyalarını Çekme
Bash

git clone https://github.com/KULLANICI_ADINIZ/FireNet-IoT.git
cd FireNet-IoT
(Yukarıdaki KULLANICI_ADINIZ kısmını kendi GitHub kullanıcı adınızla değiştirmeyi unutmayın.)

3. Python Bağımlılıklarını Yükleme
Bash

pip install opencv-python ultralytics numpy requests pyserial RPi.GPIO
Not: RPi.GPIO sadece Raspberry Pi üzerinde çalışacaktır. Diğer sistemlerde bu kurulum adımında hata alabilirsiniz, bu normaldir.

4. YOLO Modeli Yükleme
Bu proje için önceden eğitilmiş best.pt adlı bir YOLO modeline ihtiyacınız var. Lütfen bu dosyayı projenin ana dizinine indirin. Kendi özel modelinizi eğittiyseniz, best.pt dosyasını bu dizine yerleştirin.

5. Firebase Realtime Database Kurulumu
Firebase Projesi Oluşturma:

Firebase Konsolu'na gidin: https://console.firebase.google.com/

Yeni bir proje oluşturun.

Realtime Database'i etkinleştirin ve güvenlik kurallarını (şimdilik test için) genel okuma/yazma izni verecek şekilde ayarlayabilirsiniz:

JSON

{
  "rules": {
    ".read": "true",
    ".write": "true"
  }
}
UYARI: Bu kurallar güvenlik açısından risklidir ve sadece test/geliştirme aşaması için uygundur. Canlı bir ortamda daha sıkı güvenlik kuralları tanımlamanız şiddetle tavsiye edilir.

FIREBASE_URL Güncelleme: Projenizdeki FIREBASE_URL değişkenini kendi Firebase Realtime Database URL'nizle güncelleyin:

Python

FIREBASE_URL = "https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/" # Kendi proje ID'nizle değiştirin
6. SIM7600X ve GPIO Bağlantıları
SIM7600X modülünü Raspberry Pi'ye bağlayın (genellikle USB veya UART üzerinden). Proje, UART bağlantısını ve belirli bir GPIO pinini (power_key = 6) modülün açma/kapama kontrolü için kullanır.

power_key: Modülünüzün güç anahtarı pinini Raspberry Pi GPIO pinine bağladığınızdan emin olun. Kodda bu pin 6 (BCM numaralandırması) olarak ayarlanmıştır. Donanım bağlantı şemanıza göre bunu değiştirmeniz gerekebilir.

GPS_PORT: Modülünüzün seri portunun Raspberry Pi üzerinde doğru şekilde göründüğünden emin olun. Çoğu durumda /dev/ttyS0 veya /dev/ttyUSB0 olabilir.

Python

GPS_PORT = '/dev/ttyS0' # Modülünüzün bağlandığı seri portu kontrol edin
7. Konfigürasyon Dosyasını Düzenleme
main.py dosyasının başındaki CONFIG sözlüğünü kendi ihtiyaçlarınıza göre güncelleyin:

Python

CONFIG = {
    "camera_width": 640,
    "camera_height": 480,
    "detection_count_threshold": 7,      # Yangın ilan etmek için kümülatif yüksek doğruluklu tespit sayısı
    "output_base_folder": "./Output",    # Tüm çıktıların kaydedileceği ana klasör
    "photo_capture_delay_seconds": 1,    # Her fotoğraf çekimi arasındaki gecikme (saniye)
    "fire_alert_filename_prefix": "YANGIN_ALARM", # Yangın alarmı verildiğinde kaydedilen fotoğrafların öneki
    "buffer_max_size": 100,              # Bellekte tutulacak maksimum tespit edilmiş kare sayısı

    "confidence_levels": [
        {"threshold": 0.50, "folder": "ALARM", "prefix": "YANGIN_ALARM", "firebase_tag": "fire_alarm_high"}, # %50 ve üzeri
        {"threshold": 0.25, "folder": "DIKKAT", "prefix": "DIKKAT_EDILMELI", "firebase_tag": "fire_attention"}, # %25 - %50 arası
        {"threshold": 0.10, "folder": "AZ_ONEMLI", "prefix": "AZ_ONEMLI", "firebase_tag": "fire_low_importance"} # %10 - %25 arası
    ],

    "phone_number": "+905051234567", # >>> BURAYI KENDİ TELEFON NUMARANIZLA DEĞİŞTİRİN (Uluslararası formatda: +ÜlkeKoduNumara) <<<
    "sms_message": "UYARI: Yuksek dogrulukta yangin tespit edildi! Konum bilgisi Firebase'de.",
    "pin_code": "1234",              # >>> BURAYI SIM KARTINIZIN PIN KODUYLA DEĞİŞTİRİN (Eğer PIN yoksa boş bırakın: "") <<<
    "call_threshold": 0.80,          # Arama tetiklemek için güvenirlik eşiği
    "sms_threshold": 0.70            # SMS tetiklemek için güvenirlik eşiği
}
Kullanım
Tüm kurulum adımlarını tamamladıktan sonra, projeyi başlatmak için ana dizinde aşağıdaki komutu çalıştırın:

Bash

python3 main.py
Sistem çalışmaya başladığında:

SIM7600X modülünü açacak ve ağa kaydolmasını bekleyecektir.

Gerekirse SIM PIN kodunu girecektir.

GPS modülünü etkinleştirecektir.

Kamera akışını işlemeye başlayacak, yangın tespiti yapacak ve çıktıları yönetecektir.

Yangın tespit durumuna göre Firebase'e veri gönderecek, SMS veya arama yapacaktır.

cv2.imshow penceresi yangın tespiti olan kareleri gösterecektir. q tuşuna basarak veya Ctrl+C ile sistemi durdurabilirsiniz.

Arka Planda Çalıştırma (İsteğe Bağlı)
Eğer sistemi arka planda çalıştırmak isterseniz screen komutunu kullanabilirsiniz:

Bash

screen -S fire_detection
python3 main.py
screen oturumundan ayrılmak için Ctrl+A ardından D tuşlarına basın. Geri dönmek için:

Bash

screen -r fire_detection
Çıktı Yapısı
Sistem, Output klasörü altında yangın tespitlerinin güvenilirlik seviyesine göre alt klasörler oluşturur:

Output/
├── ALARM/
│   ├── YANGIN_ALARM_20250727_161702_0.92.jpg
│   └── YANGIN_ALARM_ANIT_part1_20250727_161702.jpg
├── DIKKAT/
│   └── DIKKAT_EDILMELI_20250727_161705_0.35.jpg
└── AZ_ONEMLI/
    └── AZ_ONEMLI_20250727_161708_0.12.jpg
