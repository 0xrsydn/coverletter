# AI Cover Letter Generator

A modern web application that automatically generates tailored cover letters based on your resume, job descriptions, and company information using AI.

## Overview

This project uses AI to streamline the job application process by generating personalized cover letters that highlight relevant experience and skills based on the specific job and company you're applying to.

### Key Features

- **Resume Parsing**: Extract key skills and experience from your CV/resume
- **Job Description Analysis**: Identify key requirements and qualifications from job postings
- **Company Research**: Automatically gather company information to personalize your letter
- **AI-Powered Generation**: Create tailored, professional cover letters that match the job and company
- **Multiple Input Methods**: Upload documents or paste text for job descriptions
- **Modern UI**: Clean, responsive interface that works on desktop and mobile devices

## Architecture

The application is built with a modern, scalable architecture:

- **Frontend**: HTMX with Daisy UI CSS for styling
- **Backend**: FastAPI Python backend
- **Containerization**: Docker support for easy deployment

## Getting Started

### Prerequisites

- Node.js 16+ and npm/pnpm (frontend)
- Python 3.9+ (backend)
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cover-letter.git
   cd cover-letter
   ```

2. Set up the backend:
   ```bash
   cd backend
   cp .env.example .env  # Configure your environment variables
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd ../frontend
   cp .env.example .env  # Configure your environment variables
   npm install  # or pnpm install
   ```

### Running Locally

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev  # or pnpm dev
   ```

3. Access the application at http://localhost:1234

### Docker Deployment

To run the entire application using Docker:

```bash
docker-compose up -d
```

## Documentation

- [Backend API Documentation](/backend/README.md): Detailed information about the API endpoints, configuration, and development
- [Frontend Documentation](/frontend/README.md): Information about the frontend architecture, components, and development

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.



