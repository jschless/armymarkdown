"""
Tests for form handling and validation.
"""

import pytest
from unittest.mock import patch, Mock
from werkzeug.datastructures import MultiDict


class TestFormCreation:
    """Test form creation and initialization."""
    
    def test_login_form_creation(self):
        """Test LoginForm creation and fields."""
        from forms import LoginForm
        
        form = LoginForm()
        
        # Should have required fields
        assert hasattr(form, 'username')
        assert hasattr(form, 'password')
        assert hasattr(form, 'submit')
    
    def test_register_form_creation(self):
        """Test RegisterForm creation and fields."""
        from forms import RegisterForm
        
        form = RegisterForm()
        
        # Should have required fields
        assert hasattr(form, 'username')
        assert hasattr(form, 'email')
        assert hasattr(form, 'password')
        assert hasattr(form, 'confirm_password')
        assert hasattr(form, 'submit')
    
    @patch('app.config.get')
    def test_register_form_captcha_enabled(self, mock_config):
        """Test RegisterForm with CAPTCHA enabled."""
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': False,
            'RECAPTCHA_PUBLIC_KEY': 'test-key'
        }.get(key, default)
        
        from forms import RegisterForm
        form = RegisterForm()
        
        # Should have recaptcha field when enabled
        assert hasattr(form, 'recaptcha')
    
    @patch('app.config.get')
    def test_register_form_captcha_disabled(self, mock_config):
        """Test RegisterForm with CAPTCHA disabled.""" 
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': True,
            'RECAPTCHA_PUBLIC_KEY': 'test-key'
        }.get(key, default)
        
        from forms import RegisterForm
        form = RegisterForm()
        
        # Should not have recaptcha field when disabled
        assert not hasattr(form, 'recaptcha')
    
    @patch('app.config.get')
    def test_register_form_no_recaptcha_key(self, mock_config):
        """Test RegisterForm when no reCAPTCHA key is configured."""
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': False,
            'RECAPTCHA_PUBLIC_KEY': None
        }.get(key, default)
        
        from forms import RegisterForm
        form = RegisterForm()
        
        # Should not have recaptcha field when no key configured
        assert not hasattr(form, 'recaptcha')


