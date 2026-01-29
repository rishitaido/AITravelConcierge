from flask import Flask, render_template, request, jsonify, send_from_directory
from ai_routes import ai_routes
from flask_swagger_ui import get_swaggerui_blueprint
import os
from prometheus_client import Counter, Histogram, generate_latest
import time 
from limiter_config import limiter
import logging
import sys
from pythonjsonlogger import jsonlogger


# Configure structured JSON logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        # Add request context if available
        from flask import has_request_context
        if has_request_context():
            log_record['endpoint'] = request.path
            log_record['method'] = request.method
            log_record['remote_addr'] = request.remote_addr

# Set up JSON logging to stdout
logHandler = logging.StreamHandler(sys.stdout)
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
logHandler.setFormatter(formatter)

# Configure Flask app logger
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Also configure werkzeug (Flask's underlying WSGI server) logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
werkzeug_logger.addHandler(logHandler)



app = Flask(__name__, static_folder='static', static_url_path='/static')

limiter.init_app(app)  # Apply rate limits to this blueprint
app.register_blueprint(ai_routes)


# 1) Define your metrics
REQUEST_COUNT   = Counter('request_count', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])

# 2) Hook into the request lifecycle
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(request.method, request.path).inc()
    start = getattr(request, "start_time", time.time())
    latency = time.time() - start
    REQUEST_LATENCY.labels(request.path).observe(latency)
    
    # Log request with structured data
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "endpoint": request.path,
            "status_code": response.status_code,
            "latency_seconds": latency,
            "remote_addr": request.remote_addr
        }
    )
    
    return response

# 3) Expose the /metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# 4) Health and readiness probes for Kubernetes
@app.route('/healthz')
def healthz():
    """Liveness probe - returns 200 if the app is running"""
    return jsonify({"status": "healthy"}), 200

@app.route('/readyz')
def readyz():
    """Readiness probe - returns 200 if the app is ready to serve traffic"""
    # In a more complex app, you might check database connections, etc.
    # For now, if the server is up, we're ready
    return jsonify({"status": "ready"}), 200



SWAGGER_URL = '/docs'
API_URL     = '/openapi.yaml'

swaggerui_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={ 'app_name': "My Personalised AI Travel Concierge" }
)
app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

# Serve the spec file itself
@app.route('/openapi.yaml')
def openapi_spec():
    return send_from_directory(os.getcwd(), 'openapi.yaml')

@app.route("/")
def index():
    return render_template("TravelHome.html", page_title='My Personalised AI Travel Concierge')

@app.route("/model")
def model():
    return render_template("TravelModel.html")

@app.route("/itinerary")
def itinerary():
    return render_template("itinerary.html")

@app.route("/globe")
def globe():
    return render_template("globe.html", maptiler_key=os.getenv("MAPTILER_KEY"))

@app.route("/destinations")
def destinations(): 
    return render_template("destinations.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
    