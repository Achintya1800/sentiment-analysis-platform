#!/usr/bin/env python3
"""
Sentiment Analysis Platform - Application Entry Point
Professional Flask application for PDF document sentiment analysis.

Usage:
    python run.py                    # Run in development mode
    python run.py --prod            # Run in production mode
    python run.py --host 0.0.0.0    # Run with custom host
    python run.py --port 8080       # Run with custom port

Author: [Your Name]
Created: July 2025
"""

import os
import sys
import argparse
from app.main import create_app
from config.settings import config

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Sentiment Analysis Platform')
    parser.add_argument('--config', default='development',
                       choices=['development', 'production', 'testing'],
                       help='Configuration mode (default: development)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port number (default: 5000)')
    parser.add_argument('--prod', action='store_true',
                       help='Run in production mode')
    return parser.parse_args()

def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Determine configuration
    config_name = 'production' if args.prod else args.config
    
    # Create Flask application
    app = create_app()
    app.config.from_object(config[config_name])
    
    # Initialize configuration
    config[config_name].init_app(app)
    
    print(f"🚀 Starting Sentiment Analysis Platform")
    print(f"📊 Configuration: {config_name}")
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"🔧 Debug mode: {app.config['DEBUG']}")
    print("=" * 50)
    
    try:
        # Run the application
        app.run(
            host=args.host,
            port=args.port,
            debug=app.config['DEBUG']
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Sentiment Analysis Platform")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()