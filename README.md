# IBM CloudMate

IBM CloudMate is an intelligent cloud infrastructure agent powered by IBM Cloud services. This application helps users manage cloud resources and perform various cloud operations through a user-friendly interface.

## Features

- Cloud Object Storage (COS) Management
- Cloudant Database Operations
- Intelligent Chat Interface
- File Upload and Management
- Conversation History
- Real-time Cloud Operations

## Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB
- Google Cloud Account (for Gemini API)
- ffmpeg (brew install ffmpeg)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Backend Environment Variables
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=mongodb://admin:password123@localhost:27017

# Frontend Environment Variables (create in frontend/.env)
REACT_APP_API_URL=http://localhost:8000
```

## Backend Setup

1. Navigate to the project root directory:
   ```bash
   cd /path/to/project
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   uvicorn app:app --reload --port 8000
   ```

The backend API will be available at `http://localhost:8000`

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend application will be available at `http://localhost:3000`

## Docker Setup (Optional)

You can also run the application using Docker:

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Available Scripts

### Backend
- `uvicorn app:app --reload`: Start the development server
- `pytest`: Run tests

### Frontend
- `npm start`: Start the development server
- `npm test`: Run tests
- `npm run build`: Build for production
- `npm run eject`: Eject from Create React App

## Project Structure

```
.
├── app.py                 # Backend FastAPI application
├── requirements.txt       # Python dependencies
├── frontend/             # React frontend application
├── uploads/              # File upload directory
├── tools/               # Backend tools and utilities
└── docker-compose.yml   # Docker configuration
```
# IBMCloudMate-Agent
