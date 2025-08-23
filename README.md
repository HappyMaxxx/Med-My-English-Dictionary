# Med - My English Dictionary 📖

<p align="center">
  <img src="src/img/logo.svg" alt="Med Logo" />
</p>

<p align="center">
  <a href="https://ko-fi.com/v1mer" target="_blank">
    <img src="https://img.shields.io/badge/Support-Ko--fi-FF5E5B?style=flat-square&logo=ko-fi&logoColor=white" alt="Support me on Ko-fi" />
  </a>
  <a href="mailto:mpatik2006@gmail.com">
    <img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=flat-square&logo=paypal&logoColor=white" alt="Donate via PayPal" />
  </a>
</p>

**Med – My English Dictionary** is a web application that helps users learn English more effectively.  
With Med you can create a personal dictionary, group words into categories, practice vocabulary, track your achievements, and connect with friends.  

---

## ✨ Features

- 📚 **Personal Dictionary** – Add and manage your own English words with meanings and examples.  
- 🗂️ **Word Groups** – Organize words into categories for better learning.  
- 🏆 **Achievements** – Earn badges and rewards for your progress.  
- 👥 **Friends** – Connect with other learners and stay motivated.  
- 🔔 **Notifications** – Get updates on your activity and friends.  
- ⭐ **Top Users** – Compete with others and climb the leaderboard.  
- 🎯 **Practice Mode** – Interactive exercises for vocabulary retention.  
- ⚡ **Asynchronous Tasks** – Celery + Redis for background processing.  
- 🐳 **Dockerized Setup** – Easy installation and consistent environment.  

---

## 📋 Prerequisites

Make sure you have installed:  

- [Docker](https://www.docker.com/get-started/)  
- [Docker Compose](https://docs.docker.com/compose/install/)  
- [Python 3.10+](https://www.python.org/downloads/) (optional, for manual Django setup)  
- [Git](https://git-scm.com/downloads)  

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone --depth=1 https://github.com/HappyMaxxx/Med-My-English-Dictionary.git med
cd med
```
> **Note**: The `--depth=1` flag performs a shallow clone, downloading only the latest commit to save time and space. If you need the full commit history later, run: 
> ```bash
> git fetch --unshallow
> ```

### 2. Configure Environment Variables

Create a `.env` file in the project root:  

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=web,localhost,127.0.0.1

POSTGRES_DB=app_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

EMAIL_HOST_USER=your-email-host-user
EMAIL_HOST_PASSWORD=your-email-host-password
DEFAULT_FROM_EMAIL=your-default-from-email
```

> **Note**:  
> - Generate a secure `DJANGO_SECRET_KEY` (e.g., using `python -c "import secrets; print(secrets.token_hex(32))"`).
> - Configure email credentials if you want notifications via email. [Django Documentation](https://docs.djangoproject.com/en/5.2/topics/email/).

### 3. Collect Static Files

Prepare static assets:  

```bash
python3 manage.py collectstatic # for Linux/macOS
# or
python manage.py collectstatic # for Windows
```

### 4. Build and Run with Docker

```bash
docker-compose up --build
```

> **Note**: On Linux, you may need `sudo` depending on your Docker setup. On Windows, use Docker Desktop and run the command in PowerShell or CMD.

The application will be available at: [http://localhost:8000](http://localhost:8000).

The Flower dashboard for monitoring Celery tasks will be available at: [http://localhost:5555](http://localhost:5555).

---

## 🛑 Stopping and Cleaning Up

### Stop the Containers

```bash
docker-compose down
```

### Remove Containers and Volumes

```bash
docker-compose down -v
```

⚠️ This will remove the PostgreSQL volume and delete all stored data.  

---

## 🐳 Docker Compose Configuration

The `docker-compose.yml` defines these services:  

- **web** – Django app, exposed on port `8000`  
- **db** – PostgreSQL database, port `5432`  
- **redis** – Redis cache and broker, port `6379`  
- **celery** – Celery worker for async tasks  
- **celery-beat** – Celery beat scheduler for periodic tasks  
- **flower** – Monitoring dashboard for Celery, port `5555`  

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - TZ=Europe/Kyiv
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app_db
    command: ["./wait-for-it.sh", "db:5432", "--", "python3", "manage.py", "runserver", "0.0.0.0:8000"]
    volumes:
      - ./media:/app/media

  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    environment:
      - TZ=Europe/Kyiv

  celery:
    build: .
    command: celery -A mad worker --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      - TZ=Europe/Kyiv
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app_db

  celery-beat:
    build: .
    command: celery -A mad beat --loglevel=info
    depends_on:
      - redis
      - db
      - web
    environment:
      - TZ=Europe/Kyiv
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app_db

  flower:
    image: mher/flower
    environment:
      - TZ=Europe/Kyiv
      - CELERY_BROKER_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  postgres_data:
```

---

## 🔧 Troubleshooting

- **Port conflicts**: Ensure ports 8000, 5432, 6379, and 5555 are free.  
- **Database issues**: Check your `.env` PostgreSQL credentials.  
- **Redis/Celery issues**: Verify Redis is running and Celery is configured with the correct broker URL.  
- **Docker permissions**: On Linux, add your user to the Docker group:  
  ```bash
  sudo usermod -aG docker $USER
  ```

---

## 🌐 Accessing from Local Network

To access **MED** or the Flower dashboard from another device on your local network:

1. Add your machine’s local IP (e.g., `192.168.1.6` or `192.168.0.120`) to `ALLOWED_HOSTS` in the `.env` file.
2. Ensure your firewall allows traffic on ports `8000` (Django) and `5555` (Flower).
3. Access the app via `http://<your-ip>:8000` or Flower via `http://<your-ip>:5555` from another device.

---

## 🙌 Support the Project

If you find Med helpful and want to support development:  

- 💖 Ko-fi: [https://ko-fi.com/v1mer](https://ko-fi.com/v1mer)  
- 📬 PayPal: mpatik2006@gmail.com  

Your support helps me dedicate more time to improving this project 🙏  

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.  

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.  

---

Happy learning with **Med – My English Dictionary**! 🚀  