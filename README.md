# Event Management System

## 🚀 Features
- User Authentication and Authorization
- Event Creation and Management
- Ticket Booking System
- Admin Dashboard
- Image Upload
- Payment Integration

## 📋 Prerequisites
- Python 3.10+
- MySQL Server
- Git (optional)

## ⚙️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd event-final
```

### 2. Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```sql
CREATE DATABASE event_mang;
```

Update main.py database configuration:
```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'event_mang'
}
```

Initialize database:
```bash
mysql -u root -p event_mang < schema.sql
```

### 5. Directory Structure
```
event_final/
├── main.py
├── requirements.txt
├── schema.sql
├── static/
│   └── images/
│       └── events/
├── templates/
│   ├── admin/
│   ├── auth/
│   └── user/
└── .env
```

### 6. Environment Variables
Create `.env` file:
```env
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

### 7. Run Application
```bash
python main.py
```
Visit: `http://localhost:5000`

## 🔑 Default Credentials
### Admin Login
- URL: `/admin/login`
- Username: `admin`
- Password: `admin123`

## 💡 Usage

### For Users
1. Register new account `/register`
2. Browse available events
3. Book tickets
4. View bookings in dashboard

### For Admins
1. Create/Edit events
2. Manage tickets
3. View registrations
4. Monitor dashboard

## 📁 Project Structure
```
event_final/
├── main.py              # Application entry point
├── requirements.txt     # Dependencies
├── schema.sql          # Database schema
├── static/             # Static assets
│   └── images/
│       └── events/     # Event images
├── templates/          # HTML templates
│   ├── admin/         # Admin templates
│   ├── auth/          # Auth templates
│   └── user/          # User templates
└── .env               # Environment variables
```

## 🛡️ Security
- Passwords are hashed
- CSRF protection
- Secure file uploads
- SQL injection prevention

## 🤝 Contributing
1. Fork repository
2. Create feature branch
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit changes
   ```bash
   git commit -m 'Add AmazingFeature'
   ```
4. Push to branch
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open Pull Request

## 📝 License
This project is MIT licensed.

---
Made with using Flask and MySQL
