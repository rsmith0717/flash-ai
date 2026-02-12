# Flash AI

An AI-powered flashcard application that helps you learn more effectively using intelligent flashcard generation and spaced repetition.

## 🚀 Overview

Flash AI is a full-stack application that combines modern web technologies with AI capabilities to create an intelligent learning platform. The application uses Large Language Models (LLMs) to generate flashcards, provide explanations, and enhance the learning experience.

## 🛠️ Technologies Used

### Backend
- **Python 3.12** - Core programming language
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - ORM for database interactions
- **Alembic** - Database migration tool
- **LangChain** - Framework for developing LLM-powered applications
- **LangGraph** - Library for building stateful, multi-actor applications with LLMs
- **FastAPI Users** - Authentication and user management
- **Uvicorn** - ASGI server for running the application

### Frontend
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **TanStack Router** - Type-safe routing solution
- **TanStack Query** - Data fetching and caching
- **TanStack Start** - Full-stack React framework
- **Tailwind CSS** - Utility-first CSS framework
- **DaisyUI** - Component library for Tailwind
- **Lucide React** - Icon library
- **Biome** - Fast formatter and linter

### Database & AI
- **PostgreSQL 17** with **pgvector** - Vector database for embeddings
- **Ollama** - Local LLM runtime
  - Chat Model: `llama3.2:3b-instruct-q4_K_M`
  - Embedding Model: `nomic-embed-text:latest`

### DevOps & Tools
- **Docker** & **Docker Compose** - Containerization
- **uv** - Fast Python package manager
- **pnpm** - Efficient Node.js package manager
- **Just** - Command runner (Makefile alternative)
- **mise** - Development environment manager

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10 or higher) & **Docker Compose** (version 2.0 or higher)
- **NVIDIA GPU** (optional, but recommended for better performance with Ollama)
- **NVIDIA Container Toolkit** (if using GPU support)

### For Local Development (without Docker):
- **Python 3.12+**
- **Node.js 24+**
- **pnpm** (for frontend)
- **uv** (for Python package management)
- **PostgreSQL 17** with pgvector extension
- **Ollama** (for local LLM)

## 🚀 Quick Start with Docker

The easiest way to get started is using Docker Compose:

### 1. Clone the Repository

```bash
git clone https://github.com/rsmith0717/flash-ai.git
cd flash-ai
```

### 2. Set Up Environment Variables

Create environment files from the examples:

```bash
# Database configuration
cp db.env.example db.env

# API configuration
cp api.env.example api.env

# Ollama configuration
cp ollama.env.example ollama.env
```

Edit these files if you need to change default values.

### 3. Start the Application

```bash
# Using Just (recommended)
just dev

# Or using Docker Compose directly
docker compose build && docker compose up
```

This will:
- Start PostgreSQL with pgvector extension (port 5433)
- Download and run Ollama with required models (port 11434)
- Start the FastAPI backend (port 8000)
- Start the React frontend (port 3000)

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Create a User

After the services are running, you can create additional users:

```bash
just create-user
```

Or manually:

```bash
docker exec -it flash-ai-backend-1 uv run app/scripts/user_create.py
```

## 💻 Local Development Setup

For development without Docker:

### Backend Setup

1. **Install Python dependencies using uv**:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

2. **Set up PostgreSQL**:

```bash
# Install PostgreSQL 17 with pgvector
# Then create the database
psql -U postgres -c "CREATE DATABASE flashcarddb;"
```

3. **Set up Ollama**:

```bash
# Install Ollama (visit https://ollama.com)
# Pull required models
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull nomic-embed-text:latest
```

4. **Configure environment variables**:

Update `api.env` with your local settings:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/flashcarddb
APP_OLLAMA_BASE_URL=http://localhost:11434
APP_CHAT_MODEL=llama3.2:3b-instruct-q4_K_M
APP_EMBEDDING_MODEL=nomic-embed-text:latest
```

5. **Run the backend**:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. **Install Node.js dependencies**:

```bash
cd frontend
pnpm install
```

2. **Configure environment**:

Create `.env.local` in the frontend directory:

```env
VITE_BACKEND_URL=http://localhost:8000
```

3. **Run the frontend**:

```bash
pnpm dev
```

## 📝 Available Commands

The project uses `just` as a command runner. Here are the available commands:

```bash
# Development
just dev                # Start all services with Docker Compose
just build              # Build Docker images
just down               # Stop and remove all containers
just force-rebuild      # Full rebuild without cache

# Code Quality (Backend)
just format             # Format Python code with Ruff
just lint               # Lint Python code with Ruff
just test               # Run backend tests with pytest
just validate           # Run format, lint, and test

# User Management
just create-user        # Create a new user interactively
```

### Frontend Commands

```bash
cd frontend

pnpm dev                # Start development server
pnpm build              # Build for production
pnpm preview            # Preview production build
pnpm test               # Run tests
pnpm format             # Format code with Biome
pnpm lint               # Lint code with Biome
pnpm check              # Run all Biome checks
```

## 📁 Project Structure

```
flash-ai/
├── app/                    # Backend application
│   ├── api/               # API routes and endpoints
│   │   └── routes/        # Route handlers (chat, flashcard, user)
│   ├── core/              # Core configuration and utilities
│   ├── database/          # Database setup and initialization
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── scripts/           # Utility scripts (user creation, etc.)
│   ├── services/          # Business logic services
│   └── main.py           # FastAPI application entry point
├── frontend/              # Frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── context/      # React context providers
│   │   ├── routes/       # TanStack Router routes
│   │   └── styles.css    # Global styles
│   ├── public/           # Static assets
│   └── vite.config.ts    # Vite configuration
├── data/                  # Application data (generated)
├── logs/                  # Application logs (generated)
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile.app         # Backend Dockerfile
├── Dockerfile.fe          # Frontend Dockerfile
├── pyproject.toml         # Python project configuration
├── justfile              # Just command definitions
└── init.sql              # Database initialization script
```

## 🔧 Configuration

### Environment Variables

#### Database (db.env)
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password

#### API (api.env)
- `DATABASE_URL` - PostgreSQL connection string
- `APP_OLLAMA_BASE_URL` - Ollama API URL
- `APP_CHAT_MODEL` - LLM model for chat
- `APP_EMBEDDING_MODEL` - Model for embeddings

#### Ollama (ollama.env)
- `OLLAMA_HOST` - Host for Ollama server
- `APP_CHAT_MODEL` - Chat model to pull
- `APP_EMBEDDING_MODEL` - Embedding model to pull

## 🐛 Troubleshooting

### GPU Support Issues

If you don't have an NVIDIA GPU, modify `docker-compose.yml` and comment out the GPU-related sections:

```yaml
# Comment out these lines in the ollama service:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: all
#           capabilities: [gpu]
```

### Port Conflicts

If ports are already in use:
- PostgreSQL: Change `5433:5432` in docker-compose.yml
- Ollama: Change `11434:11434` in docker-compose.yml
- Backend: Change `8000:8000` in docker-compose.yml
- Frontend: Change `3000:3000` in docker-compose.yml

### Database Connection Issues

Ensure PostgreSQL is running and the credentials in your environment files match.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [LangChain](https://www.langchain.com/)
- UI components from [TanStack](https://tanstack.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Local AI with [Ollama](https://ollama.com/)