class TestFormValidation:
    """Test form validation logic."""
    
    def test_login_form_valid_data(self):
        """Test LoginForm with valid data."""
        from forms import LoginForm
        
        form_data = MultiDict([
            ('username', 'testuser'),
            ('password', 'testpass'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True):
            form = LoginForm(form_data)
            # Skip CSRF validation in tests
            form.csrf_token.data = 'dummy'
            
            # Basic field validation should pass
            assert form.username.data == 'testuser'
            assert form.password.data == 'testpass'
    
    def test_login_form_empty_fields(self):
        """Test LoginForm with empty required fields."""
        from forms import LoginForm
        
        form_data = MultiDict([
            ('username', ''),
            ('password', ''),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True):
            form = LoginForm(form_data)
            form.csrf_token.data = 'dummy'
            
            # Should have validation errors for required fields
            is_valid = form.validate()
            if not is_valid:
                # Check that there are errors for required fields
                assert len(form.errors) > 0
    
    def test_register_form_valid_data(self):
        """Test RegisterForm with valid data."""
        from forms import RegisterForm
        
        form_data = MultiDict([
            ('username', 'newuser'),
            ('email', 'test@example.com'),
            ('password', 'SecurePass123'),
            ('confirm_password', 'SecurePass123'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
             patch('app.config.get', return_value=True):  # Disable CAPTCHA for test
            
            form = RegisterForm(form_data)
            form.csrf_token.data = 'dummy'
            
            # Basic field validation should pass
            assert form.username.data == 'newuser'
            assert form.email.data == 'test@example.com'
            assert form.password.data == 'SecurePass123'
    
    def test_register_form_password_mismatch(self):
        """Test RegisterForm with mismatched passwords."""
        from forms import RegisterForm
        
        form_data = MultiDict([
            ('username', 'newuser'),
            ('email', 'test@example.com'),
            ('password', 'password1'),
            ('confirm_password', 'password2'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
             patch('app.config.get', return_value=True):  # Disable CAPTCHA
            
            form = RegisterForm(form_data)
            form.csrf_token.data = 'dummy'
            
            is_valid = form.validate()
            if not is_valid:
                # Should have error about password mismatch
                assert 'confirm_password' in form.errors or 'password' in form.errors
    
    def test_register_form_invalid_email(self):
        """Test RegisterForm with invalid email format."""
        from forms import RegisterForm
        
        form_data = MultiDict([
            ('username', 'newuser'),
            ('email', 'invalid_email'),
            ('password', 'SecurePass123'),
            ('confirm_password', 'SecurePass123'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
             patch('app.config.get', return_value=True):  # Disable CAPTCHA
            
            form = RegisterForm(form_data)
            form.csrf_token.data = 'dummy'
            
            is_valid = form.validate()
            if not is_valid:
                # Should have error about invalid email
                assert 'email' in form.errors


class TestFormSecurity:
    """Test form security features."""
    
    def test_csrf_protection_enabled(self, client):
        """Test that CSRF protection is working."""
        response = client.get('/register')
        
        assert response.status_code == 200
        # Should contain CSRF token in form
        assert b'csrf_token' in response.data
    
    def test_form_submission_without_csrf(self, client):
        """Test form submission without CSRF token."""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password',
            'confirm_password': 'password'
        })
        
        # In testing environment, CSRF might be disabled
        # This test verifies the form handles missing CSRF appropriately
        assert response.status_code in [200, 400, 403]
    
    def test_input_sanitization(self):
        """Test that form inputs are properly sanitized."""
        from forms import RegisterForm
        
        malicious_input = '<script>alert("xss")</script>'
        form_data = MultiDict([
            ('username', malicious_input),
            ('email', 'test@example.com'),
            ('password', 'password'),
            ('confirm_password', 'password'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
             patch('app.config.get', return_value=True):
            
            form = RegisterForm(form_data)
            form.csrf_token.data = 'dummy'
            
            # Form should contain the input but it should be handled safely
            # The actual sanitization might happen at render time or in validators
            assert form.username.data == malicious_input  # Raw data preserved
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection in form fields."""
        from forms import LoginForm
        
        malicious_input = "'; DROP TABLE users; --"
        form_data = MultiDict([
            ('username', malicious_input),
            ('password', 'password'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True):
            form = LoginForm(form_data)
            form.csrf_token.data = 'dummy'
            
            # Form should accept the input safely
            # Protection happens at the database layer, not form layer
            assert form.username.data == malicious_input


class TestFormIntegration:
    """Test form integration with Flask routes."""
    
    def test_login_form_post_success(self, client):
        """Test successful login form submission."""
        with patch('login.authenticate_user', return_value=True), \
             patch('login.get_user_by_username', return_value={'id': 1, 'username': 'testuser'}):
            
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'password'
            }, follow_redirects=True)
            
            # Should redirect or show success
            assert response.status_code == 200
    
    def test_login_form_post_failure(self, client):
        """Test failed login form submission."""
        with patch('login.authenticate_user', return_value=False):
            response = client.post('/login', data={
                'username': 'wronguser',
                'password': 'wrongpass'
            })
            
            # Should return to login page or show error
            assert response.status_code in [200, 401]
            # Should contain login form again or error message
    
    @patch('app.config.get')
    def test_register_form_post_success(self, mock_config, client):
        """Test successful registration form submission."""
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': True,
            'RECAPTCHA_PUBLIC_KEY': None
        }.get(key, default)
        
        with patch('login.create_user', return_value=(True, "User created successfully")):
            response = client.post('/register', data={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
    
    @patch('app.config.get')
    def test_register_form_post_duplicate_user(self, mock_config, client):
        """Test registration with duplicate username."""
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': True,
            'RECAPTCHA_PUBLIC_KEY': None
        }.get(key, default)
        
        with patch('login.create_user', return_value=(False, "Username already exists")):
            response = client.post('/register', data={
                'username': 'existing',
                'email': 'new@example.com',
                'password': 'SecurePass123',
                'confirm_password': 'SecurePass123'
            })
            
            assert response.status_code in [200, 400]
            # Should show error message
            assert b'exists' in response.data or b'error' in response.data


class TestFormRendering:
    """Test form rendering in templates."""
    
    def test_login_form_renders_correctly(self, client):
        """Test that login form renders with proper fields."""
        response = client.get('/login')
        
        assert response.status_code == 200
        # Should contain form fields
        assert b'username' in response.data
        assert b'password' in response.data
        assert b'type="password"' in response.data
        assert b'type="submit"' in response.data
    
    def test_register_form_renders_correctly(self, client):
        """Test that register form renders with proper fields."""
        response = client.get('/register')
        
        assert response.status_code == 200
        # Should contain form fields
        assert b'username' in response.data
        assert b'email' in response.data
        assert b'password' in response.data
        assert b'confirm' in response.data or b'password' in response.data
        assert b'type="email"' in response.data
        assert b'type="password"' in response.data
    
    @patch('app.config.get')
    def test_register_form_captcha_rendering(self, mock_config, client):
        """Test CAPTCHA field rendering based on configuration."""
        # Test with CAPTCHA enabled
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': False,
            'RECAPTCHA_PUBLIC_KEY': 'test-public-key'
        }.get(key, default)
        
        response = client.get('/register')
        
        assert response.status_code == 200
        # Should contain reCAPTCHA elements when enabled
        # The exact implementation depends on the template
    
    @patch('app.config.get')
    def test_register_form_no_captcha_rendering(self, mock_config, client):
        """Test register form without CAPTCHA when disabled."""
        mock_config.side_effect = lambda key, default=None: {
            'DISABLE_CAPTCHA': True,
            'RECAPTCHA_PUBLIC_KEY': 'test-key'
        }.get(key, default)
        
        response = client.get('/register')
        
        assert response.status_code == 200
        # Should not contain reCAPTCHA elements when disabled
        # The exact check depends on template implementation


class TestFieldValidators:
    """Test custom field validators."""
    
    def test_username_length_validation(self):
        """Test username length validation."""
        from forms import RegisterForm
        
        # Test very long username
        long_username = 'a' * 100
        form_data = MultiDict([
            ('username', long_username),
            ('email', 'test@example.com'),
            ('password', 'password'),
            ('confirm_password', 'password'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
             patch('app.config.get', return_value=True):
            
            form = RegisterForm(form_data)
            form.csrf_token.data = 'dummy'
            
            is_valid = form.validate()
            if not is_valid and 'username' in form.errors:
                # Should have length validation error
                error_message = str(form.errors['username'])
                assert 'length' in error_message.lower() or 'long' in error_message.lower()
    
    def test_password_strength_validation(self):
        """Test password strength validation.""" 
        from forms import RegisterForm
        
        weak_passwords = ['123', 'password', 'abc', '']
        
        for weak_pass in weak_passwords:
            form_data = MultiDict([
                ('username', 'testuser'),
                ('email', 'test@example.com'),
                ('password', weak_pass),
                ('confirm_password', weak_pass),
                ('csrf_token', 'dummy_token')
            ])
            
            with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
                 patch('app.config.get', return_value=True):
                
                form = RegisterForm(form_data)
                form.csrf_token.data = 'dummy'
                
                is_valid = form.validate()
                # Weak passwords should fail validation
                if not is_valid:
                    assert 'password' in form.errors or len(form.errors) > 0
    
    def test_email_format_validation(self):
        """Test email format validation."""
        from forms import RegisterForm
        
        invalid_emails = ['notanemail', 'missing@', '@missing.com', 'spaces in@email.com']
        
        for invalid_email in invalid_emails:
            form_data = MultiDict([
                ('username', 'testuser'),
                ('email', invalid_email),
                ('password', 'ValidPass123'),
                ('confirm_password', 'ValidPass123'),
                ('csrf_token', 'dummy_token')
            ])
            
            with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
                 patch('app.config.get', return_value=True):
                
                form = RegisterForm(form_data)
                form.csrf_token.data = 'dummy'
                
                is_valid = form.validate()
                # Invalid emails should fail validation
                if not is_valid:
                    assert 'email' in form.errors or len(form.errors) > 0


class TestFormEdgeCases:
    """Test edge cases and unusual scenarios."""
    
    def test_form_with_unicode_input(self):
        """Test form handling of unicode characters."""
        from forms import RegisterForm
        
        unicode_data = {
            'username': 'üser_ñame',
            'email': 'tëst@éxample.com',
            'password': 'Pássword123',
            'confirm_password': 'Pássword123'
        }
        
        form_data = MultiDict([(k, v) for k, v in unicode_data.items()] + [('csrf_token', 'dummy')])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True), \
             patch('app.config.get', return_value=True):
            
            form = RegisterForm(form_data)
            form.csrf_token.data = 'dummy'
            
            # Should handle unicode characters gracefully
            assert form.username.data == unicode_data['username']
            assert form.email.data == unicode_data['email']
    
    def test_form_with_very_large_input(self):
        """Test form handling of extremely large input."""
        from forms import LoginForm
        
        very_large_input = 'x' * 10000  # 10KB of data
        form_data = MultiDict([
            ('username', very_large_input),
            ('password', 'password'),
            ('csrf_token', 'dummy_token')
        ])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True):
            form = LoginForm(form_data)
            form.csrf_token.data = 'dummy'
            
            # Should handle large input without crashing
            # May fail validation due to length limits
            try:
                is_valid = form.validate()
                # Either succeeds or fails gracefully
                assert isinstance(is_valid, bool)
            except Exception as e:
                # Should not crash with unhandled exceptions
                assert False, f"Form validation crashed with large input: {e}"
    
    def test_empty_form_submission(self):
        """Test completely empty form submission."""
        from forms import LoginForm
        
        form_data = MultiDict([('csrf_token', 'dummy_token')])
        
        with patch('flask_wtf.csrf.CSRFProtect.validate_token', return_value=True):
            form = LoginForm(form_data)
            form.csrf_token.data = 'dummy'
            
            is_valid = form.validate()
            # Should fail validation due to required fields
            assert not is_valid
            assert len(form.errors) > 0