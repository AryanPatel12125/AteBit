# AteBit Legal Document Platform - Hackathon Boilerplate

🚀 **Minimal starter template for hackathon teams** - Zero features implemented, 100% infrastructure ready!

## 🎯 Purpose

This is a **BOILERPLATE ONLY** repository with complete version consistency and Docker setup. Perfect for hackathon teams to start coding immediately without setup conflicts.

**⚠️ NO ACTUAL FEATURES IMPLEMENTED** - Just infrastructure placeholders with TODO comments.

## 🛠️ Tech Stack & Versions

### Backend
- **Django:** 5.2.6
- **Django REST Framework:** 3.16  
- **Python:** 3.11.6
- **Database:** SQLite (development)

### Frontend  
- **Next.js:** 15.5.3
- **React:** 18.2.0
- **Node.js:** 18.18.0

### Infrastructure
- **Docker & Docker Compose**
- **CORS configured for development**
- **Environment variable management**

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git

### Setup & Run

```bash
# Clone and enter directory
git clone <repository-url>
cd AteBit

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000  
# Backend: http://localhost:8000
# Admin: http://localhost:8000/admin
```

That's it! Both frontend and backend will be running with live reload.

## 📁 Project Structure

```
AteBit/
├── backend/                 # Django API backend
│   ├── apps/               
│   │   ├── documents/      # Document models (TODO placeholders)
│   │   └── ai_services/    # AI analysis models (TODO placeholders)
│   ├── AteBit/             # Django project settings
│   ├── requirements.txt    # Python dependencies  
│   └── Dockerfile         # Backend container config
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js 13+ app directory
│   ├── components/        # React components (TODO placeholders)
│   ├── services/          # API services (TODO placeholders)
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Frontend container config
├── docker-compose.yml     # Multi-container setup
└── .env.example          # Environment variables template
```

## 👥 Team Starting Points

### 🔧 Backend Team
- **Models:** `backend/apps/*/models.py` - Add your database models
- **APIs:** `backend/apps/*/views.py` - Implement REST endpoints
- **Settings:** `backend/AteBit/settings.py` - Configure services
- **URLs:** `backend/AteBit/urls.py` - Add API routes

### 🎨 Frontend Team  
- **Components:** `frontend/components/` - Build UI components
- **Pages:** `frontend/app/` - Create application pages
- **Services:** `frontend/services/` - Add API integration
- **Styles:** Modify `frontend/app/globals.css`

### 🗄️ Database Team
- **Schema:** Define models in `backend/apps/*/models.py`
- **Migrations:** Run `python manage.py makemigrations`
- **Admin:** Configure `backend/apps/*/admin.py`

## 🔧 Development Commands

### Backend Commands
```bash
# Enter backend container
docker-compose exec backend bash

# Create Django app
python manage.py startapp myapp

# Database migrations  
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Install new packages
pip install package-name
# Don't forget to update requirements.txt!
```

### Frontend Commands
```bash  
# Enter frontend container
docker-compose exec frontend bash

# Install new packages
npm install package-name

# Run linting
npm run lint
```

## 📋 TODO Checklist

This boilerplate includes TODO comments for:

- [ ] Firebase integration setup
- [ ] Document upload functionality  
- [ ] AI analysis implementation
- [ ] User authentication system
- [ ] Database model relationships
- [ ] API endpoint implementation
- [ ] Frontend component development
- [ ] File processing pipeline
- [ ] Real-time features
- [ ] Production deployment setup

## 🔑 Environment Setup

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
# Edit .env with your actual configuration values
```

## 🐛 Troubleshooting

### Docker Issues
```bash  
# Rebuild containers
docker-compose down
docker-compose up --build

# View logs
docker-compose logs backend
docker-compose logs frontend
```

### Port Conflicts
- Backend runs on port 8000
- Frontend runs on port 3000  
- Change ports in `docker-compose.yml` if needed

### Dependencies
- Backend dependencies in `requirements.txt`
- Frontend dependencies in `package.json`
- Both files have exact versions specified

## 🤝 Contributing

This is a hackathon boilerplate - customize it for your project needs!

1. Uncomment relevant TODO sections
2. Add your actual configuration values  
3. Implement features in placeholder files
4. Update this README with your project details

## 📄 License

Open source - perfect for hackathons and learning! — Hackathon Project

Short description: This repository is used for the AteBit hackathon project. Keep the repo clean and follow the rules in `instructions.md`.

This is the AteBit hackathon project repository.

Quick notes:

- Read `instructions.md` before you start. It has the rules.
- Make a branch for your work: `feature/short-name` or `fix/short-name`.
- Use Pull Requests to merge into `main` and ask for a review.
- Do not commit secrets or change `.gitignore`.

Add your name to the Contributors section below when you join:

Contributors (Alphabetical order):
- Aryan Patel
- Dhruv Mistri
- Dhiraj Patil
- Diya Vyas
- Heli Parmar