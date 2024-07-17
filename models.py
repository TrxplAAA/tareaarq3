from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    username = db.Column(db.String, primary_key=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    @staticmethod
    def verify_credentials(username, password):
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            return True
        return False

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String, nullable=False)
    company_api_key = db.Column(db.String, unique=True, nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    location_name = db.Column(db.String, nullable=False)
    location_country = db.Column(db.String, nullable=False)
    location_city = db.Column(db.String, nullable=False)
    location_meta = db.Column(db.String, nullable=True)

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    sensor_name = db.Column(db.String, nullable=False)
    sensor_category = db.Column(db.String, nullable=False)
    sensor_meta = db.Column(db.String, nullable=True)
    sensor_api_key = db.Column(db.String, unique=True, nullable=False)

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)
    json_data = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)
