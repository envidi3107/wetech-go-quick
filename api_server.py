"""
API Server cho tool-go-quick
Chạy Flask/Quart server với routes từ api/routes.py
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thêm thư mục gốc vào sys.path để import modules
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import Flask
from flask import Flask, jsonify
from flask_cors import CORS

# Import routes từ api/routes.py
from api.routes import register_routes

def create_app(debug=False):
    """
    Khởi tạo Flask app
    
    Args:
        debug: Chế độ debug (True/False)
    
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    
    # Cấu hình
    app.config['DEBUG'] = debug
    app.config['JSON_AS_ASCII'] = False  # Hỗ trợ UTF-8 cho tiếng Việt
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    
    # Enable CORS để call từ frontend
    CORS(app)
    
    # Health check endpoint chính
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "success",
            "message": "API Server is running",
            "service": "tool-go-quick"
        })
    
    # API Info endpoint
    @app.route('/info', methods=['GET'])
    def info():
        return jsonify({
            "service": "tool-go-quick",
            "version": "1.0",
            "description": "Vietnamese ID Card (CCCD) Extractor & Document Processing",
            "endpoints": {
                "health": "GET /health",
                "info": "GET /info",
                "go-quick": {
                    "health": "GET /api/go-quick/health",
                    "read-quick": "POST /api/go-quick/read-quick - Đọc nhanh 1 CCCD",
                    "process-cccd": "POST /api/go-quick/process-cccd - Xử lý CCCD Extractor"
                }
            },
            "features": [
                "CCCD Extractor - Extract data from ID card images",
                "PDF2PNG - Convert PDF to PNG",
                "XLSX2PNG - Convert Excel to PNG"
            ]
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "status": "error",
            "message": "Endpoint not found",
            "path": str(e.description)
        }), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "detail": str(e) if debug else "Server error"
        }), 500
    
    # Đăng ký routes từ api/routes.py
    logger.info("Registering routes from api/routes.py...")
    register_routes(app, '/api/go-quick')
    logger.info("✅ Routes registered successfully!")
    
    return app

def run_development_server(host='0.0.0.0', port=5000, debug=True):
    """
    Chạy server ở chế độ development
    
    Args:
        host: Host address (default: 0.0.0.0)
        port: Port number (default: 5000)
        debug: Debug mode (default: True)
    """
    logger.info(f"🚀 Starting API Server...")
    logger.info(f"   Host: {host}")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    
    app = create_app(debug=debug)
    app.run(host=host, port=port, debug=debug, use_reloader=debug)

def run_production_server(host='0.0.0.0', port=5000):
    """
    Chạy server ở chế độ production (dùng Gunicorn)
    
    Usage:
        from api_server import app
        # Then run: gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
    """
    app = create_app(debug=False)
    return app

# Tạo app instance cho production (Gunicorn, etc.)
app = create_app(debug=False)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Start API Server for tool-go-quick')
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    
    args = parser.parse_args()
    
    # Xác định chế độ debug
    debug = False
    if args.debug:
        debug = True
    elif not args.no_debug:
        debug = True  # Default to debug for development
    
    run_development_server(host=args.host, port=args.port, debug=debug)
