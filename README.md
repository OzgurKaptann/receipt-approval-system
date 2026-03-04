# Receipt Approval System

## 🇬🇧 English

### Overview

Receipt Approval System is a backend service designed to process bank transfer receipts through a controlled approval workflow.

The system allows uploaded payment receipts to be parsed, validated, and approved through a Telegram-based approval mechanism before further financial processing.

This project demonstrates a **production-style backend architecture** including authentication, database migrations, external API integration, and audit logging.

---

### System Workflow

Receipt Upload
→ OCR Parsing
→ Telegram Approval Request
→ Telegram Approval Webhook
→ Status Update
→ Audit Logging

---

### Features

* JWT Authentication
* Customer Management
* Receipt / Document Upload
* OCR Parsing (mock implementation)
* Telegram Approval Integration
* Webhook Callback Handling
* Full Audit Event Tracking
* Dockerized Development Environment

---

### Architecture

Backend Framework: **FastAPI**
Database: **PostgreSQL**
ORM: **SQLAlchemy**
Migration Tool: **Alembic**
Containerization: **Docker & Docker Compose**

---

### API Endpoints

Authentication

* `POST /auth/register`
* `POST /auth/login`

Customers

* `POST /customers`
* `GET /customers`

Documents

* `POST /documents/upload`

Telegram Integration

* `POST /telegram/webhook`

System

* `GET /health`

---

### Database Tables

**uploaded_documents**

Stores uploaded receipt metadata and OCR extracted data.

Fields include:

* sender_name
* amount_try
* transfer_date
* tg_chat_id
* tg_message_id
* status

---

**audit_events**

Stores a complete history of system actions for traceability.

Examples:

* DOCUMENT_UPLOADED
* OCR_PARSED
* TG_SENT
* TG_APPROVED
* TG_REJECTED

---

### Running the Project

Requirements

* Docker
* Docker Compose

Start services:

```
docker compose up -d --build
```

API will run at:

```
http://localhost:8000
```

Swagger documentation:

```
http://localhost:8000/docs
```

---

### Environment Variables

See `.env.example` for configuration.

Important variables:

```
DATABASE_URL
JWT_SECRET
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

---

### Example Approval Flow

1. Upload a bank receipt

2. OCR parser extracts:

   * sender name
   * transfer amount
   * transfer date

3. Telegram approval message is sent

4. Approval webhook updates document status

5. Audit event is recorded

---

### Project Status

Sprint-1 Completed

Implemented:

* Document upload
* OCR parsing (mock)
* Telegram approval integration
* Webhook callback processing
* Audit event tracking
* Dockerized backend

Next planned features (Sprint-2):

* Slack approval workflow
* TRY → USD FX conversion
* Deposit creation pipeline
* CRM / trading system integration

---

## 🇹🇷 Türkçe

### Proje Hakkında

Receipt Approval System, banka havale / EFT dekontlarını otomatik olarak işleyip bir onay sürecinden geçiren bir backend servisidir.

Yüklenen dekontlar OCR ile analiz edilir ve Telegram üzerinden onay sürecine gönderilir. Onay sonrası sistem doküman durumunu günceller ve tüm işlemleri audit log olarak kaydeder.

Bu proje aşağıdaki backend konularını göstermektedir:

* API geliştirme
* veritabanı modelleme
* migration yönetimi
* dış servis entegrasyonu
* audit logging
* docker tabanlı geliştirme ortamı

---

### Sistem Akışı

Dekont Yükleme
→ OCR Analizi
→ Telegram Onay Talebi
→ Telegram Webhook
→ Doküman Durumu Güncelleme
→ Audit Log Kaydı

---

### Özellikler

* JWT Authentication
* Müşteri yönetimi
* Dekont yükleme sistemi
* OCR veri çıkarımı (mock)
* Telegram bot entegrasyonu
* Webhook callback mekanizması
* Audit event takibi
* Docker ile container mimarisi

---

### Mimari

Backend Framework: **FastAPI**
Veritabanı: **PostgreSQL**
ORM: **SQLAlchemy**
Migration aracı: **Alembic**
Container: **Docker & Docker Compose**

---

### API Endpointleri

Authentication

* `POST /auth/register`
* `POST /auth/login`

Customers

* `POST /customers`
* `GET /customers`

Documents

* `POST /documents/upload`

Telegram

* `POST /telegram/webhook`

System

* `GET /health`

---

### Veritabanı Tabloları

**uploaded_documents**

Yüklenen dekont bilgilerini ve OCR ile çıkarılan verileri tutar.

Örnek alanlar:

* sender_name
* amount_try
* transfer_date
* tg_chat_id
* tg_message_id
* status

---

**audit_events**

Sistemde gerçekleşen tüm işlemlerin geçmişini tutar.

Örnek eventler:

* DOCUMENT_UPLOADED
* OCR_PARSED
* TG_SENT
* TG_APPROVED
* TG_REJECTED

---

### Projeyi Çalıştırma

Gereksinimler

* Docker
* Docker Compose

Servisleri başlatmak için:

```
docker compose up -d --build
```

API adresi:

```
http://localhost:8000
```

Swagger arayüzü:

```
http://localhost:8000/docs
```

---

### Ortam Değişkenleri

`.env.example` dosyasına bakınız.

Önemli değişkenler:

```
DATABASE_URL
JWT_SECRET
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

---

### Örnek Onay Süreci

1. Kullanıcı dekont yükler

2. OCR servisinden şu bilgiler çıkarılır:

   * gönderen kişi
   * transfer tutarı
   * transfer tarihi

3. Telegram grubuna onay mesajı gönderilir

4. Onay webhook üzerinden sisteme gelir

5. Doküman durumu güncellenir

6. Audit log kaydı oluşturulur

---

### Proje Durumu

Sprint-1 tamamlandı.

Tamamlanan özellikler:

✔ Dekont yükleme
✔ OCR parsing (mock)
✔ Telegram onay entegrasyonu
✔ Webhook callback işleme
✔ Audit log sistemi
✔ Docker tabanlı backend

Planlanan Sprint-2:

* Slack onay mekanizması
* TRY → USD dönüşüm servisi
* Deposit oluşturma pipeline
* CRM / trading sistemi entegrasyonu
