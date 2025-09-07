"""
Utility functions for Selenium-based end-to-end tests.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumTestHelper:
    """Helper class for common Selenium operations."""
    
    def __init__(self, driver, default_timeout=10):
        self.driver = driver
        self.default_timeout = default_timeout
    
    def wait_for_element(self, by, value, timeout=None):
        """Wait for an element to be present and return it."""
        timeout = timeout or self.default_timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_clickable(self, by, value, timeout=None):
        """Wait for an element to be clickable and return it."""
        timeout = timeout or self.default_timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
    
    def wait_for_visible(self, by, value, timeout=None):
        """Wait for an element to be visible and return it."""
        timeout = timeout or self.default_timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
    
    def wait_for_invisible(self, by, value, timeout=None):
        """Wait for an element to become invisible."""
        timeout = timeout or self.default_timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located((by, value))
        )
    
    def wait_for_text_in_element(self, by, value, text, timeout=None):
        """Wait for specific text to appear in an element."""
        timeout = timeout or self.default_timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element((by, value), text)
        )
    
    def safe_click(self, element):
        """Safely click an element, scrolling to it if necessary."""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Brief pause for scroll
        element.click()
    
    def fill_form_field(self, field_id, value, clear=True):
        """Fill a form field with a value."""
        field = self.wait_for_element(By.ID, field_id)
        if clear:
            field.clear()
        field.send_keys(value)
        return field
    
    def check_no_javascript_errors(self):
        """Check for JavaScript errors in the browser console."""
        logs = self.driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        # Filter out known acceptable errors
        filtered_errors = []
        for error in errors:
            message = error.get('message', '').lower()
            # Skip favicon 404s and other non-critical errors
            if 'favicon' not in message and '404' not in message:
                filtered_errors.append(error)
        
        return filtered_errors
    
    def wait_for_progress_complete(self, timeout=30):
        """Wait for progress modal to appear and then disappear."""
        try:
            # Wait for progress modal to appear
            self.wait_for_visible(By.ID, "progress-modal", timeout=5)
            
            # Wait for it to disappear (completion)
            self.wait_for_invisible(By.ID, "progress-modal", timeout=timeout)
            
            return True
        except Exception:
            return False
    
    def get_progress_text(self):
        """Get current progress text, returns None if not found."""
        try:
            progress_element = self.driver.find_element(By.ID, "progress-percentage")
            return progress_element.text
        except Exception:
            return None
    
    def validate_progress_text(self, text):
        """Validate that progress text is reasonable (not NaN%, etc.)."""
        if not text:
            return False, "No progress text found"
        
        if "NaN%" in text:
            return False, f"Progress shows NaN%: {text}"
        
        if text == "Processing...":
            return True, "Indeterminate progress"
        
        if text.endswith("%"):
            try:
                percentage = float(text[:-1])
                if 0 <= percentage <= 100:
                    return True, f"Valid percentage: {percentage}%"
                else:
                    return False, f"Invalid percentage range: {percentage}%"
            except ValueError:
                return False, f"Invalid percentage format: {text}"
        
        return False, f"Unknown progress format: {text}"


class MemoTestData:
    """Test data for memo generation tests."""
    
    SAMPLE_MEMO_MARKDOWN = """ORGANIZATION_NAME=4th Engineer Battalion
ORGANIZATION_STREET_ADDRESS=588 Wetzel Road  
ORGANIZATION_CITY_STATE_ZIP=Colorado Springs, CO 80904
OFFICE_SYMBOL=ABC-DEF-GH
AUTHOR=Joseph C. Schlessinger
RANK=1LT
BRANCH=EN
TITLE=Test Officer
MEMO_TYPE=MEMORANDUM FOR RECORD
SUBJECT=Selenium Test Memo

- This is a test memo generated by Selenium automation.
- It validates that PDF generation works correctly.
    - This is a sub-item to test nested formatting.
    - Another sub-item for completeness.
- **Bold text** and *italic text* should be formatted correctly.
- Point of contact is the undersigned at (719) 555-0123."""

    SAMPLE_FORM_DATA = {
        "ORGANIZATION_NAME": "Test Battalion (Selenium)",
        "ORGANIZATION_STREET_ADDRESS": "123 Automation Street",
        "ORGANIZATION_CITY_STATE_ZIP": "Test City, ST 12345-6789",
        "OFFICE_SYMBOL": "TEST-AUTO-OPS",
        "AUTHOR": "Selenium Test Author",
        "RANK": "CPT",
        "BRANCH": "EN", 
        "TITLE": "Test Automation Officer",
        "SUBJECT": "Selenium Form Builder Test Memo",
        "MEMO_TEXT": """- This memo was generated using the form builder interface.
- It tests the form-based workflow for PDF generation.
- All form fields should be properly validated and processed.
    - This is a nested item to test formatting.
- Point of contact for this test is the test automation system."""
    }
    
    INVALID_MEMO_DATA = """INVALID_FIELD=This should cause an error
SUBJECT=Test memo with invalid field

- This memo contains invalid fields and should be rejected."""

    MINIMAL_VALID_MEMO = """ORGANIZATION_NAME=Minimal Test Unit
SUBJECT=Minimal Test Memo

- This is a minimal valid memo for basic testing."""