// Environment configuration
const isDevelopment = process.env.NODE_ENV === 'development';

// API configuration
const config = {
  // API base URL - determined purely by NODE_ENV
  apiBaseUrl: isDevelopment 
    ? 'http://localhost:8000'  // Development URL
    : process.env.API_URL,     // Production URL from .env

  // Version info
  version: process.env.npm_package_version || '1.0.0',
  
  // Feature flags
  features: {
    debug: isDevelopment,
  }
};

// Freeze the config to prevent modifications
Object.freeze(config);

export default config; 