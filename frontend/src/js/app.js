// Main application entry point
import config from '../config.js';
import { sanitizeInput, sanitizeHtml, showError, validateForm } from '../utils.js';
import { setupFormHandlers } from './form-handlers.js';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  console.log('Cover Letter Generator initialized');
  
  // Make config and utils available globally (for HTMX and inline scripts)
  window.appConfig = config;
  window.appUtils = { sanitizeInput, sanitizeHtml, showError, validateForm };
  
  // Setup form handlers
  setupFormHandlers();
}); 