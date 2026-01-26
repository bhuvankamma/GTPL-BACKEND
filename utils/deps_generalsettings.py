import database_B

def get_db():
    if database_B.SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    db = database_B.SessionLocal()
    try:
        yield db
    finally:
        db.close()
