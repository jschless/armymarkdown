"""
UI-focused Selenium tests that test the front-end behavior without mocking backend.
These tests validate that the JavaScript fixes work correctly.
"""

import os
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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


class TestUIBehavior:
    """Test UI behavior and JavaScript functionality."""

    def wait_for_element(self, driver, by, value, timeout=10):
        """Wait for element to be present."""
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_clickable(self, driver, by, value, timeout=10):
        """Wait for element to be clickable."""
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    @pytest.mark.selenium
    def test_home_page_loads_correctly(self, chrome_driver, app_url):
        """Test that home page loads with all required elements."""
        chrome_driver.get(app_url)

        # Check main elements are present
        editor = self.wait_for_element(chrome_driver, By.ID, "editor")
        assert editor.is_displayed()

        create_button = self.wait_for_element(chrome_driver, By.ID, "start-bg-job")
        assert create_button.is_displayed()
        assert "Create Memo PDF" in create_button.text

        # Check that progress modal elements exist (but are hidden)
        progress_modal = chrome_driver.find_element(By.ID, "progress-modal")
        assert not progress_modal.is_displayed()

        progress_text = chrome_driver.find_element(By.ID, "progress-percentage")
        assert progress_text.text in ["0%", ""], (
            f"Unexpected initial progress text: {progress_text.text}"
        )

    @pytest.mark.selenium
    def test_form_page_loads_correctly(self, chrome_driver, app_url):
        """Test that form page loads with all required elements."""
        chrome_driver.get(f"{app_url}/form")

        # Check form elements are present
        form = self.wait_for_element(chrome_driver, By.ID, "memo")
        assert form.is_displayed()

        # Check some key form fields
        org_name = self.wait_for_element(chrome_driver, By.ID, "ORGANIZATION_NAME")
        assert org_name.is_displayed()

        subject_field = self.wait_for_element(chrome_driver, By.ID, "SUBJECT")
        assert subject_field.is_displayed()

        submit_button = self.wait_for_element(
            chrome_driver,
            By.CSS_SELECTOR,
            "input[type='submit'], button[type='submit']",
        )
        assert submit_button.is_displayed()

    @pytest.mark.selenium
    def test_progress_modal_shows_processing_text(self, chrome_driver, app_url):
        """Test that clicking create PDF shows progress modal with correct text."""
        chrome_driver.get(app_url)

        # Fill in some sample content
        editor = self.wait_for_element(chrome_driver, By.ID, "editor")
        sample_content = """ORGANIZATION_NAME=Test Unit
SUBJECT=Test Memo

- This is a test memo for UI validation"""
        editor.clear()
        editor.send_keys(sample_content)

        # Click create PDF button
        create_button = self.wait_for_clickable(chrome_driver, By.ID, "start-bg-job")
        create_button.click()

        # Wait for progress modal to appear
        progress_modal = self.wait_for_element(chrome_driver, By.ID, "progress-modal")
        WebDriverWait(chrome_driver, 10).until(
            lambda driver: progress_modal.is_displayed()
        )

        # Check progress text over time - should never be NaN%
        start_time = time.time()
        nan_found = False
        progress_values = []

        while time.time() - start_time < 3:  # Monitor for 3 seconds
            try:
                progress_element = chrome_driver.find_element(
                    By.ID, "progress-percentage"
                )
                text = progress_element.text
                progress_values.append(text)

                # Main test: should never show NaN%
                if "NaN%" in text:
                    nan_found = True
                    break

                # Should show either "Processing..." or a valid percentage
                assert text == "Processing..." or (
                    text.endswith("%") and text[:-1].replace(".", "").isdigit()
                ), f"Invalid progress text: {text}"

            except Exception as e:
                # Progress element might disappear if request completes quickly
                progress_values.append(f"Exception: {e!s}")

            time.sleep(0.5)

        print(f"Progress values observed: {progress_values}")
        assert not nan_found, f"Found NaN% in progress values: {progress_values}"
        assert len(progress_values) > 0, "No progress values were observed"

    @pytest.mark.selenium
    def test_form_submission_shows_progress(self, chrome_driver, app_url):
        """Test that form submission shows progress modal with correct text."""
        chrome_driver.get(f"{app_url}/form")

        # Fill required form fields
        form_fields = {
            "ORGANIZATION_NAME": "Test Form Unit",
            "ORGANIZATION_STREET_ADDRESS": "123 Test Street",
            "ORGANIZATION_CITY_STATE_ZIP": "Test City, ST 12345",
            "OFFICE_SYMBOL": "TEST-UI",
            "AUTHOR": "UI Test Author",
            "RANK": "CPT",
            "BRANCH": "EN",
            "SUBJECT": "UI Test Form Memo",
            "MEMO_TEXT": "- This is a test memo from form submission\n- Testing UI behavior",
        }

        for field_id, value in form_fields.items():
            field = self.wait_for_element(chrome_driver, By.ID, field_id)
            field.clear()
            field.send_keys(value)

        # Submit the form
        submit_button = self.wait_for_clickable(
            chrome_driver,
            By.CSS_SELECTOR,
            "input[type='submit'], button[type='submit']",
        )
        submit_button.click()

        # Check that progress modal appears
        progress_modal = self.wait_for_element(chrome_driver, By.ID, "progress-modal")
        WebDriverWait(chrome_driver, 10).until(
            lambda driver: progress_modal.is_displayed()
        )

        # Verify progress text is reasonable
        progress_element = chrome_driver.find_element(By.ID, "progress-percentage")
        text = progress_element.text

        assert "NaN%" not in text, f"Form submission shows NaN%: {text}"
        assert text == "Processing..." or (
            text.endswith("%") and text[:-1].replace(".", "").isdigit()
        ), f"Invalid progress text from form: {text}"

    @pytest.mark.selenium
    def test_javascript_no_console_errors(self, chrome_driver, app_url):
        """Test that there are no JavaScript console errors on page load."""
        chrome_driver.get(app_url)

        # Wait for page to fully load
        self.wait_for_element(chrome_driver, By.ID, "editor")
        time.sleep(2)  # Give JS time to execute

        # Check browser console for JavaScript errors
        logs = chrome_driver.get_log("browser")
        js_errors = [
            log
            for log in logs
            if log["level"] == "SEVERE"
            and "javascript" in log.get("source", "").lower()
        ]

        # Filter out non-critical errors (like favicon 404s)
        critical_errors = []
        for error in js_errors:
            message = error.get("message", "").lower()
            if not any(ignore in message for ignore in ["favicon", "net::", "blocked"]):
                critical_errors.append(error)

        assert len(critical_errors) == 0, f"JavaScript errors found: {critical_errors}"

    @pytest.mark.selenium
    def test_navigation_between_pages(self, chrome_driver, app_url):
        """Test navigation between home and form pages works."""
        # Start at home page
        chrome_driver.get(app_url)
        time.sleep(1)  # Allow initial page to load completely
        editor = self.wait_for_element(chrome_driver, By.ID, "editor")
        assert editor.is_displayed()

        # Navigate to form page
        chrome_driver.get(f"{app_url}/form")
        form = self.wait_for_element(chrome_driver, By.ID, "memo")
        assert form.is_displayed()

        # Navigate back to home page
        chrome_driver.get(app_url)
        time.sleep(1)  # Allow page to load completely
        editor = self.wait_for_element(chrome_driver, By.ID, "editor")
        assert editor.is_displayed()

        # Check that both pages maintain their JavaScript functionality
        create_button = chrome_driver.find_element(By.ID, "start-bg-job")
        assert create_button.is_displayed()


if __name__ == "__main__":
    import subprocess

    subprocess.run(["uv", "run", "pytest", __file__, "-v", "-m", "selenium"])
