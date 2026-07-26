import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import app

def handler(context, basic_io):
    """
    Zoho Catalyst Advanced I/O Python Entry Point
    """
    req = basic_io.get_request()
    url_path = req.get_url_path()
    
    with app.test_client() as client:
        method = req.get_request_method()
        response = client.open(url_path, method=method)
        
        basic_io.write(response.get_data(as_text=True))
        basic_io.set_status_code(response.status_code)
        basic_io.set_content_type("application/json")

if __name__ == "__main__":
    app.run(port=5000)
