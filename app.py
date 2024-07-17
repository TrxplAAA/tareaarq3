from flask import Flask
from models import db, Admin
from views import setup_routes

def create_default_admin():
    # Crear un administrador por defecto si no existe
    if not Admin.query.first():
        admin = Admin(username='admin', password='admin1')
        db.session.add(admin)
        db.session.commit()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    create_default_admin()

setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
