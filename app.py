from flask import Flask, render_template, request, jsonify, send_from_directory
from ai_routes import ai_routes
from flask_swagger_ui import get_swaggerui_blueprint
import os
from prometheus_client import Counter, Histogram, generate_latest
import time 
from limiter_config import limiter


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
    REQUEST_LATENCY.labels(request.path).observe(time.time() - start)
    return response

# 3) Expose the /metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


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
    app.run(host="0.0.0.0", port=5001, debug=True)
    