# Cellarium Backend

A Django-based backend application for wine management.

## Docker Development Setup

This project is configured to run in a Docker container for development.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Getting Started

1. **Build the Docker image**:

   ```bash
   docker-compose build
   ```

2. **Run database migrations**:

   ```bash
   docker-compose run web python manage.py migrate
   ```

3. **Create a superuser** (optional):

   ```bash
   docker-compose run web python manage.py createsuperuser
   ```

4. **Start the development server**:

   ```bash
   docker-compose up
   ```

5. **Access the application**:
   - The Django application will be available at http://localhost:8000
   - The admin interface will be at http://localhost:8000/admin

### Development Workflow

- The docker-compose.yml file includes a volume mount that maps your local code to the container
- Changes to your code will be reflected immediately without rebuilding the image
- The SQLite database file is stored in the project directory and persisted through the volume mount

### Common Commands

- **Start the application in detached mode**:

  ```bash
  docker-compose up -d
  ```

- **View logs**:

  ```bash
  docker-compose logs -f
  ```

- **Stop the application**:

  ```bash
  docker-compose down
  ```

- **Run Django management commands**:

  ```bash
  docker-compose run web python manage.py [command]
  ```

- **Run tests**:

  ```bash
  docker-compose run web python manage.py test
  ```

- **Install new dependencies**:
  
  1. Add the dependency to requirements.txt
  2. Rebuild the Docker image:
     ```bash
     docker-compose build
     ```

### Project Structure

- `cellarium_backend/`: Main Django project directory
- `winemanager/`: Django app for wine management
- `Dockerfile`: Docker configuration for the application
- `docker-compose.yml`: Docker Compose configuration
- `requirements.txt`: Python dependencies