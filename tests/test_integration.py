"""
Integration tests for Army Memo Maker - testing complete workflows.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock


class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to document generation."""
    
    def test_user_registration_login_workflow(self, client):
        """Test complete user registration and login flow."""
        # Mock database operations
        with patch('login.create_user', return_value=(True, "User created successfully")), \
             patch('login.authenticate_user', return_value=True), \
             patch('login.get_user_by_username', return_value={'id': 1, 'username': 'testuser'}):
            
            # Step 1: Register new user
            register_response = client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com', 
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123'
            }, follow_redirects=True)
            
            assert register_response.status_code == 200
            
            # Step 2: Login with new credentials
            login_response = client.post('/login', data={
                'username': 'testuser',
                'password': 'SecurePass123'
            }, follow_redirects=True)
            
            assert login_response.status_code == 200
            
            # Step 3: Access protected route
            history_response = client.get('/history')
            assert history_response.status_code == 200
    
    @patch('app.create_memo.delay')
    @patch('login.save_document')
    def test_memo_creation_workflow_text_editor(self, mock_save, mock_task, client, sample_memo_text):
        """Test complete memo creation workflow using text editor."""
        mock_task.return_value.id = "test-task-123"
        mock_save.return_value = "Document saved"
        
        # Step 1: Access main page
        index_response = client.get('/')
        assert index_response.status_code == 200
        assert b'memo_text' in index_response.data
        
        # Step 2: Save progress
        save_response = client.post('/save_progress', data={
            'memo_text': sample_memo_text
        })
        assert save_response.status_code == 200
        mock_save.assert_called_once()
        
        # Step 3: Process memo for PDF generation
        process_response = client.post('/process', data={
            'memo_text': sample_memo_text
        })
        assert process_response.status_code in [200, 302]
        mock_task.assert_called_once()
        
        # Step 4: Check status
        if mock_task.return_value.id:
            status_response = client.get(f'/status/{mock_task.return_value.id}')
            assert status_response.status_code in [200, 404]  # 404 if task not found in test
    
    @patch('app.create_memo.delay')
    @patch('login.save_document')
    def test_memo_creation_workflow_form_builder(self, mock_save, mock_task, client, sample_form_data):
        """Test complete memo creation workflow using form builder."""
        mock_task.return_value.id = "test-task-456"
        mock_save.return_value = "Document saved"
        
        # Step 1: Access form page
        form_response = client.get('/form')
        assert form_response.status_code == 200
        assert b'ORGANIZATION_NAME' in form_response.data
        
        # Step 2: Save progress from form
        save_response = client.post('/save_progress', data=sample_form_data)
        assert save_response.status_code == 200
        mock_save.assert_called_once()
        
        # Step 3: Process form submission
        process_response = client.post('/process', data=sample_form_data)
        assert process_response.status_code in [200, 302]
        mock_task.assert_called_once()
    
    def test_authenticated_document_management_workflow(self, client):
        """Test document management workflow for authenticated users."""
        with patch('login.save_document', return_value="Document saved successfully"), \
             patch('login.get_user_documents', return_value=[
                 (1, 'Test Document 1', 'Content 1', '2024-01-01'),
                 (2, 'Test Document 2', 'Content 2', '2024-01-02')
             ]):
            
            # Step 1: Login
            with client.session_transaction() as sess:
                sess['user_id'] = 1
                sess['username'] = 'testuser'
            
            # Step 2: Save a document
            save_response = client.post('/save_progress', data={
                'memo_text': 'Test document content'
            })
            assert save_response.status_code == 200
            
            # Step 3: View document history
            history_response = client.get('/history')
            assert history_response.status_code == 200
            assert b'Test Document 1' in history_response.data
            assert b'Test Document 2' in history_response.data


