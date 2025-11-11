# backend/database.py
"""
Configuration SQLAlchemy et gestion de la connexion PostgreSQL.
Fournit le moteur, la session et la base pour les modèles SQLAlchemy.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from urllib.parse import quote_plus

# --- Configuration de la base de données ---

# Récupération des variables d'environnement (convention 12-factor app)
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "app_db")

def get_database_url() -> str:
    """
    Construit l'URL de connexion PostgreSQL avec encodage du mot de passe 
    pour gérer les caractères spéciaux de manière sécurisée.
    """
    encoded_password = quote_plus(DB_PASSWORD)
    return f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Création du moteur SQLAlchemy ---

engine = create_engine(
    get_database_url(),
    # Vérifie la connexion avant chaque requête (évite les erreurs de connexion inactives)
    pool_pre_ping=True,
    # Taille du pool de connexions
    pool_size=10,
    max_overflow=20,
    # Affiche les requêtes SQL en console (utile pour le développement)
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
)

# --- Configuration de la session ---

# Création de la factory de sessions (à utiliser dans toute l'application)
SessionLocal = sessionmaker(
    autocommit=False,      # Désactive l'autocommit pour gérer les transactions manuellement
    autoflush=False,       # Désactive l'autoflush pour plus de contrôle
    bind=engine,
    class_=Session
)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

# --- Gestion des dépendances ---

def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour obtenir une session de base de données.
    Gère automatiquement l'ouverture et la fermeture de la session.
    Usage : db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # En cas d'erreur, rollback pour garantir l'intégrité des données
        db.rollback()
        raise e
    finally:
        # Ferme la session dans tous les cas
        db.close()

def init_db() -> None:
    """
    Initialise la base de données en créant toutes les tables définies dans les modèles.
    À appeler au démarrage de l'application si vous utilisez SQLAlchemy pour gérer le schéma.
    """
    Base.metadata.create_all(bind=engine)