# backend/database.py
"""
Configuration SQLAlchemy et gestion de la connexion à la base de données.
Supporte SQLite (par défaut) et PostgreSQL via DATABASE_URL.
Fournit le moteur, la session et la base pour les modèles SQLAlchemy.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from backend.core.config import settings

# --- Configuration de la base de données ---

# Utilise DATABASE_URL de config.py (SQLite par défaut, PostgreSQL si configuré)
DATABASE_URL = settings.DATABASE_URL

# --- Création du moteur SQLAlchemy ---

# Configuration adaptée selon le type de base de données
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite nécessite check_same_thread=False pour FastAPI
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    # Vérifie la connexion avant chaque requête (évite les erreurs de connexion inactives)
    pool_pre_ping=True,
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