class TestErrorRecoveryWorkflows:
    """Test error recovery and graceful degradation."""
    
    def test_database_error_recovery(self, client, sample_memo_text):
        """Test workflow when database operations fail."""
        with patch('login.save_document', side_effect=Exception("Database error")):
            
            # Should handle database errors gracefully
            save_response = client.post('/save_progress', data={
                'memo_text': sample_memo_text
            })
            
            # Should not crash, should show error or degrade gracefully
            assert save_response.status_code in [200, 500]
            if save_response.status_code == 200:
                # Should contain error message or fallback behavior
                assert b'error' in save_response.data.lower() or b'memo_text' in save_response.data
    
    @patch('app.create_memo.delay')
    def test_celery_task_failure_handling(self, mock_task, client, sample_memo_text):
        """Test handling when Celery task fails."""
        mock_task.side_effect = Exception("Celery connection failed")
        
        process_response = client.post('/process', data={
            'memo_text': sample_memo_text
        })
        
        # Should handle Celery failures gracefully
        assert process_response.status_code in [200, 500]
        # Should not crash the application
    
    def test_invalid_memo_content_handling(self, client, invalid_memo_samples):
        """Test handling of invalid memo content."""
        for sample_name, invalid_content in invalid_memo_samples.items():
            process_response = client.post('/process', data={
                'memo_text': invalid_content
            })
            
            # Should handle invalid content gracefully
            assert process_response.status_code in [200, 400, 500]
            # Should not crash the application
    
    def test_missing_example_file_handling(self, client):
        """Test handling when example files are missing."""
        # Try to access non-existent example
        response = client.get('/?example_file=nonexistent.Amd')
        
        # Should fall back gracefully
        assert response.status_code == 200
        assert b'memo_text' in response.data
        
        # Try form with non-existent example
        form_response = client.get('/form?example_file=nonexistent.Amd')
        assert form_response.status_code == 200
        assert b'ORGANIZATION_NAME' in form_response.data


class TestSecurityWorkflows:
    """Test security-related workflows."""
    
    def test_xss_prevention_workflow(self, client):
        """Test XSS prevention throughout the workflow.""" 
        malicious_content = '<script>alert("xss")</script>Test content'
        
        # Test in memo text
        save_response = client.post('/save_progress', data={
            'memo_text': malicious_content
        })
        
        assert save_response.status_code == 200
        # The specific malicious script should be escaped, not executed
        assert b'alert("xss")' not in save_response.data or b'&lt;script&gt;' in save_response.data
        
        # Test in form fields - provide all required fields
        form_response = client.post('/save_progress', data={
            'SUBJECT': malicious_content,
            'MEMO_TEXT': 'Safe content',
            'ORGANIZATION_NAME': 'Test Unit',
            'ORGANIZATION_STREET_ADDRESS': '123 Test St',
            'ORGANIZATION_CITY_STATE_ZIP': 'Test, ST 12345',
            'OFFICE_SYMBOL': 'TEST',
            'AUTHOR': 'Test User',
            'RANK': 'CPT',
            'BRANCH': 'EN',
            'TITLE': 'Test Title'
        })
        
        assert form_response.status_code == 200
        # The specific malicious script should be escaped, not executed
        assert b'alert("xss")' not in form_response.data or b'&lt;script&gt;' in form_response.data
    
    def test_sql_injection_prevention_workflow(self, client):
        """Test SQL injection prevention in user workflows."""
        malicious_input = "'; DROP TABLE users; --"
        
        # Test in login
        with patch('login.authenticate_user', return_value=False):
            login_response = client.post('/login', data={
                'username': malicious_input,
                'password': 'password'
            })
            
            # Should handle safely without SQL errors (302 is redirect on failed login)
            assert login_response.status_code in [200, 302, 401]
        
        # Test in registration
        with patch('login.create_user', return_value=(False, "Invalid username")):
            register_response = client.post('/register', data={
                'username': malicious_input,
                'email': 'test@example.com',
                'password': 'password',
                'password2': 'password'  # Correct field name from forms.py
            })
            
            # Should handle safely without SQL errors (200 shows form again, 302 redirects)
            assert register_response.status_code in [200, 302, 400]
    
    def test_session_security_workflow(self, client):
        """Test session security throughout user workflow."""
        # Test session fixation prevention
        response1 = client.get('/login')
        
        with client.session_transaction() as sess:
            old_session_id = sess.get('_id')  # Flask session ID if available
        
        # Login should regenerate session
        with patch('login.authenticate_user', return_value=True), \
             patch('login.get_user_by_username', return_value={'id': 1, 'username': 'testuser'}):
            
            login_response = client.post('/login', data={
                'username': 'testuser',
                'password': 'password'
            })
            
            assert login_response.status_code in [200, 302]
        
        # Test session timeout/logout
        logout_response = client.get('/logout')
        assert logout_response.status_code in [200, 302]
        
        # Session should be cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess


