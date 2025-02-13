from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    #  initialize_workload_types()
    app.run(host='0.0.0.0', port=9000, debug=False)