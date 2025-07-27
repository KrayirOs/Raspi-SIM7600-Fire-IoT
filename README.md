# Raspi-SIM7600-Fire-IoT

An intelligent, Raspberry Pi and SIM7600X-based system that uses YOLO for fire detection, sending emergency notifications via SMS, calls, and Firebase.

<p align="center">
  <img src="https://via.placeholder.com/800x400?text=Sistem+Görüntüsü+veya+Mimarisi+Buraya" alt="Sistem Çalışma Görüntüsü veya Şeması">
  <br>
  <em>Projenizin bir fotoğrafını veya mimari şemasını buraya ekleyebilirsiniz.</em>
</p>

---

## İçindekiler

* [Proje Hakkında](#proje-hakkında)
* [Özellikler](#özellikler)
* [Gereksinimler](#gereksinimler)
    * [Donanım](#donanım)
    * [Yazılım ve Kütüphaneler](#yazılım-ve-kütüphaneler)
* [Kurulum](#kurulum)
    * [1. Raspberry Pi Hazırlığı](#1-raspberry-pi-hazırlığı)
    * [2. Proje Dosyalarını Çekme](#2-proje-dosyalarını-çekme)
    * [3. Python Bağımlılıklarını Yükleme](#3-python-bağımlılıklarını-yükleme)
    * [4. YOLO Modeli Yükleme](#4-yolo-modeli-yükleme)
    * [5. Firebase Realtime Database Kurulumu](#5-firebase-realtime-database-kurulumu)
    * [6. SIM7600X ve GPIO Bağlantıları](#6-sim7600x-ve-gpio-bağlantıları)
    * [7. Konfigürasyon Dosyasını Düzenleme](#7-konfigürasyon-dosyasını-düzenleme)
* [Kullanım](#kullanım)
    * [Arka Planda Çalıştırma (İsteğe Bağlı)](#arka-planda-çalıştırma-i̇steğe-bağlı)
* [Çıktı Yapısı](#çıktı-yapısı)
* [Ek Kaynaklar](#ek-kaynaklar)
* [Katkıda Bulunma](#katkıda-bulunma)
* [Lisans](#lisans)

---

## Proje Hakkında

Bu proje, **Raspberry Pi** üzerinde çalışan bir **YOLO (You Only Look Once)** modeli kullanarak canlı kamera akışından yangınları gerçek zamanlı olarak tespit eden, tespit durumuna göre görüntüleri kaydeden ve entegre bir **SIM7600X 4G Modülü** aracılığıyla **Firebase Realtime Database**'e veri gönderen, ayrıca belirli yangın eşiklerinde **SMS ve arama bildirimi** yapan akıllı bir yangın tespit ve acil durum bildirim sistemidir.

Amacımız, özellikle insan müdahalesinin zor veya tehlikeli olduğu alanlarda (örn. ormanlar, büyük depolar, kritik altyapılar) yangınları hızlıca belirleyerek erken uyarı ve hızlı müdahale imkanı sağlamaktır.

---

## Özellikler

* **Gerçek Zamanlı Yangın Tespiti:** Yüksek performanslı YOLO modeli ile kamera görüntülerinden yangın tespiti.
* **Akıllı Görüntü Kaydı:** Tespit edilen yangınların güvenirlik düzeyine göre (**Yüksek Alarm**, **Dikkat**, **Az Önemli**) farklı klasörlere otomatik olarak kaydedilmesi.
* **Kümülatif Alarm Sistemi:** Ardışık yüksek güvenilirlikli yangın tespitlerinde gerçek bir yangın alarmı tetiklenmesi ve sistemin bu durumda ek fotoğraflar kaydetmesi.
* **SIM7600X Modül Entegrasyonu:**
    * **SMS Bildirimi:** Belirlenen güvenilirlik eşiği aşıldığında önceden tanımlanmış numaraya SMS gönderme.
    * **Otomatik Arama:** Daha yüksek güvenilirlik eşiği aşıldığında tanımlı numarayı otomatik olarak arama.
    * **GPS Konum Takibi:** Yangın tespit edildiğinde veya sistem durumu güncellendiğinde Firebase'e anlık konum verisi gönderme.
* **Firebase Realtime Database Entegrasyonu:**
    * Sistem durumunun (en son tespit, güvenilirlik, GPS konumu vb.) anlık olarak güncellenmesi.
    * Yangın tespit olaylarının (zaman, güvenilirlik, kategori, GPS) ayrı bir liste olarak kaydedilmesi.
    * Kümülatif yangın alarmı tetiklendiğinde özel bildirim gönderimi.
* **GPIO Kontrolü:** SIM7600X modülünün donanımsal olarak açılıp kapatılması için Raspberry Pi **GPIO** pinlerinin kullanımı.
* **Esnek Konfigürasyon:** `CONFIG` sözlüğü aracılığıyla kamera çözünürlüğü, tespit eşikleri, dosya adlandırma kuralları ve iletişim bilgileri gibi parametrelerin kolayca ayarlanabilmesi.

---

## Gereksinimler

### Donanım

* **Raspberry Pi** (Tavsiye edilen: Raspberry Pi 3B+ veya daha yenisi)
* **Raspberry Pi Kamera Modülü** (CSI arayüzü)
* **Waveshare SIM7600X 4G DONGLE** veya benzeri SIM7600 serisi modül (UART/USB üzerinden bağlanabilen)
* **Aktif SIM Kart** (Arama ve SMS özelliği olan)
* **Güç Kaynağı** (Raspberry Pi ve SIM7600X için yeterli akımı sağlayacak)
* **Antenler** (SIM7600X için 4G/LTE ve GPS antenleri)

### Yazılım ve Kütüphaneler

* **Raspberry Pi OS** (64-bit Lite veya Desktop önerilir)
* **Python 3**
* **pip** (Python paket yöneticisi)
* **OpenCV** (`cv2`)
* **Ultralytics YOLO** (`ultralytics`)
* **NumPy** (`numpy`)
* **Requests** (`requests`)
* **PySerial** (`pyserial`)
* **RPi.GPIO** (`RPi.GPIO`)
* **libcamera-tools** (Özellikle `libcamera-still` komutu için)

---

## Kurulum

### 1. Raspberry Pi Hazırlığı

1.  **Raspberry Pi OS Kurulumu:** [Raspberry Pi Imager](https://www.raspberrypi.com/software/) kullanarak SD kartınıza en güncel Raspberry Pi OS'u (64-bit Lite veya Desktop) yazın.
2.  **Güncelleme:**
    ```bash
    sudo apt update
    sudo apt full-upgrade -y
    ```
3.  **Gerekli Araçları Kurulumu:**
    ```bash
    sudo apt install -y libcamera-tools git screen
    ```
4.  **Seri Port ve Kamera Etkinleştirme:**
    * `sudo raspi-config` komutunu çalıştırın.
    * **Interface Options** -> **P3 Camera** -> **Yes** seçeneğini etkinleştirin.
    * **Interface Options** -> **P6 Serial Port** -> **Login shell over serial NO** ve **Serial port hardware YES** seçeneğini etkinleştirin.
    * Değişiklikleri kaydedip Raspberry Pi'yi yeniden başlatın.
5.  **Kullanıcıyı `dialout` Grubuna Ekleme:** SIM7600X seri portuna erişim için kullanıcı izni:
    ```bash
    sudo adduser $USER dialout
    ```
    Bu komuttan sonra yeniden başlatmanız gerekebilir (`sudo reboot`).

### 2. Proje Dosyalarını Çekme

```bash
git clone [https://github.com/KULLANICI_ADINIZ/Raspi-SIM7600-Fire-IoT.git](https://github.com/KULLANICI_ADINIZ/Raspi-SIM7600-Fire-IoT.git)
cd Raspi-SIM7600-Fire-IoT
