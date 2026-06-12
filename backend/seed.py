from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.domain import Domain
from app.services.auth_service import get_password_hash
from app.services.domain_service import DomainService

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(username="admin", hashed_password=get_password_hash("admin123"))
        db.add(new_admin)
        db.commit()
        print("Created admin user (admin / admin123)")

    # Check if we have domains
    domain_count = db.query(Domain).count()
    if domain_count == 0:
        d1 = Domain(url="https://google.com", name="Google Search")
        d2 = Domain(url="https://example.com", name="Example Website")
        db.add_all([d1, d2])
        db.commit()
        
        # Trigger sync to create websites.yml
        service = DomainService(db)
        service.trigger_prometheus_sync()
        print("Created initial sample domains and generated websites.yml")

    db.close()

if __name__ == "__main__":
    seed_data()
