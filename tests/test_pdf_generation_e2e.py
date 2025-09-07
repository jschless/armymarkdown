"""
Focused end-to-end tests for PDF generation from both home page and form view.
Tests that the "Create Memo PDF" button works and produces PDFs correctly.
"""

import os
import time
from unittest.mock import Mock, patch

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="module")
def chrome_driver():
    """Set up Chrome WebDriver for testing."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(5)

    yield driver
    driver.quit()


@pytest.fixture
def app_url():
    """Application URL for testing."""
    return os.getenv("TEST_APP_URL", "http://localhost:8000")


@pytest.fixture
def sample_memo_text():
    """Sample memo content for testing."""
    return """ORGANIZATION_NAME=Test Battalion
ORGANIZATION_STREET_ADDRESS=123 Test Street
ORGANIZATION_CITY_STATE_ZIP=Test City, ST 12345
OFFICE_SYMBOL=TEST-OPS
AUTHOR=Test Author
RANK=CPT
BRANCH=EN
SUBJECT=Selenium Test Memo

- This is a test memo for Selenium automation
- It validates PDF generation functionality
- Point of contact is test automation system"""


class TestPDFGeneration:
    """Test PDF generation from both interfaces."""

    def wait_for_element(self, driver, by, value, timeout=10):
        """Wait for element to be present."""
        return WebDriverWait(driver, timeout).until(
            expected_conditions.presence_of_element_located((by, value))
        )

    def wait_for_clickable(self, driver, by, value, timeout=10):
        """Wait for element to be clickable."""
        return WebDriverWait(driver, timeout).until(
            expected_conditions.element_to_be_clickable((by, value))
        )

    def check_progress_not_nan(self, driver):
        """Check that progress doesn't show NaN%."""
        try:
            progress_element = driver.find_element(By.ID, "progress-percentage")
            text = progress_element.text
            assert "NaN%" not in text, f"Progress shows NaN%: {text}"
            return text
        except Exception:
            return None

    @pytest.mark.selenium
    @patch("app.create_memo.delay")
    def test_pdf_from_home_page(
        self, mock_celery, chrome_driver, app_url, sample_memo_text
    ):
        """Test PDF generation from home page editor."""
        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "test-home-123"
        mock_celery.return_value = mock_task

        # Navigate to home page
        chrome_driver.get(app_url)

        # Find and fill the editor
        editor = self.wait_for_element(chrome_driver, By.ID, "editor")
        editor.clear()
        editor.send_keys(sample_memo_text)

        # Click Create PDF button
        create_btn = self.wait_for_clickable(chrome_driver, By.ID, "start-bg-job")
        create_btn.click()

        # Check progress modal appears
        progress_modal = self.wait_for_element(chrome_driver, By.ID, "progress-modal")
        assert progress_modal.is_displayed()

        # Verify progress text is not NaN%
        progress_text = self.check_progress_not_nan(chrome_driver)
        assert progress_text is not None, "Progress element not found"

        # Verify Celery was called
        mock_celery.assert_called_once()

    @pytest.mark.selenium
    @patch("app.create_memo.delay")
    def test_pdf_from_form_view(self, mock_celery, chrome_driver, app_url):
        """Test PDF generation from form builder."""
        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "test-form-456"
        mock_celery.return_value = mock_task

        # Navigate to form page
        chrome_driver.get(f"{app_url}/form")

        # Fill required form fields
        fields = {
            "ORGANIZATION_NAME": "Test Form Unit",
            "ORGANIZATION_STREET_ADDRESS": "456 Form Street",
            "ORGANIZATION_CITY_STATE_ZIP": "Form City, ST 67890",
            "OFFICE_SYMBOL": "FORM-TEST",
            "AUTHOR": "Form Test Author",
            "RANK": "MAJ",
            "BRANCH": "IN",
            "SUBJECT": "Form Builder Test",
            "MEMO_TEXT": "- Test memo from form builder\n- Validates form functionality",
        }

        for field_id, value in fields.items():
            field = self.wait_for_element(chrome_driver, By.ID, field_id)
            field.clear()
            field.send_keys(value)

        # Submit the form
        submit_btn = self.wait_for_clickable(
            chrome_driver,
            By.CSS_SELECTOR,
            "input[type='submit'], button[type='submit']",
        )
        submit_btn.click()

        # Check progress modal appears
        progress_modal = self.wait_for_element(chrome_driver, By.ID, "progress-modal")
        assert progress_modal.is_displayed()

        # Verify progress text is not NaN%
        progress_text = self.check_progress_not_nan(chrome_driver)
        assert progress_text is not None, "Progress element not found"

        # Verify Celery was called
        mock_celery.assert_called_once()

    @pytest.mark.selenium
    def test_progress_bar_nan_bug(self, chrome_driver, app_url, sample_memo_text):
        """Specific test for the NaN% progress bug."""
        chrome_driver.get(app_url)

        # Fill editor and start process (without mocking to see real behavior)
        editor = self.wait_for_element(chrome_driver, By.ID, "editor")
        editor.clear()
        editor.send_keys(sample_memo_text)

        create_btn = self.wait_for_clickable(chrome_driver, By.ID, "start-bg-job")
        create_btn.click()

        # Monitor progress for a few seconds
        start_time = time.time()
        nan_found = False
        progress_values = []

        while time.time() - start_time < 5:  # Monitor for 5 seconds
            try:
                progress_element = chrome_driver.find_element(
                    By.ID, "progress-percentage"
                )
                text = progress_element.text
                progress_values.append(text)

                if "NaN%" in text:
                    nan_found = True
                    break

            except Exception:
                pass

            time.sleep(0.5)

        # Report what we found
        print(f"Progress values observed: {progress_values}")
        assert not nan_found, f"Found NaN% in progress values: {progress_values}"


# Helper function to run tests manually
def run_selenium_tests():
    """Run selenium tests manually for development."""
    pytest.main([__file__, "-v", "-m", "selenium", "--tb=short"])


if __name__ == "__main__":
    run_selenium_tests()
