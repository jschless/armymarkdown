document.addEventListener('DOMContentLoaded', function() {
  // Handle title clicks
  document.querySelectorAll('.document-title').forEach(function(element) {
    element.addEventListener('click', function() {
      const url = element.getAttribute('data-url');
      window.location.href = url;
    });
  });

  // Handle "View in classic editor" button clicks
  document.querySelectorAll('.classic-editor-button').forEach(function(button) {
    button.addEventListener('click', function() {
      const url = button.getAttribute('data-url');
      window.location.href = url;
    });
  });

  // Handle "View in form editor" button clicks
  document.querySelectorAll('.form-editor-button').forEach(function(button) {
    button.addEventListener('click', function() {
      const url = button.getAttribute('data-url');
      window.location.href = url;
    });
  });

  // Handle "Delete document" button clicks
  document.querySelectorAll('.delete-document-button').forEach(function(button) {
    button.addEventListener('click', function() {
      const url = button.getAttribute('data-url');
      window.location.href = url;
    });
  });
});
