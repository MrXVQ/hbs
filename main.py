from app import app, db

# Check if database tables exist and create them if needed
def create_database_if_not_exists():
    with app.app_context():
        db.create_all()
        print("✔️  Database checked/created successfully!")

if __name__ == "__main__":
    create_database_if_not_exists()
    app.run(host="0.0.0.0", port=5000, debug=True)