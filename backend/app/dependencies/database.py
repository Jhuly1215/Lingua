from app.db.session import get_db_session

# Re-export de la dependencia de sesión para un acceso centralizado
get_db = get_db_session
