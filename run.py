# run.py
from app import create_app

app = create_app()  # uses config.Config by default

if __name__ == "__main__":
    app.run(debug=True)
