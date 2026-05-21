# app.py
import os
import logging
from logging.handlers import RotatingFileHandler
from routes.users.auth import verify_phone, verify_email
import click
from flask import Flask, redirect, url_for, request, session, jsonify, g
from flask_babel import Babel, gettext
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer
import json
from models import db, User, Order, DataProvider, Port, PremiumRequest
from models.user import Role
from routes.admin.routes import admin_bp
from routes.users.routes import users_bp
from routes.social import social_bp
from config import Config
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail, Message
from routes.users import root_bp
from extensions import mail, cache, limiter, babel
from datetime import datetime
import time

migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def get_locale():
    # اولویت ۱: زبان انتخاب‌شده توسط کاربر در session
    if 'lang' in session:
        return session['lang']

    # اولویت ۲: پارامتر URL (برای تغییرات لحظه‌ای)
    lang = request.args.get('lang')
    if lang and lang in ['fa', 'en']:
        session['lang'] = lang  # ذخیره برای جلسات بعدی
        return lang

    # اولویت ۳: زبان مرورگر
    return request.accept_languages.best_match(['fa', 'en'], 'fa')

def setup_logging(app):
    """Setup structured logging configuration for the application."""
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", '
            '"module": "%(module)s", "lineno": %(lineno)d}'
        ))
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
        ))
        console_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    else:
        logging.basicConfig(level=logging.INFO)
        app.logger.info('Application startup in development mode')


