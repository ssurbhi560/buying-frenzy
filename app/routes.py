from app import app

@app.route("/")
def home():
    return "Backend API for a restaurant."