# Cover Letter Generator - Frontend

A minimalist web application that generates personalized cover letters based on user's resume and job descriptions.

## Project Overview

This frontend application provides a user-friendly interface for:
- Uploading CV/resume files
- Submitting job descriptions (via text or image)
- Generating customized cover letters
- Editing and downloading the generated cover letters

## Tech Stack

- **HTML/CSS/JavaScript**: Vanilla frontend approach
- **HTMX**: For dynamic interactions without complex JavaScript
- **TailwindCSS**: For styling with DaisyUI components
- **PostCSS**: For processing CSS
- **DOMPurify**: For sanitizing user inputs

## Project Structure

```
frontend/
├── dist/                # Compiled output
│   ├── css/             # Compiled CSS
│   ├── js/              # JavaScript libraries
│   └── webfonts/        # Font Awesome webfonts
├── src/
│   ├── config.js        # Environment configuration
│   ├── main.css         # TailwindCSS imports
│   └── utils.js         # Utility functions
├── index.html           # Main application HTML
├── package.json         # Project dependencies and scripts
├── postcss.config.js    # PostCSS configuration
└── tailwind.config.js   # Tailwind with DaisyUI configuration
```

## Key Components

### Configuration (`src/config.js`)
- Manages environment detection (development vs production)
- Sets API endpoints based on environment
- Defines feature flags

### Utilities (`src/utils.js`)
- Input sanitization to prevent XSS attacks
- Form validation
- Error handling and display

### Main UI (`index.html`)
- Complete single-page application
- Form for uploading CV and job descriptions
- Cover letter editor with formatting options
- Download functionality

## Setup and Installation

### Prerequisites
- Node.js (v14+)
- npm or pnpm package manager

### Installation
```bash
# Install dependencies
npm install
# or
pnpm install
```

## Development

```bash
# Start development with CSS watching
npm run dev
# or
pnpm dev
```

This will:
1. Copy required dependencies to the dist folder
2. Watch CSS files for changes and recompile automatically

## Building for Production

```bash
# Build for production
npm run build
# or
pnpm build
```

This creates optimized assets in the `dist/` directory.

## Architecture

The application uses a minimalist approach:
- No framework dependencies (Vue, React, etc.)
- HTMX for AJAX and dynamic content updates
- Server communication handled through form submissions

## Backend Integration

The application connects to a Python backend API that:
1. Processes the CV/resume
2. Analyzes the job description
3. Generates a tailored cover letter using AI 