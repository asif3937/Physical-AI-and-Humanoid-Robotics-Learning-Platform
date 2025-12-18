# AI-Native Textbook Platform

Welcome to the AI-Native Textbook with RAG Chatbot - an interactive learning platform focused on Physical AI and related topics. This platform combines comprehensive textbook content with an AI-powered chatbot that can answer questions based on the textbook material.

## 📚 About the Textbook

This textbook covers essential concepts of Physical AI through six comprehensive chapters:

1. **Introduction to Physical AI** - Foundational concepts, history, and key applications
2. **Basics of Humanoid Robotics** - Core principles of humanoid design, locomotion, manipulation, and sensing
3. **ROS 2 Fundamentals** - Introduction to Robot Operating System 2
4. **Digital Twin Simulation** - Concepts using Gazebo and NVIDIA Isaac Sim
5. **Vision-Language-Action Systems** - Integration of computer vision, NLP, and robotic action
6. **Capstone Project** - Integration of learned concepts in a comprehensive project

## 🤖 AI Chatbot

The platform features an integrated AI chatbot powered by Retrieval-Augmented Generation (RAG) that can:
- Answer questions about the textbook content
- Provide explanations and clarifications
- Reference specific sections of the textbook
- Engage in interactive learning conversations

## 🏗️ Architecture

### Frontend
- **Framework**: Docusaurus 3.x
- **Hosting**: GitHub Pages
- **Features**: Responsive design, search, interactive chat interface

### Backend
- **Framework**: FastAPI (Python)
- **Vector Database**: Qdrant for content retrieval
- **Embeddings**: Sentence Transformers
- **Hosting**: Railway or Render
- **API**: RESTful endpoints for chat and health monitoring

## 🚀 Quick Start

### Prerequisites
- Node.js (v20+ for frontend)
- Python (v3.9+ for backend)
- Docker (for local vector database)

### Frontend Development
```bash
cd textbook
npm install
npm start
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt
docker-compose up -d  # To start Qdrant vector database
uvicorn main:app --reload
```

## 🚀 Deployment

### Frontend (GitHub Pages)
1. The Docusaurus site is configured for GitHub Pages deployment
2. GitHub Actions workflow automatically builds and deploys on commits to main branch
3. See `textbook/.github/workflows/deploy.yml` for configuration

### Backend (Railway/Render)
1. Containerized with Docker
2. Deployable to Railway or Render with provided configurations
3. Environment variables configured for production

## 🛠️ Environment Setup

### Backend Environment Variables
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

Required variables:
- `DATABASE_URL`: PostgreSQL database connection string
- `QDRANT_URL`: Qdrant vector database URL
- `QDRANT_API_KEY`: Qdrant API key (if using cloud)
- `EMBEDDING_MODEL`: Model for text embeddings (default: all-MiniLM-L6-v2)
- `LLM_MODEL`: Model for response generation
- `OPENAI_API_KEY` or equivalent for chosen LLM provider

## 🧪 Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd textbook
npm run build
```

## 📋 Project Status

**COMPLETED** - Ready for Production Deployment

All components have been implemented and tested:
- ✅ Complete textbook content
- ✅ Functional RAG system
- ✅ Production deployment configurations
- ✅ Health monitoring and security
- ✅ Documentation and launch procedures

## 📄 Documentation

Comprehensive documentation is available in the `backend/docs/` directory:
- Environment setup guide
- Health checks documentation
- Launch checklist
- API documentation

## 🤝 Contributing

This project was built using Spec-Driven Development principles. All changes follow the established architecture and maintain the core principles of the platform.

## 📞 Support

For support, please check the documentation in `backend/docs/` or create an issue in this repository.

---

**Project completed and ready for launch!**