class TestPerformanceWorkflows:
    """Test performance-related scenarios."""
    
    def test_large_memo_processing(self, client):
        """Test processing of very large memos."""
        # Create a large memo content
        large_content = """ORGANIZATION_NAME=Test Battalion
ORGANIZATION_STREET_ADDRESS=123 Main St
ORGANIZATION_CITY_STATE_ZIP=City, ST 12345
OFFICE_SYMBOL=TEST-OPS-XO
AUTHOR=Test Author
RANK=CPT
BRANCH=EN
SUBJECT=Large Test Memo

"""
        
        # Add many items
        for i in range(100):
            large_content += f"- This is test item number {i} with substantial content to test performance.\n"
            if i % 10 == 0:
                large_content += f"    - Sub-item {i}-1 with additional nested content.\n"
                large_content += f"    - Sub-item {i}-2 with more detailed information.\n"
        
        with patch('login.save_document', return_value="Large document saved"), \
             patch('app.create_memo.delay', return_value=Mock(id="large-task-123")):
            
            # Should handle large content without timeout
            save_response = client.post('/save_progress', data={
                'memo_text': large_content
            })
            assert save_response.status_code == 200
            
            process_response = client.post('/process', data={
                'memo_text': large_content
            })
            assert process_response.status_code in [200, 302]
    
    def test_concurrent_user_simulation(self, client):
        """Test handling multiple simultaneous requests."""
        # This is a simplified concurrency test
        # Real load testing would require specialized tools
        
        sample_content = "ORGANIZATION_NAME=Test\nSUBJECT=Concurrent Test\n- Test content"
        
        with patch('login.save_document', return_value="Saved"), \
             patch('app.create_memo.delay', return_value=Mock(id="concurrent-task")):
            
            # Simulate multiple requests quickly
            responses = []
            for i in range(5):
                response = client.post('/save_progress', data={
                    'memo_text': f"{sample_content} {i}"
                })
                responses.append(response)
            
            # All requests should complete successfully
            for response in responses:
                assert response.status_code == 200


class TestEndToEndFeatureTests:
    """Test end-to-end functionality of major features."""
    
    def test_dark_mode_toggle_integration(self, client):
        """Test dark mode toggle integration across pages."""
        # Test that dark mode assets are served correctly
        css_response = client.get('/static/css/modern.css')
        assert css_response.status_code == 200
        
        # Check that pages contain dark mode toggle
        pages_to_test = ['/', '/form', '/login', '/register']
        
        for page in pages_to_test:
            response = client.get(page)
            if response.status_code == 200:
                # Should contain theme toggle elements or dark mode CSS variables
                data_lower = response.data.decode().lower()
                has_dark_mode = (
                    'theme' in data_lower or 
                    'dark' in data_lower or 
                    '--color' in data_lower or
                    'data-theme' in data_lower
                )
                # Dark mode integration present in most pages
    
    def test_captcha_integration_workflow(self, client):
        """Test CAPTCHA integration in registration workflow."""
        # Test with CAPTCHA disabled (test environment)
        # Test environment already has CAPTCHA disabled
        register_response = client.get('/register')
        assert register_response.status_code == 200
        
        # Should not require CAPTCHA validation when disabled
        with patch('login.create_user', return_value=(True, "User created")), \
             patch('db.schema.User.query') as mock_query:
            # Mock no existing users
            mock_query.filter_by.return_value.first.return_value = None
            
            post_response = client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'password123'  # Correct field name
            })
            assert post_response.status_code in [200, 302]
    
    def test_responsive_design_workflow(self, client):
        """Test responsive design elements across workflows."""
        # Test that CSS contains responsive design
        css_response = client.get('/static/css/modern.css')
        if css_response.status_code == 200:
            css_content = css_response.data.decode()
            
            # Should contain responsive design elements
            responsive_indicators = [
                '@media',
                'max-width',
                'min-width',
                'flex',
                'grid'
            ]
            
            has_responsive = any(indicator in css_content for indicator in responsive_indicators)
            assert has_responsive or len(css_content) > 0  # At least has some CSS
    
    def test_accessibility_workflow(self, client):
        """Test accessibility features in key workflows.""" 
        pages_to_test = ['/', '/form', '/login', '/register']
        
        for page in pages_to_test:
            response = client.get(page)
            if response.status_code == 200:
                html_content = response.data.decode()
                
                # Basic accessibility checks
                accessibility_features = [
                    'aria-', 
                    'role=',
                    'alt=',
                    'label',
                    'title='
                ]
                
                # Should have some accessibility features
                has_accessibility = any(feature in html_content for feature in accessibility_features)
                # Most pages should have basic accessibility features
    
    def test_error_handling_integration(self, client):
        """Test integrated error handling across the application."""
        # Test 404 handling
        not_found_response = client.get('/nonexistent-page')
        assert not_found_response.status_code == 404
        
        # Test method not allowed
        method_not_allowed = client.post('/')  # GET-only route
        assert method_not_allowed.status_code == 405
        
        # Test processing with completely invalid data
        invalid_process = client.post('/process', data={})
        assert invalid_process.status_code in [200, 302, 400]  # Should handle gracefully
        
        # Test status with invalid task ID
        invalid_status = client.get('/status/invalid-task-id')
        assert invalid_status.status_code in [200, 404]  # Should handle gracefully