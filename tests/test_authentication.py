"""
Tests for authentication and user management functionality.
"""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch, Mock
from werkzeug.security import generate_password_hash


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    @patch('login.get_user_by_username')
    @patch('login.check_password_hash')
    def test_authenticate_valid_user(self, mock_check_pass, mock_get_user):
        """Test authentication with valid credentials."""
        # Mock user data
        mock_get_user.return_value = {
            'id': 1,
            'username': 'testuser',
            'password_hash': 'hashed_password'
        }
        mock_check_pass.return_value = True
        
        from login import authenticate_user
        result = authenticate_user('testuser', 'correct_password')
        
        assert result is True
        mock_get_user.assert_called_once_with('testuser')
        mock_check_pass.assert_called_once()
    
    @patch('login.get_user_by_username')
    def test_authenticate_invalid_user(self, mock_get_user):
        """Test authentication with non-existent user."""
        mock_get_user.return_value = None
        
        from login import authenticate_user
        result = authenticate_user('nonexistent', 'password')
        
        assert result is False
        mock_get_user.assert_called_once_with('nonexistent')
    
    @patch('login.get_user_by_username') 
    @patch('login.check_password_hash')
    def test_authenticate_wrong_password(self, mock_check_pass, mock_get_user):
        """Test authentication with wrong password."""
        mock_get_user.return_value = {
            'id': 1,
            'username': 'testuser',
            'password_hash': 'hashed_password'
        }
        mock_check_pass.return_value = False
        
        from login import authenticate_user
        result = authenticate_user('testuser', 'wrong_password')
        
        assert result is False


class TestUserRegistration:
    """Test user registration functionality."""
    
    @patch('login.get_user_by_username')
    @patch('login.get_user_by_email')
    @patch('login.create_user_in_db')
    def test_create_user_success(self, mock_create_db, mock_get_email, mock_get_user):
        """Test successful user creation."""
        # Mock no existing user
        mock_get_user.return_value = None
        mock_get_email.return_value = None
        mock_create_db.return_value = True
        
        from login import create_user
        success, message = create_user('newuser', 'test@example.com', 'password123')
        
        assert success is True
        assert 'success' in message.lower() or 'created' in message.lower()
        mock_create_db.assert_called_once()
    
    @patch('login.get_user_by_username')
    def test_create_user_duplicate_username(self, mock_get_user):
        """Test user creation with duplicate username."""
        mock_get_user.return_value = {'id': 1, 'username': 'existing'}
        
        from login import create_user
        success, message = create_user('existing', 'new@example.com', 'password123')
        
        assert success is False
        assert 'username' in message.lower() and 'exists' in message.lower()
    
    @patch('login.get_user_by_username')
    @patch('login.get_user_by_email') 
    def test_create_user_duplicate_email(self, mock_get_email, mock_get_user):
        """Test user creation with duplicate email."""
        mock_get_user.return_value = None
        mock_get_email.return_value = {'id': 1, 'email': 'existing@example.com'}
        
        from login import create_user
        success, message = create_user('newuser', 'existing@example.com', 'password123')
        
        assert success is False
        assert 'email' in message.lower() and 'exists' in message.lower()
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        from werkzeug.security import generate_password_hash, check_password_hash
        
        password = 'test_password_123'
        hashed = generate_password_hash(password)
        
        assert hashed != password  # Should be hashed, not plain text
        assert check_password_hash(hashed, password) is True
        assert check_password_hash(hashed, 'wrong_password') is False


class TestSessionManagement:
    """Test user session management."""
    
    def test_login_session_creation(self, client):
        """Test that login creates proper session."""
        with patch('login.authenticate_user', return_value=True), \
             patch('login.get_user_by_username', return_value={'id': 1, 'username': 'testuser'}):
            
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'password'
            }, follow_redirects=True)
            
            # Check session was created
            with client.session_transaction() as sess:
                # Session should contain user info
                assert 'user_id' in sess or 'username' in sess
    
    def test_logout_session_cleanup(self, client):
        """Test that logout clears session."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        response = client.get('/logout', follow_redirects=True)
        
        # Check session was cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess
    
    def test_protected_route_access_logged_in(self, client):
        """Test access to protected routes when logged in."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        response = client.get('/history')
        
        # Should allow access
        assert response.status_code == 200
    
    def test_protected_route_access_not_logged_in(self, client):
        """Test access to protected routes when not logged in.""" 
        response = client.get('/history')
        
        # Should redirect to login or deny access
        assert response.status_code in [302, 401]


