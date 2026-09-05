"""IxquemaTatico API - quadro tático de futebol."""
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI

from database import init_db

info = Info(title="IxquemaTatico API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
