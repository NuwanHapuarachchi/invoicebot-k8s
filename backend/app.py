import sys
import os
from flask import Flask

# Add the parent directory to Python path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes import bp as main_bp


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.register_blueprint(main_bp)
    return app


app = create_app()


if __name__ == '__main__':
    print("Starting server...")
    try:
        from waitress import serve
        print("Using Waitress WSGI server on 0.0.0.0:5000")
        serve(app, host='0.0.0.0', port=5000)
    except ImportError:
        print("Waitress not available. Using Flask development server.")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Waitress failed to start: {e}. Falling back to Flask development server.")
        app.run(host='0.0.0.0', port=5000, debug=True)

