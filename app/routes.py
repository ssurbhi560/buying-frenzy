from app import app


@app.route("/")
def home():
    return "Backend Service for a food delivery platform."
