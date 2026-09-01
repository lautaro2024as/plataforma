/**
 * Vercel Web Analytics initialization for Django project
 * This script loads and initializes Vercel Web Analytics
 */
(function() {
  'use strict';
  
  // Initialize the queue for Vercel Analytics
  window.va = window.va || function() {
    (window.vaq = window.vaq || []).push(arguments);
  };
  
  // Create script element to load analytics
  var script = document.createElement('script');
  script.defer = true;
  script.src = '/_vercel/insights/script.js';
  
  // Append to document
  document.head.appendChild(script);
})();
