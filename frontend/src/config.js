// Environment configuration
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// API configuration
const config = {
  // API base URL - automatically detects environment
  apiBaseUrl: isDevelopment 
    ? 'http://localhost:8000'  // Development
    : '/api', // Production - using relative path for same-domain API

  // Version info
  version: '1.0.0',
  
  // Feature flags
  features: {
    debug: isDevelopment,
  }
};

// Freeze the config to prevent modifications
Object.freeze(config);

export default config; 