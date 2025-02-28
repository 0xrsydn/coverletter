// Import DOMPurify (will be loaded as a module in index.html)
import DOMPurify from 'dompurify';

/**
 * Sanitize a string to prevent XSS attacks
 * @param {string} input - The string to sanitize
 * @returns {string} Sanitized string
 */
export function sanitizeInput(input) {
  if (!input) return '';
  return DOMPurify.sanitize(input, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] }).trim();
}

/**
 * Sanitize HTML content for display
 * @param {string} html - The HTML to sanitize
 * @returns {string} Sanitized HTML
 */
export function sanitizeHtml(html) {
  if (!html) return '';
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'em', 'strong', 'u', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: []
  });
}

/**
 * Display an error message
 * @param {string} message - Error message
 * @param {string} elementId - Target element ID (defaults to common error display)
 */
export function showError(message, elementId = 'error_container') {
  const errorElement = document.getElementById(elementId);
  if (errorElement) {
    errorElement.textContent = sanitizeInput(message);
    errorElement.classList.remove('hidden');
    
    // Auto hide after 5 seconds
    setTimeout(() => {
      errorElement.classList.add('hidden');
    }, 5000);
  } else {
    console.error('Error:', message);
  }
}

/**
 * Validate form inputs
 * @param {FormData} formData - The form data to validate
 * @returns {Object} Validation result with isValid and errorMessage
 */
export function validateForm(formData) {
  // Check for CV file
  const cvFile = formData.get('cv_file');
  if (!cvFile || cvFile.size === 0) {
    return { isValid: false, errorMessage: 'Please upload your CV/resume file' };
  }
  
  // Check job description - either text or image must be provided
  const jobDescText = formData.get('job_desc_text');
  const jobDescImage = formData.get('job_desc_image');
  
  if ((!jobDescText || jobDescText.trim() === '') && (!jobDescImage || jobDescImage.size === 0)) {
    return { isValid: false, errorMessage: 'Please provide either job description text or image' };
  }
  
  return { isValid: true, errorMessage: '' };
} 