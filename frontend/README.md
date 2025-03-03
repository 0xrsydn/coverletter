# Cover Letter Generator Frontend

A modern web application that generates personalized cover letters based on your resume/CV and job descriptions.

## Features

- Upload CV/resume files in PDF or DOCX format
- Provide job descriptions as text or image
- Generate tailored cover letters
- Copy to clipboard functionality
- Responsive design with Tailwind CSS and DaisyUI

## Tech Stack

- HTML5
- Tailwind CSS with DaisyUI components
- HTMX for interactive functionality
- Parcel for bundling and building
- DOMPurify for security

## Development Setup

1. Clone the repository
2. Install dependencies:
   ```
   npm install
   ```
3. Create a `.env` file with your API URL:
   ```
   API_URL=https://your-api-url.com/generate_cover_letter
   ```
4. Run the development server:
   ```
   npm run dev
   ```

## Building for Production

```
npm run build
```

This will create optimized files in the `dist/` directory ready for deployment.

## Environment Configuration

The application automatically detects whether it's running in development or production mode:

- Development: Uses `http://localhost:8000` as fallback API URL
- Production: Uses the URL specified in the `.env` file

## Security Features

- Input sanitization with DOMPurify
- Environment variables for sensitive URLs
- Form validation

## License

ISC 