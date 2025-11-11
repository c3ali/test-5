# backend/alembic/env.py
"""Configuration d'Alembic pour les migrations de base de données."""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ajout du chemin du projet pour importer les modules backend
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import de la configuration et des modèles
from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import *  # noqa: E402, F403

# Configuration des logs
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# Métadonnées des modèles pour la génération automatique des migrations
target_metadata = Base.metadata


def get_database_url() -> str:
    """Récupère l'URL de la base de données depuis les settings."""
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    Exécute les migrations en mode 'offline' sans nécessiter de connexion DB.
    
    Cette configuration utilise une URL de base de données directe.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        # Pour PostgreSQL avec plusieurs schemas
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Exécute les migrations en mode 'online' avec une connexion active à la base.
    
    Cette configuration crée une connexion SQLAlchemy.
    """
    configuration = context.config.get_section(context.config.config_ini_section)
    if configuration is None:
        raise RuntimeError("Section de configuration Alembic introuvable")
    
    # Utilise l'URL de la base de données depuis les settings
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # Pour PostgreSQL avec plusieurs schemas
            include_schemas=True,
            # Optionnel : exclure certains schémas système
            # include_object=lambda obj, name, type_, reflected, compare_to: (
            #     obj.schema == "public" if type_ == "table" else True
            # ),
        )

        with context.begin_transaction():
            # Pour PostgreSQL : définir le schema de recherche si nécessaire
            # connection.execute("SET search_path TO public")
            context.run_migrations()


if __name__ == "__main__":
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
