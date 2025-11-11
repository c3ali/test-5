# backend/auth.py
"""
Gestion de l'authentification JWT
- Hashage et vérification des mots de passe
- Création et validation des tokens JWT
- Décorateur de protection des routes
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
import os

# Configuration (utiliser des variables d'environnement en production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "votre-clé-secrète-très-sécurisée-changez-moi-en-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# =============================================================================
# Gestion des mots de passe
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash un mot de passe en utilisant bcrypt.
    
    Args:
        password: Le mot de passe en clair
        
    Returns:
        Le mot de passe hashé avec le salt
    """
    # Génère un salt et hash le mot de passe
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe correspond à son hash.
    
    Args:
        plain_password: Le mot de passe en clair
        hashed_password: Le mot de passe hashé
        
    Returns:
        True si le mot de passe est correct, False sinon
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

# =============================================================================
# Gestion des tokens JWT
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT d'accès.
    
    Args:
        data: Données à encoder dans le token (ex: {"sub": user_id})
        expires_delta: Durée de validité optionnelle (par défaut 30 min)
        
    Returns:
        Le token JWT encodé
    """
    to_encode = data.copy()
    
    # Calcul de la date d'expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Ajout de l'expiration et d'informations standard
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # Encodage du token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Vérifie et décode un token JWT.
    
    Args:
        token: Le token JWT à vérifier
        
    Returns:
        Les données décodées si le token est valide, None sinon
    """
    try:
        # Décodage et vérification du token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except jwt.ExpiredSignatureError:
        # Le token a expiré
        return None
    
    except jwt.InvalidTokenError:
        # Token invalide (signature, format, etc.)
        return None

def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode un token sans vérifier sa signature (utile pour le debug).
    Attention : N'utilisez pas en production !
    
    Args:
        token: Le token JWT
        
    Returns:
        Les données décodées sans vérification
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.InvalidTokenError:
        return None

# =============================================================================
# Décorateur de protection pour Flask
# =============================================================================

def login_required(f):
    """
    Décorateur pour protéger les routes Flask.
    Vérifie le token JWT dans l'en-tête Authorization.
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return jsonify({"msg": "Accès autorisé", "user": g.user})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Récupération du token depuis l'en-tête Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                "error": "Token manquant",
                "msg": "Un token d'authentification est requis"
            }), 401
        
        # Vérification du token
        payload = verify_token(token)
        if not payload:
            return jsonify({
                "error": "Token invalide",
                "msg": "Le token est invalide ou a expiré"
            }), 401
        
        # Stockage des infos utilisateur dans le contexte
        g.user = payload
        g.user_id = payload.get('sub')
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Récupère l'utilisateur courant depuis le contexte Flask.
    Doit être utilisé avec @login_required.
    
    Returns:
        Les données de l'utilisateur ou None
    """
    from flask import g
    return getattr(g, 'user', None)

# =============================================================================
# Exemples d'utilisation
# =============================================================================

"""
Exemple d'utilisation avec Flask :

from flask import Flask, request, jsonify
from .auth import (
    hash_password, verify_password, create_access_token,
    verify_token, login_required, get_current_user
)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Hash du mot de passe
    hashed_pwd = hash_password(password)
    
    # Sauvegarde en base de données...
    # user = User(username=username, password=hashed_pwd)
    # db.session.add(user)
    # db.session.commit()
    
    return jsonify({"msg": "Utilisateur créé"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Récupération de l'utilisateur depuis la base de données
    # user = User.query.filter_by(username=username).first()
    
    # if user and verify_password(password, user.password):
    #     token = create_access_token({"sub": user.id, "username": user.username})
    #     return jsonify({"access_token": token, "token_type": "bearer"})
    
    return jsonify({"error": "Identifiants invalides"}), 401

@app.route('/protected')
@login_required
def protected():
    user = get_current_user()
    return jsonify({
        "msg": "Accès autorisé",
        "user_id": user.get('sub'),
        "username": user.get('username')
    })

@app.route('/verify-token', methods=['POST'])
def verify_token_route():
    token = request.json.get('token')
    payload = verify_token(token)
    if payload:
        return jsonify({"valid": True, "payload": payload})
    return jsonify({"valid": False, "msg": "Token invalide"}), 401
"""

# =============================================================================
# Tests unitaires
# =============================================================================

def test_auth_functions():
    """Tests basiques des fonctions d'authentification"""
    print("🧪 Tests d'authentification...")
    
    # Test hashage mot de passe
    pwd = "monSuperMotDePasse123!"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed), "❌ La vérification du mot de passe a échoué"
    assert not verify_password("mauvais_mdp", hashed), "❌ La vérification ne devrait pas réussir"
    print("✅ Hashage et vérification des mots de passe : OK")
    
    # Test création et vérification de token
    user_data = {"sub": "123", "username": "testuser", "role": "admin"}
    token = create_access_token(user_data)
    assert token is not None, "❌ La création du token a échoué"
    print(f"✅ Token créé : {token[:50]}...")
    
    # Test vérification valide
    decoded = verify_token(token)
    assert decoded is not None, "❌ La vérification du token valide a échoué"
    assert decoded["sub"] == "123", "❌ Données du token incorrectes"
    print("✅ Vérification du token valide : OK")
    
    # Test token expiré
    expired_token = create_access_token(
        user_data,
        expires_delta=timedelta(seconds=-1)
    )
    decoded_expired = verify_token(expired_token)
    assert decoded_expired is None, "❌ Le token expiré ne devrait pas être valide"
    print("✅ Vérification du token expiré : OK")
    
    # Test token invalide
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.payload"
    decoded_fake = verify_token(fake_token)
    assert decoded_fake is None, "❌ Le token invalide ne devrait pas être valide"
    print("✅ Vérification du token invalide : OK")
    
    print("🎉 Tous les tests ont réussi !")

if __name__ == "__main__":
    test_auth_functions()