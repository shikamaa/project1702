from flask import Flask
from os import getenv
from werkzeug.security import generate_password_hash

from database1702 import db
from routes import routes_bp, teacher_bp, admin_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = '1702school'
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL', 'postgresql://postgres:admin1702@db/1702school')

    db.init_app(app)

    app.register_blueprint(routes_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    return app

app = create_app()

with app.app_context():
    import models
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)