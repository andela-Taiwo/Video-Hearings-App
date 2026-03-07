

## 📋 Prerequisites

- Python 3.12+ 
- Docker
- pip or uv package manager
- Node v22 +

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/andela-Taiwo/Video-Hearings-App.git
cd Video-Hearings-App
```

### 2. Install Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using uv (if available):
```bash
uv pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```bash
# Database Configuration
DATABASE_URL="datbase url"
PROD_SECRET_KEY=""
SECRET_KEY=""

# Database Configuration
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=1

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

```

### 4. Build and Run the Application

```bash
 # Build and start all services
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v

```
#### Test Super Admin User
```bash
Test SuperAdmin:
   - email="admin@courts.gov.uk"
   - password="admin123"
```

## 🔧 Configuration

### Access the Application

| Service | URL | Description |
|----------|-------------|---------|
| `Frontend` | http://localhost:3000 | `React App` |
| `Backend API` | http://localhost:8000/api/v1| `Dhjando Rest API` |
| `Admin Panel` | http://localhost:8000/admin| `Django Admin` |
| `API Docs` | http://localhost:8000/swagger | `Swagger/OpenAPI Docs` |

### Local  Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local settings

# Run database migrations
python manage.py migrate

# Seed initial data
python manage.py seed_data

# Create superuser (for admin access)
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
tox
```


### Local Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
yarn install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your settings

# Run development server
npm start

# Run tests
yarn test

# Run tests with coverage
yarn test -- --coverage

# Build for production
yarn run build
```


## 🛠️ Development

### API Endpoints


|Method	| Endpoint | Description
|--------|---------|------------
GET	| /api/v1/hearings/	| List all hearings
POST |	/api/v1/hearings/ |	Create new hearing
GET | /api/v1/hearings/{id}/| Get hearing details
PUT	| /api/v1/hearings/{id}/ | 	Update hearing
DELETE | /api/v1/hearings/{id}/ |	Delete hearing
POST| /api/v1/hearings/{id}/cancel/| Cancel hearing
POST | /api/v1/hearings/{id}/reschedule/ | Reschedule hearing
POST | /api/v1/hearings/{id}/add_participants/	| Add participants
GET	| /api/v1/courts/courtrooms/ | List courtrooms
GET	| /api/v1/cases/ |	List cases




## 🐛 Troubleshooting

### Limitations
These are the core features that are yet to be implemented
- uplaoading hearing documents
- Notification logic
- mail Notification
- Authentication and Authorization
- CD/CD workflows
- Monitoring
- Rate limiting
