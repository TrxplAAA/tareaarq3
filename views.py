import time
import uuid
from flask import request, jsonify, g
from models import db, Admin, Company, Location, Sensor, SensorData

def setup_routes(app):

    @app.before_request
    def before_request():
        g.admin_authenticated = False
        auth = request.authorization
        if auth:
            g.admin_authenticated = Admin.verify_credentials(auth.username, auth.password)

    def requires_auth(f):
        def decorated(*args, **kwargs):
            if not g.admin_authenticated:
                return jsonify({"error": "Autenticación requerida"}), 401
            return f(*args, **kwargs)
        decorated.__name__ = f.__name__
        return decorated

    @app.route('/api/v1/admin/login', methods=['POST'])
    def admin_login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if Admin.verify_credentials(username, password):
            return jsonify({"message": "Inicio de sesión exitoso"}), 200
        return jsonify({"error": "Credenciales inválidas"}), 401

    @app.route('/api/v1/companies', methods=['POST'])
    @requires_auth
    def create_company():
        data = request.get_json()
        company_api_key = str(uuid.uuid4())  # Generar una API key única
        new_company = Company(company_name=data['company_name'], company_api_key=company_api_key)
        db.session.add(new_company)
        db.session.commit()
        return jsonify({"message": "Compañía creada", "company_api_key": company_api_key}), 201

    @app.route('/api/v1/locations', methods=['POST'])
    @requires_auth
    def create_location():
        data = request.get_json()
        new_location = Location(
            company_id=data['company_id'],
            location_name=data['location_name'],
            location_country=data['location_country'],
            location_city=data['location_city'],
            location_meta=data['location_meta']
        )
        db.session.add(new_location)
        db.session.commit()
        return jsonify({"message": "Ubicación creada"}), 201

    @app.route('/api/v1/sensors', methods=['POST'])
    @requires_auth
    def create_sensor():
        data = request.get_json()
        sensor_api_key = str(uuid.uuid4())  # Generar una API key única
        new_sensor = Sensor(
            location_id=data['location_id'],
            sensor_name=data['sensor_name'],
            sensor_category=data['sensor_category'],
            sensor_meta=data['sensor_meta'],
            sensor_api_key=sensor_api_key
        )
        db.session.add(new_sensor)
        db.session.commit()
        return jsonify({"message": "Sensor creado", "sensor_api_key": sensor_api_key}), 201

    @app.route('/api/v1/sensor_data', methods=['POST'])
    def create_sensor_data():
        data = request.get_json()
        api_key = data['api_key']
        sensor = Sensor.query.filter_by(sensor_api_key=api_key).first()
        if not sensor:
            return jsonify({"error": "API key inválida"}), 400
        for measurement in data['json_data']:
            new_data = SensorData(sensor_id=sensor.id, json_data=measurement, timestamp=int(time.time()))
            db.session.add(new_data)
        db.session.commit()
        return jsonify({"message": "Datos del sensor creados"}), 201

    @app.route('/api/v1/sensor_data', methods=['GET'])
    def get_sensor_data():
        company_api_key = request.args.get('company_api_key')
        from_timestamp = request.args.get('from')
        to_timestamp = request.args.get('to')
        sensor_ids_param = request.args.get('sensor_id')

        if not company_api_key or not from_timestamp or not to_timestamp or not sensor_ids_param:
            return jsonify({"error": "Parámetros faltantes"}), 400

        # Verificar si la company_api_key es válida
        company = Company.query.filter_by(company_api_key=company_api_key).first()
        if not company:
            return jsonify({"error": "API key de la compañía inválida"}), 400

        # Convertir los IDs de los sensores a enteros
        try:
            sensor_ids = [int(sid) for sid in sensor_ids_param.split(',')]
        except ValueError:
            return jsonify({"error": "Parámetro sensor_id inválido"}), 400

        # Obtener los sensores existentes
        existing_sensors = Sensor.query.filter(Sensor.id.in_(sensor_ids)).all()
        existing_sensor_ids = [sensor.id for sensor in existing_sensors]

        # Identificar los sensores no existentes
        non_existing_sensor_ids = list(set(sensor_ids) - set(existing_sensor_ids))

        data = SensorData.query.filter(SensorData.timestamp >= from_timestamp,
                                       SensorData.timestamp <= to_timestamp,
                                       SensorData.sensor_id.in_(existing_sensor_ids)).all()

        results = [{"sensor_id": d.sensor_id, "json_data": d.json_data, "timestamp": d.timestamp} for d in data]

        response = {"data": results}
        if non_existing_sensor_ids:
            response["sensores_no_existentes"] = non_existing_sensor_ids

        return jsonify(response), 200

    # Endpoints estándar para Location (GET, PUT, DELETE)
    @app.route('/api/v1/locations', methods=['GET'])
    def get_locations():
        company_api_key = request.args.get('company_api_key')
        if not company_api_key:
            return jsonify({"error": "Falta company_api_key"}), 400
        locations = Location.query.all()
        return jsonify([{"id": loc.id, "company_id": loc.company_id, "location_name": loc.location_name,
                         "location_country": loc.location_country, "location_city": loc.location_city,
                         "location_meta": loc.location_meta} for loc in locations]), 200

    @app.route('/api/v1/locations/<int:id>', methods=['GET'])
    def get_location(id):
        company_api_key = request.args.get('company_api_key')
        if not company_api_key:
            return jsonify({"error": "Falta company_api_key"}), 400
        location = Location.query.get(id)
        if not location:
            return jsonify({"error": "Ubicación no encontrada"}), 404
        return jsonify({"id": location.id, "company_id": location.company_id, "location_name": location.location_name,
                        "location_country": location.location_country, "location_city": location.location_city,
                        "location_meta": location.location_meta}), 200

    @app.route('/api/v1/locations/<int:id>', methods=['PUT'])
    @requires_auth
    def update_location(id):
        data = request.get_json()
        location = Location.query.get(id)
        if not location:
            return jsonify({"error": "Ubicación no encontrada"}), 404
        location.location_name = data.get('location_name', location.location_name)
        location.location_country = data.get('location_country', location.location_country)
        location.location_city = data.get('location_city', location.location_city)
        location.location_meta = data.get('location_meta', location.location_meta)
        db.session.commit()
        return jsonify({"message": "Ubicación actualizada"}), 200

    @app.route('/api/v1/locations/<int:id>', methods=['DELETE'])
    @requires_auth
    def delete_location(id):
        location = Location.query.get(id)
        if not location:
            return jsonify({"error": "Ubicación no encontrada"}), 404
        db.session.delete(location)
        db.session.commit()
        return jsonify({"message": "Ubicación eliminada"}), 200

    # Endpoints estándar para Sensor (GET, PUT, DELETE)
    @app.route('/api/v1/sensors', methods=['GET'])
    def get_sensors():
        company_api_key = request.args.get('company_api_key')
        if not company_api_key:
            return jsonify({"error": "Falta company_api_key"}), 400
        sensors = Sensor.query.all()
        return jsonify([{"id": sen.id, "location_id": sen.location_id, "sensor_name": sen.sensor_name,
                         "sensor_category": sen.sensor_category, "sensor_meta": sen.sensor_meta,
                         "sensor_api_key": sen.sensor_api_key} for sen in sensors]), 200

    @app.route('/api/v1/sensors/<int:id>', methods=['GET'])
    def get_sensor(id):
        company_api_key = request.args.get('company_api_key')
        if not company_api_key:
            return jsonify({"error": "Falta company_api_key"}), 400
        sensor = Sensor.query.get(id)
        if not sensor:
            return jsonify({"error": "Sensor no encontrado"}), 404
        return jsonify({"id": sensor.id, "location_id": sensor.location_id, "sensor_name": sensor.sensor_name,
                        "sensor_category": sensor.sensor_category, "sensor_meta": sensor.sensor_meta,
                        "sensor_api_key": sensor.sensor_api_key}), 200

    @app.route('/api/v1/sensors/<int:id>', methods=['PUT'])
    @requires_auth
    def update_sensor(id):
        data = request.get_json()
        sensor = Sensor.query.get(id)
        if not sensor:
            return jsonify({"error": "Sensor no encontrado"}), 404
        sensor.sensor_name = data.get('sensor_name', sensor.sensor_name)
        sensor.sensor_category = data.get('sensor_category', sensor.sensor_category)
        sensor.sensor_meta = data.get('sensor_meta', sensor.sensor_meta)
        db.session.commit()
        return jsonify({"message": "Sensor actualizado"}), 200

    @app.route('/api/v1/sensors/<int:id>', methods=['DELETE'])
    @requires_auth
    def delete_sensor(id):
        sensor = Sensor.query.get(id)
        if not sensor:
            return jsonify({"error": "Sensor no encontrado"}), 404
        db.session.delete(sensor)
        db.session.commit()
        return jsonify({"message": "Sensor eliminado"}), 200

    # Endpoints estándar para SensorData (GET, DELETE)
    @app.route('/api/v1/sensor_data/<int:id>', methods=['GET'])
    def get_sensor_data_by_id(id):
        company_api_key = request.args.get('company_api_key')
        if not company_api_key:
            return jsonify({"error": "Falta company_api_key"}), 400
        sensor_data = SensorData.query.get(id)
        if not sensor_data:
            return jsonify({"error": "Datos del sensor no encontrados"}), 404
        return jsonify({"id": sensor_data.id, "sensor_id": sensor_data.sensor_id, "json_data": sensor_data.json_data,
                        "timestamp": sensor_data.timestamp}), 200

    @app.route('/api/v1/sensor_data/<int:id>', methods=['DELETE'])
    @requires_auth
    def delete_sensor_data(id):
        company_api_key = request.args.get('company_api_key')
        if not company_api_key:
            return jsonify({"error": "Falta company_api_key"}), 400
        sensor_data = SensorData.query.get(id)
        if not sensor_data:
            return jsonify({"error": "Datos del sensor no encontrados"}), 404
        db.session.delete(sensor_data)
        db.session.commit()
        return jsonify({"message": "Datos del sensor eliminados"}), 200
