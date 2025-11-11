# tests/test_users.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import du module à tester (à adapter selon votre structure)
# Exemples d'imports possibles :
# from app import users
# from models import users
# import users

# Supposons que le module users a ces fonctions typiques :
# - create_user(data)
# - get_user(user_id)
# - update_user(user_id, data)
# - delete_user(user_id)
# - list_users()
# - authenticate_user(username, password)

# Fixtures de test
@pytest.fixture
def mock_db():
    """Mock de la base de données"""
    return MagicMock()

@pytest.fixture
def sample_user_data():
    """Données utilisateur valides"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'secure_password123',
        'first_name': 'Test',
        'last_name': 'User'
    }

@pytest.fixture
def sample_user_db():
    """Représentation d'un utilisateur en base de données"""
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lewv8iY0L9fG1JZZm',  # hash de 'secure_password123'
        'first_name': 'Test',
        'last_name': 'User',
        'created_at': datetime(2023, 1, 1, 12, 0, 0),
        'is_active': True
    }

@pytest.fixture
def sample_user_list():
    """Liste d'utilisateurs pour les tests de listing"""
    return [
        {'id': 1, 'username': 'user1', 'email': 'user1@example.com'},
        {'id': 2, 'username': 'user2', 'email': 'user2@example.com'},
        {'id': 3, 'username': 'user3', 'email': 'user3@example.com'}
    ]

# Tests pour create_user
class TestCreateUser:
    """Tests de la fonction create_user"""
    
    def test_create_user_success(self, mock_db, sample_user_data):
        """Test la création réussie d'un utilisateur"""
        # Arrange
        mock_db.insert.return_value = 1
        
        # Act
        user_id = users.create_user(sample_user_data, db=mock_db)
        
        # Assert
        mock_db.insert.assert_called_once()
        assert user_id == 1
    
    def test_create_user_missing_required_fields(self, mock_db, sample_user_data):
        """Test la création avec des champs obligatoires manquants"""
        # Arrange
        incomplete_data = sample_user_data.copy()
        del incomplete_data['username']
        
        # Act & Assert
        with pytest.raises(ValueError, match="Le champ 'username' est requis"):
            users.create_user(incomplete_data, db=mock_db)
    
    def test_create_user_invalid_email(self, mock_db, sample_user_data):
        """Test la création avec un email invalide"""
        # Arrange
        invalid_data = sample_user_data.copy()
        invalid_data['email'] = 'not-an-email'
        
        # Act & Assert
        with pytest.raises(ValueError, match="Format d'email invalide"):
            users.create_user(invalid_data, db=mock_db)
    
    def test_create_user_duplicate_username(self, mock_db, sample_user_data):
        """Test la création avec un nom d'utilisateur déjà existant"""
        # Arrange
        mock_db.find_one.return_value = {'username': 'testuser'}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Nom d'utilisateur déjà utilisé"):
            users.create_user(sample_user_data, db=mock_db)
        mock_db.find_one.assert_called_once_with('users', {'username': 'testuser'})

# Tests pour get_user
class TestGetUser:
    """Tests de la fonction get_user"""
    
    def test_get_user_success(self, mock_db, sample_user_db):
        """Test la récupération réussie d'un utilisateur"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        
        # Act
        user = users.get_user(1, db=mock_db)
        
        # Assert
        mock_db.find_one.assert_called_once_with('users', {'id': 1})
        assert user['id'] == 1
        assert user['username'] == 'testuser'
        assert user['email'] == 'test@example.com'
    
    def test_get_user_not_found(self, mock_db):
        """Test la récupération d'un utilisateur inexistant"""
        # Arrange
        mock_db.find_one.return_value = None
        
        # Act & Assert
        with pytest.raises(users.UserNotFoundError):
            users.get_user(999, db=mock_db)
    
    def test_get_user_inactive(self, mock_db, sample_user_db):
        """Test la récupération d'un utilisateur inactif"""
        # Arrange
        inactive_user = sample_user_db.copy()
        inactive_user['is_active'] = False
        mock_db.find_one.return_value = inactive_user
        
        # Act & Assert
        with pytest.raises(users.UserNotFoundError, match="Utilisateur inactif"):
            users.get_user(1, db=mock_db)

