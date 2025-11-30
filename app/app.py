from flask import Flask
from os import getenv
from database1702 import db
from routes import routes_bp

app = Flask(__name__)
app.secret_key = '1702school'
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL', 'postgresql://postgres:admin1702@db/1702school')

app.register_blueprint(routes_bp, url_prefix='')

print("\n=== Registered endpoints ===")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")
print("===========================\n")

db.init_app(app)

with app.app_context():
    import models
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)