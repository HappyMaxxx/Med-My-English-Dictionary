# Med - My English Dictionary  

**Med** is a web application designed to help users learn English more effectively. It allows users to create personalized dictionaries, group words by categories, and even connect with friends who are also learning English.

---

## Features  

- **Create Your Dictionary:** Add and manage your own English words with meanings and examples.  
- **Group Words:** Organize words into categories or topics for better learning.  
- **Find Friends:** Connect with other users, share progress, and motivate each other.  
- **Interactive Learning:** Engage with tools and activities to enhance vocabulary retention.  

---

## Repository  

The source code for the project is hosted on GitHub. Clone the repository to start:  
[Med - My English Dictionary](https://github.com/HappyMaxxx/Med-My-English-dictionary-)  

---

## Setup and Installation  

### 1. Clone the Repository  
Clone the repository to your local machine and save it under a specific name (e.g., `med`):  

```bash
git clone https://github.com/HappyMaxxx/Med-My-English-dictionary- med
cd med
```

### 2. Create a Virtual Environment  

Create and activate a Python virtual environment:  

```bash
python3 -m venv venv
source venv/bin/activate  # For Linux and macOS
# or
venv\Scripts\activate     # For Windows
```

### 3. Install Dependencies  

Install the required dependencies from `requirements.txt`:  

```bash
pip install -r requirements.txt
```

### 4. Set Up Docker and Redis  

This project uses Redis for caching or managing task queues.  

#### Install Docker  

Download and install Docker from the official website: [Docker](https://www.docker.com/).  

#### Run Redis with Docker  

Start the Redis container using Docker:  

```bash
docker run -d -p 6379:6379 redis
```

### 5. Run the Project  

Start the Django development server:  

```bash
python manage.py runserver
```

### Additional Commands  

#### Check if Redis is Running  

Ensure that the Redis container is up and running:  

```bash
docker ps
```

#### Stop Redis  

Stop and remove the Redis container if necessary:  

```bash
docker stop redis-server
docker rm redis-server
```

#### Deactivate Virtual Environment  

When finished, deactivate the virtual environment:  

```bash
deactivate
```

## Requirements  

- Python 3.8+  
- Docker  
- Redis  
- Django (check dependencies in `requirements.txt`)  

For more details or questions, feel free to contact the developer.
