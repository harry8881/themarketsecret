from app import app, db

with app.app_context():
    print(db.engine.url)
