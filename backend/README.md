# NOMAC Project

Project description goes here 
## Setup Instructions

### Prerequisites
- Python 3.12
- Java 8+ (for Apache Spark)
- Django 5.2.4
- Django REST Framework 3.16.0
- PySpark 4.0.0
- Delta Spark 4.0.0

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nomac
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://localhost:8000`

[//]: # ()
[//]: # (## Project Structure)

[//]: # ()
[//]: # (```)

[//]: # (nomac/)

[//]: # (├── apps/core/           # Main Django application)

[//]: # (├── nomac/              # Django project settings)

[//]: # (├── requirements.txt    # Python dependencies)

[//]: # (└── manage.py          # Django management script)

[//]: # (```)

