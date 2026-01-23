P# Docker Development Setup Plan for Cellarium Backend

## Project Overview
- Django 5.2.3 application
- SQLite database
- REST framework and CORS headers enabled
- Wine management functionality

## Docker Setup Plan

### 1. Create Required Docker Files

#### A. Dockerfile
We'll create a Dockerfile that:
- Uses Python 3.11 as the base image
- Installs required dependencies
- Sets up the working directory
- Copies the project files
- Exposes the necessary port
- Defines the command to run the Django development server

#### B. requirements.txt
Since there's no requirements.txt file in the project yet, we'll create one that includes:
- Django 5.2.3
- Django REST framework
- django-cors-headers
- Any other dependencies needed

#### C. docker-compose.yml (Optional)
For simplicity, we can create a docker-compose.yml file to make it easier to:
- Run the Django application
- Mount volumes for live code changes
- Set environment variables
- Define port mappings

### 2. Docker Configuration Details

#### Dockerfile Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

#### requirements.txt Content
```
Django==5.2.3
djangorestframework
django-cors-headers
```

#### docker-compose.yml Configuration
```yaml
version: '3'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
```

### 3. Development Workflow

1. **Build the Docker image**:
   ```bash
   docker-compose build
   ```

2. **Run database migrations**:
   ```bash
   docker-compose run web python manage.py migrate
   ```

3. **Start the development server**:
   ```bash
   docker-compose up
   ```

4. **Access the application**:
   - The Django application will be available at http://localhost:8000
   - The admin interface will be at http://localhost:8000/admin

5. **Development with live code changes**:
   - The docker-compose.yml file includes a volume mount that maps your local code to the container
   - Changes to your code will be reflected immediately without rebuilding the image

### 4. Additional Considerations

1. **SQLite Database**:
   - The SQLite database file will be stored in the project directory
   - It will be persisted through the volume mount in docker-compose.yml

2. **Static Files**:
   - Static files will be served by Django's development server
   - For production, you would need to configure static file serving differently

3. **Secret Management**:
   - For development, secrets are kept in settings.py
   - For production, consider using environment variables or Docker secrets

## Diagram: Docker Development Architecture

```mermaid
graph TD
    A[Developer] -->|Code Changes| B[Local Project Directory]
    B <-->|Volume Mount| C[Docker Container]
    C -->|Serves| D[Django App :8000]
    C -->|Reads/Writes| E[SQLite DB]
    D -->|Accessed via| F[Browser http://localhost:8000]