def setup_monitoring(app):
    """Setup monitoring endpoints and health checks."""
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'checks': {
                'database': 'ok',
                'redis': 'ok',
                'celery': 'ok'
            }
        }
        
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            health_status['checks']['database'] = 'ok'
        except Exception as e:
            health_status['checks']['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        try:
            cache.cache.set('_health_check', 'ok', timeout=5)
            result = cache.cache.get('_health_check')
            if result == 'ok':
                health_status['checks']['redis'] = 'ok'
            else:
                health_status['checks']['redis'] = 'error: connection failed'
        except Exception as e:
            health_status['checks']['redis'] = f'error: {str(e)}'
        
        try:
            from celery_app import celery
            inspect = celery.control.inspect(timeout=2)
            active_workers = inspect.active()
            if active_workers:
                health_status['checks']['celery'] = 'ok'
            else:
                health_status['checks']['celery'] = 'warning: no active workers'
        except Exception as e:
            health_status['checks']['celery'] = f'warning: {str(e)}'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    
    @app.route('/metrics')
    def metrics():
        """Metrics endpoint for Prometheus-style monitoring."""
        metrics_data = {
            'uptime_seconds': time.time() - app.config.get('START_TIME', time.time()),
            'active_users': User.query.filter_by(is_active=True).count() if 'User' in globals() else 0,
            'total_orders': Order.query.count() if 'Order' in globals() else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(metrics_data)
    
    @app.before_request
    def before_request_metrics():
        """Record request start time for metrics."""
        request.start_time = time.time()
    
    @app.after_request
    def after_request_metrics(response):
        """Log request duration and add headers."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response.headers['X-Response-Time'] = f'{duration:.4f}s'
            if duration > 1.0:
                app.logger.warning(f'Slow request: {request.method} {request.path} took {duration:.4f}s')
        return response


file_path = "/static/files/ports.json"
def load_ports_from_dataset(file_path):
    """Load ports data from JSON file and save to database."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        for key in data:
            name = data[key].get('port_name')
            country = data[key].get("country")
            latitude = data[key].get('lat')
            longitude = data[key].get('long')

            if not name or not country or latitude is None or longitude is None:
                print(f"Invalid data: {data[key]}")
                continue
                
            existing_port = Port.query.filter_by(name=name, country=country).first()
            if existing_port:
                print(f"Port already exists: {name}, {country}")
                continue
                
            new_port = Port(
                name=name,
                country=country,
                latitude=float(latitude),
                longitude=float(longitude)
            )
            db.session.add(new_port)
        
        db.session.commit()
        print("Ports loaded successfully!")
    except FileNotFoundError:
        print("Dataset file not found!")
    except json.JSONDecodeError:
        print("Invalid JSON format in dataset file!")
    except Exception as e:
        db.session.rollback()
        print(f"Error loading ports: {e}")



def get_serializer(app):
    """Create a URL-safe timed serializer instance."""
    return URLSafeTimedSerializer(app.secret_key)


def create_app():
   #app = Flask(__name__)
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    base_dir = os.path.abspath(os.path.dirname(__file__))
    trans_dir = os.path.join(base_dir, 'translations')

    # === Flask-Babel Setup (Compatible with v4.x) ===
    babel = Babel(app)
    app.config['BABEL_DEFAULT_LOCALE'] = 'fa_IR'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = trans_dir
    app.config['BABEL_SUPPORTED_LANGUAGES'] = ['fa_IR', 'en']

    # =============================================================================
    # ✅ CLI Command: Load Ports from JSON (با پشتیبانی از PostgreSQL)
    # =============================================================================
    from sqlalchemy.dialects.postgresql import insert as pg_insert  # ← این خط را اضافه کنید

    @app.cli.command("load-ports")
    @click.option('--file', '-f',
                  type=click.Path(exists=True, readable=True),
                  default=os.path.join(app.static_folder, 'files', 'ports.json'),
                  help='Path to ports JSON file')
    @click.option('--dry-run', is_flag=True, help='Show what would be inserted without saving')
    def load_ports_command(file, dry_run):
        """Load ports data from JSON file into PostgreSQL database."""
        with app.app_context():
            try:
                # Resolve absolute path
                if not os.path.isabs(file):
                    file = os.path.join(app.root_path, file.lstrip('/'))

                click.echo(f"📦 Loading ports from: {file}")

                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Pre-fetch existing ports for O(1) lookup (Case-insensitive)
                existing = {
                    (p.name.lower(), p.country.lower()): p.id
                    for p in Port.query.with_entities(Port.name, Port.country, Port.id).all()
                }

                ports_to_insert = []
                skipped = 0

                for key, item in data.items():
                    name = item.get('port_name')
                    country = item.get('country')
                    lat = item.get('lat')
                    lon = item.get('long')

                    if not all([name, country, lat is not None, lon is not None]):
                        click.echo(f"⚠️  Skipping invalid: {item}")
                        skipped += 1
                        continue

                    # Case-insensitive duplicate check in memory
                    if (name.lower(), country.lower()) in existing:
                        skipped += 1
                        continue

                    try:
                        ports_to_insert.append({
                            'name': name.strip(),
                            'country': country.strip(),
                            'latitude': float(lat),
                            'longitude': float(lon)
                        })
                    except (ValueError, TypeError) as e:
                        click.echo(f"⚠️  Invalid coordinates for {name}: {e}")
                        skipped += 1

                if dry_run:
                    click.echo(
                        f"🔍 DRY RUN: Would insert {len(ports_to_insert)} new ports, skip {skipped} existing/invalid")
                    for p in ports_to_insert[:5]:
                        click.echo(f"   • {p['name']}, {p['country']} ({p['latitude']}, {p['longitude']})")
                    if len(ports_to_insert) > 5:
                        click.echo(f"   ... and {len(ports_to_insert) - 5} more")
                    return

                if ports_to_insert:
                    # ✅ استفاده از ON CONFLICT DO NOTHING برای PostgreSQL
                    stmt = pg_insert(Port).values(ports_to_insert)
                    stmt = stmt.on_conflict_do_nothing(index_elements=['name', 'country'])

                    result = db.session.execute(stmt)
                    db.session.commit()

                    inserted = result.rowcount if result.rowcount is not None else len(ports_to_insert)
                    click.echo(click.style(
                        f"✅ Successfully inserted {inserted} ports (skipped {skipped} duplicates)",
                        fg='green'
                    ))
                else:
                    click.echo(click.style("ℹ️  No new ports to insert", fg='yellow'))

            except FileNotFoundError:
                click.echo(click.style(f"❌ File not found: {file}", fg='red'))
            except json.JSONDecodeError as e:
                click.echo(click.style(f"❌ Invalid JSON: {e}", fg='red'))
            except Exception as e:
                db.session.rollback()
                click.echo(click.style(f"❌ Error: {e}", fg='red'))
                raise



    def get_locale():
        if 'lang' in session:
            return session['lang']
        lang = request.args.get('lang')
        if lang:
            session['lang'] = lang
            return lang
        return request.accept_languages.best_match(['fa_IR', 'en'], 'fa_IR')

    babel.init_app(app, locale_selector=get_locale)

    # Inject _ function for translations in templates
    @app.context_processor
    def inject_babel_underscore():
        return {'_': gettext}
    # === End Babel Setup ===

    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    login_manager.login_view = 'users.login'
    login_manager.login_message = "Please log in."
    login_manager.init_app(app)
    
    mail.init_app(app)
    cache.init_app(app)
    
    if Config.RATELIMIT_ENABLED:
        limiter.init_app(app)
    
    setup_logging(app)
    setup_monitoring(app)

    # Inject translator from utils
    from utils.translations import translator
    @app.context_processor
    def inject_translator():
        return {'t': translator.t, 't_': translator.t}

    # ✅ Inject current_locale for all templates (FIXES UndefinedError)
    @app.context_processor
    def inject_current_locale():
        """Make current_locale available in all Jinja2 templates"""
        if 'lang' in session:
            return {'current_locale': session['lang']}
        lang = request.args.get('lang')
        if lang:
            return {'current_locale': lang}
        return {'current_locale': request.accept_languages.best_match(['fa_IR', 'en'], 'fa_IR')}

    @app.context_processor
    def inject_roles():
        return {'Role': Role}

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.magazine import magazine_bp
    from routes.exhibition import exhibition_bp
    from routes.trading import trading_bp
    from routes.language import language_bp
    from api_docs import init_api_docs

    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(root_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(magazine_bp, url_prefix='/magazine')
    app.register_blueprint(social_bp)
    app.register_blueprint(exhibition_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(language_bp, url_prefix='/language')
    
    init_api_docs(app)

    @app.cli.command("create-admin")
    @click.option('--username', prompt='Admin username', help='Username for the first admin')
    @click.option('--email', prompt='Admin email', help='Admin email')
    @click.option('--password', prompt='Admin password', hide_input=True, confirmation_prompt=True,
                  help='Admin password')
    def create_admin(username, email, password):
        """Creating the first admin user in the system"""
        with app.app_context():
            if User.query.filter_by(role=Role.ADMIN, is_active=True).first():
                click.echo(click.style("❌ There is already an admin.", fg='red'))
                return

            username = username.strip()
            email = email.strip().lower()

            if len(username) < 3:
                click.echo(click.style("❌ Username must be at least 3 characters long.", fg='red'))
                return
            if '@' not in email:
                click.echo(click.style("❌ The email address is invalid.", fg='red'))
                return
            if len(password) < 8:
                click.echo(click.style("❌ The password must be at least 8 characters long.", fg='red'))
                return

            if User.query.filter_by(username=username, is_active=True).first():
                click.echo(click.style(f"❌ Username '{username}' is already taken.", fg='red'))
                return
            if User.query.filter_by(email=email, is_active=True).first():
                click.echo(click.style(f"❌ Email '{email}' is already used.", fg='red'))
                return

            try:
                from werkzeug.security import generate_password_hash
                hashed = generate_password_hash(password)
                user = User(
                    username=username,
                    email=email,
                    password_hash=hashed,
                    role=Role.ADMIN,
                    is_premium=True,
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                click.echo(click.style(f"✅ Admin '{username}' created successfully.", fg='green'))
            except Exception as e:
                db.session.rollback()
                click.echo(click.style(f"❌ Database error: {e}", fg='red'))

    with app.app_context():
        db.create_all()
        
        # Initialize Exhibition & Trading modules
        from models.exhibition import init_exhibition_db
        from models.trading import init_trading_db
        
        try:
            init_exhibition_db()
            app.logger.info("Exhibition module initialized successfully.")
        except Exception as e:
            app.logger.warning(f"Exhibition initialization skipped: {e}")
        
        try:
            init_trading_db()
            app.logger.info("Trading module initialized successfully.")
        except Exception as e:
            app.logger.warning(f"Trading initialization skipped: {e}")
        
        app.logger.info("Database and tables created.")
    
    app.config['START_TIME'] = time.time()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)