class TestDocumentManagement:
    """Test document saving and retrieval."""
    
    @patch('login.get_db_connection')
    def test_save_document_logged_in(self, mock_get_conn, client):
        """Test saving document when logged in."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        from login import save_document
        result = save_document("Test memo content")
        
        assert isinstance(result, str)
        # Should indicate success
        assert 'saved' in result.lower() or 'success' in result.lower()
    
    def test_save_document_not_logged_in(self, client):
        """Test saving document when not logged in."""
        from login import save_document
        result = save_document("Test memo content")
        
        assert isinstance(result, str)
        # Should indicate need to log in
        assert 'login' in result.lower() or 'not logged' in result.lower()
    
    @patch('login.get_db_connection')
    def test_get_user_documents(self, mock_get_conn):
        """Test retrieving user documents."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (1, 'Document 1', 'Content 1', '2024-01-01'),
            (2, 'Document 2', 'Content 2', '2024-01-02'),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        from login import get_user_documents
        docs = get_user_documents(1)
        
        assert isinstance(docs, list)
        assert len(docs) == 2
        assert docs[0][1] == 'Document 1'  # Title
    
    @patch('login.get_db_connection')
    def test_delete_user_document(self, mock_get_conn):
        """Test deleting user document."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        from login import delete_document
        result = delete_document(1, 123)  # user_id, doc_id
        
        assert isinstance(result, bool)
        mock_cursor.execute.assert_called()


class TestDatabaseOperations:
    """Test database operations for user management."""
    
    def test_database_initialization(self, test_database):
        """Test that database tables are created properly."""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()
        
        # Check users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None
        
        # Check documents table exists  
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_user_crud_operations(self, test_database):
        """Test Create, Read, Update, Delete operations for users."""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()
        
        # Create user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash) 
            VALUES (?, ?, ?)
        """, ('testuser', 'test@example.com', generate_password_hash('password')))
        conn.commit()
        
        # Read user
        cursor.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
        user = cursor.fetchone()
        assert user is not None
        assert user[1] == 'testuser'  # username column
        assert user[2] == 'test@example.com'  # email column
        
        # Update user
        cursor.execute("UPDATE users SET email = ? WHERE username = ?", 
                      ('newemail@example.com', 'testuser'))
        conn.commit()
        
        cursor.execute("SELECT email FROM users WHERE username = ?", ('testuser',))
        updated_user = cursor.fetchone()
        assert updated_user[0] == 'newemail@example.com'
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE username = ?", ('testuser',))
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", ('testuser',))
        deleted_user = cursor.fetchone()
        assert deleted_user is None
        
        conn.close()
    
    def test_document_crud_operations(self, test_database):
        """Test CRUD operations for documents."""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()
        
        # First create a user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash) 
            VALUES (?, ?, ?)
        """, ('testuser', 'test@example.com', generate_password_hash('password')))
        user_id = cursor.lastrowid
        
        # Create document
        cursor.execute("""
            INSERT INTO documents (user_id, title, content) 
            VALUES (?, ?, ?)
        """, (user_id, 'Test Document', 'Test content'))
        doc_id = cursor.lastrowid
        conn.commit()
        
        # Read document
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()
        assert doc is not None
        assert doc[2] == 'Test Document'  # title column
        assert doc[3] == 'Test content'   # content column
        
        # Read user's documents
        cursor.execute("SELECT * FROM documents WHERE user_id = ?", (user_id,))
        user_docs = cursor.fetchall()
        assert len(user_docs) >= 1
        
        # Update document
        cursor.execute("UPDATE documents SET title = ? WHERE id = ?", 
                      ('Updated Title', doc_id))
        conn.commit()
        
        cursor.execute("SELECT title FROM documents WHERE id = ?", (doc_id,))
        updated_doc = cursor.fetchone()
        assert updated_doc[0] == 'Updated Title'
        
        # Delete document
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        deleted_doc = cursor.fetchone()
        assert deleted_doc is None
        
        conn.close()


class TestInputValidation:
    """Test input validation and security."""
    
    def test_username_validation(self):
        """Test username validation rules."""
        from login import validate_username
        
        # Valid usernames
        assert validate_username('user123') is True
        assert validate_username('test_user') is True
        assert validate_username('valid-name') is True
        
        # Invalid usernames
        assert validate_username('') is False          # Empty
        assert validate_username('a' * 100) is False   # Too long
        assert validate_username('user@name') is False # Invalid characters
        assert validate_username('user space') is False # Spaces
    
    def test_email_validation(self):
        """Test email validation."""
        from login import validate_email
        
        # Valid emails
        assert validate_email('test@example.com') is True
        assert validate_email('user.name+tag@domain.co.uk') is True
        
        # Invalid emails
        assert validate_email('') is False
        assert validate_email('not_an_email') is False
        assert validate_email('missing@') is False
        assert validate_email('@missing.com') is False
    
    def test_password_strength_validation(self):
        """Test password strength requirements."""
        from login import validate_password_strength
        
        # Valid passwords
        assert validate_password_strength('StrongPass123!') is True
        assert validate_password_strength('MySecurePassword2024') is True
        
        # Invalid passwords
        assert validate_password_strength('') is False        # Empty
        assert validate_password_strength('short') is False   # Too short
        assert validate_password_strength('password') is False # Too common
        assert validate_password_strength('12345678') is False # Only numbers
    
    def test_sql_injection_prevention(self, test_database):
        """Test protection against SQL injection attacks.""" 
        conn = sqlite3.connect(test_database)
        
        # Try SQL injection in username
        malicious_username = "'; DROP TABLE users; --"
        
        from login import get_user_by_username
        
        # This should not break the database
        try:
            result = get_user_by_username(malicious_username)
            # Should return None (user not found) without error
            assert result is None
        except Exception as e:
            # Should not get SQL error
            assert 'syntax error' not in str(e).lower()
        
        # Verify users table still exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_xss_prevention_in_user_data(self):
        """Test XSS prevention in user data storage and retrieval."""
        malicious_content = '<script>alert("xss")</script>'
        
        from login import sanitize_user_input
        cleaned_content = sanitize_user_input(malicious_content)
        
        # Should escape or remove script tags
        assert '<script>' not in cleaned_content
        assert '&lt;script&gt;' in cleaned_content or 'script' not in cleaned_content


class TestErrorHandling:
    """Test error handling in authentication."""
    
    @patch('login.get_db_connection')
    def test_database_connection_error(self, mock_get_conn):
        """Test handling of database connection errors."""
        mock_get_conn.side_effect = sqlite3.Error("Database connection failed")
        
        from login import authenticate_user
        result = authenticate_user('testuser', 'password')
        
        # Should handle gracefully and return False
        assert result is False
    
    @patch('login.get_db_connection')
    def test_database_query_error(self, mock_get_conn):
        """Test handling of database query errors."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        from login import get_user_by_username
        result = get_user_by_username('testuser')
        
        # Should handle gracefully and return None
        assert result is None
    
    def test_concurrent_user_registration(self, test_database):
        """Test handling of concurrent user registration attempts."""
        # This is a simplified test - real concurrency testing would be more complex
        from login import create_user
        
        # Simulate race condition by creating same user twice quickly
        success1, msg1 = create_user('raceuser', 'race1@example.com', 'password')
        success2, msg2 = create_user('raceuser', 'race2@example.com', 'password')
        
        # One should succeed, one should fail
        assert success1 != success2  # One True, one False
        if not success1:
            assert 'username' in msg1.lower() and 'exists' in msg1.lower()
        if not success2:
            assert 'username' in msg2.lower() and 'exists' in msg2.lower()