# Tests pour update_user
class TestUpdateUser:
    """Tests de la fonction update_user"""
    
    def test_update_user_success(self, mock_db, sample_user_db):
        """Test la mise à jour réussie d'un utilisateur"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        update_data = {'email': 'newemail@example.com', 'first_name': 'Updated'}
        
        # Act
        updated_user = users.update_user(1, update_data, db=mock_db)
        
        # Assert
        mock_db.update.assert_called_once()
        assert updated_user['email'] == 'newemail@example.com'
        assert updated_user['first_name'] == 'Updated'
    
    def test_update_user_not_found(self, mock_db):
        """Test la mise à jour d'un utilisateur inexistant"""
        # Arrange
        mock_db.find_one.return_value = None
        
        # Act & Assert
        with pytest.raises(users.UserNotFoundError):
            users.update_user(999, {'email': 'test@example.com'}, db=mock_db)
    
    def test_update_user_invalid_email(self, mock_db, sample_user_db):
        """Test la mise à jour avec un email invalide"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        
        # Act & Assert
        with pytest.raises(ValueError, match="Format d'email invalide"):
            users.update_user(1, {'email': 'invalid-email'}, db=mock_db)
    
    def test_update_user_duplicate_username(self, mock_db, sample_user_db):
        """Test la mise à jour avec un nom d'utilisateur déjà utilisé"""
        # Arrange
        mock_db.find_one.side_effect = [
            sample_user_db,  # Premier appel pour vérifier l'utilisateur existe
            {'username': 'existing_user'}  # Deuxième appel pour vérifier le username
        ]
        
        # Act & Assert
        with pytest.raises(ValueError, match="Nom d'utilisateur déjà utilisé"):
            users.update_user(1, {'username': 'existing_user'}, db=mock_db)

# Tests pour delete_user
class TestDeleteUser:
    """Tests de la fonction delete_user"""
    
    def test_delete_user_success(self, mock_db, sample_user_db):
        """Test la suppression réussie d'un utilisateur"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        
        # Act
        result = users.delete_user(1, db=mock_db)
        
        # Assert
        mock_db.delete.assert_called_once_with('users', {'id': 1})
        assert result is True
    
    def test_delete_user_not_found(self, mock_db):
        """Test la suppression d'un utilisateur inexistant"""
        # Arrange
        mock_db.find_one.return_value = None
        
        # Act & Assert
        with pytest.raises(users.UserNotFoundError):
            users.delete_user(999, db=mock_db)
    
    def test_delete_user_soft_delete(self, mock_db, sample_user_db):
        """Test la suppression logicielle (soft delete) d'un utilisateur"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        
        # Act
        result = users.delete_user(1, soft_delete=True, db=mock_db)
        
        # Assert
        mock_db.update.assert_called_once()
        call_args = mock_db.update.call_args[0]
        assert call_args[2]['is_active'] is False
        assert call_args[2]['deleted_at'] is not None

# Tests pour list_users
class TestListUsers:
    """Tests de la fonction list_users"""
    
    def test_list_users_success(self, mock_db, sample_user_list):
        """Test le listage réussi de tous les utilisateurs"""
        # Arrange
        mock_db.find_all.return_value = sample_user_list
        
        # Act
        users_list = users.list_users(db=mock_db)
        
        # Assert
        mock_db.find_all.assert_called_once_with('users')
        assert len(users_list) == 3
        assert users_list[0]['username'] == 'user1'
    
    def test_list_users_empty(self, mock_db):
        """Test le listage quand aucun utilisateur n'existe"""
        # Arrange
        mock_db.find_all.return_value = []
        
        # Act
        users_list = users.list_users(db=mock_db)
        
        # Assert
        assert users_list == []
    
    def test_list_users_with_filters(self, mock_db, sample_user_list):
        """Test le listage avec des filtres"""
        # Arrange
        mock_db.find_all.return_value = [sample_user_list[0]]
        
        # Act
        users_list = users.list_users(filters={'is_active': True}, db=mock_db)
        
        # Assert
        mock_db.find_all.assert_called_once_with('users', {'is_active': True})
        assert len(users_list) == 1

# Tests pour authenticate_user (si la fonction existe)
class TestAuthenticateUser:
    """Tests de la fonction authenticate_user"""
    
    def test_authenticate_user_success(self, mock_db, sample_user_db):
        """Test l'authentification réussie"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        with patch('users.bcrypt.checkpw', return_value=True):
            
            # Act
            user = users.authenticate_user('testuser', 'secure_password123', db=mock_db)
            
            # Assert
            assert user is not None
            assert user['id'] == 1
            assert user['username'] == 'testuser'
    
    def test_authenticate_user_not_found(self, mock_db):
        """Test l'authentification avec un utilisateur inexistant"""
        # Arrange
        mock_db.find_one.return_value = None
        
        # Act & Assert
        with pytest.raises(users.AuthenticationError, match="Utilisateur non trouvé"):
            users.authenticate_user('nonexistent', 'password', db=mock_db)
    
    def test_authenticate_user_wrong_password(self, mock_db, sample_user_db):
        """Test l'authentification avec un mot de passe incorrect"""
        # Arrange
        mock_db.find_one.return_value = sample_user_db
        with patch('users.bcrypt.checkpw', return_value=False):
            
            # Act & Assert
            with pytest.raises(users.AuthenticationError, match="Mot de passe incorrect"):
                users.authenticate_user('testuser', 'wrong_password', db=mock_db)
    
    def test_authenticate_user_inactive(self, mock_db, sample_user_db):
        """Test l'authentification avec un utilisateur inactif"""
        # Arrange
        inactive_user = sample_user_db.copy()
        inactive_user['is_active'] = False
        mock_db.find_one.return_value = inactive_user
        
        # Act & Assert
        with pytest.raises(users.AuthenticationError, match="Utilisateur inactif"):
            users.authenticate_user('testuser', 'password', db=mock_db)

# Tests de validation
class TestUserValidation:
    """Tests des fonctions de validation"""
    
    @pytest.mark.parametrize("email,expected", [
        ('test@example.com', True),
        ('user.name+tag@example.co.uk', True),
        ('invalid-email', False),
        ('@example.com', False),
        ('test@', False),
        ('', False),
    ])
    def test_validate_email(self, email, expected):
        """Test la validation d'email avec différents formats"""
        # Act
        result = users.validate_email(email)
        
        # Assert
        assert result == expected
    
    @pytest.mark.parametrize("password,expected", [
        ('short', False),
        ('no_digit', False),
        ('12345678', False),
        ('ValidPass123', True),
        ('anotherValid1', True),
    ])
    def test_validate_password(self, password, expected):
        """Test la validation de mot de passe"""
        # Act
        result = users.validate_password(password)
        
        # Assert
        assert result == expected

# Tests d'intégration (si vous avez une base de données de test)
@pytest.mark.integration
class TestUserIntegration:
    """Tests d'intégration avec une vraie base de données de test"""
    
    def test_full_user_lifecycle(self, test_db, sample_user_data):
        """Test le cycle de vie complet d'un utilisateur"""
        # Create
        user_id = users.create_user(sample_user_data, db=test_db)
        assert user_id > 0
        
        # Read
        user = users.get_user(user_id, db=test_db)
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        
        # Update
        users.update_user(user_id, {'first_name': 'Updated'}, db=test_db)
        updated_user = users.get_user(user_id, db=test_db)
        assert updated_user['first_name'] == 'Updated'
        
        # Delete
        users.delete_user(user_id, db=test_db)
        with pytest.raises(users.UserNotFoundError):
            users.get_user(user_id, db=test_db)

# Utilitaires pour les tests
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup et teardown automatique pour chaque test"""
    # Code exécuté avant chaque test
    yield
    # Code exécuté après chaque test
    # Par exemple, nettoyer la base de données

# Marqueurs personnalisés
def pytest_configure(config):
    """Enregistrer les marqueurs personnalisés"""
    config.addinivalue_line("markers", "integration: marque les tests d'intégration")
    config.addinivalue_line("markers", "unit: marque les tests unitaires")
```

## Instructions d'utilisation :

1. **Adaptez les imports** selon votre structure de projet :
   ```python
   from your_app.models import users
   # ou
   import users
   ```

2. **Créez les exceptions personnalisées** si nécessaire :
   ```python
   # Dans users.py
   class UserNotFoundError(Exception):
       pass
   
   class AuthenticationError(Exception):
       pass
   
   class ValidationError(Exception):
       pass
   ```

3. **Configurez les fixtures de base de données** :
   - Pour les tests unitaires : utilisez le mock `mock_db`
   - Pour les tests d'intégration : créez un `test_db` qui pointe vers une base de données de test

4. **Exécutez les tests** :
   ```bash
   # Tous les tests
   pytest tests/test_users.py -v
   
   # Uniquement les tests unitaires
   pytest tests/test_users.py -v -m "not integration"
   
   # Uniquement les tests d'intégration
   pytest tests/test_users.py -v -m "integration"
   
   # Avec couverture
   pytest tests/test_users.py --cov=users --cov-report=html
   ```

5. **Personnalisez selon votre implémentation** :
   - Modifiez les noms de fonctions si nécessaire
   - Ajoutez ou supprimez des tests selon les fonctionnalités de votre module
   - Adaptez la structure des données (champs, types, etc.)

Ce fichier de tests couvre les scénarios principaux : succès, erreurs, validation, et inclus des tests paramétrisés pour la validation des form