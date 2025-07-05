# 📊 Sentiment Analysis Platform

> A professional Flask web application for analyzing sentiment in PDF documents using Google Cloud Natural Language API.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **📄 PDF Text Extraction** - Advanced PDF processing with text validation
- **🧠 AI-Powered Analysis** - Google Cloud Natural Language API integration
- **📊 Visual Results** - Interactive charts and sentiment breakdowns
- **🎨 Modern UI** - Professional, responsive web interface
- **🔒 Secure** - API key encryption and secure file handling
- **⚡ Fast** - Optimized processing for real-time analysis
- **📱 Responsive** - Works on desktop, tablet, and mobile devices

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Frontend      │    │   Flask Backend  │    │  Google Cloud API   │
│   (HTML/CSS/JS) │◄──►│   (Python)       │◄──►│  Natural Language   │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ PDF Processor│
                       │ (PyPDF2)     │
                       └──────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **PDF Processing**: PyPDF2
- **AI/ML**: Google Cloud Natural Language API
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Custom responsive design
- **Icons**: Font Awesome
- **HTTP Client**: Requests library

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- Natural Language API enabled
- Valid Google Cloud API key

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/sentiment-analysis-platform.git
cd sentiment-analysis-platform
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run the Application
```bash
python run.py
```

Visit `http://localhost:5000` to access the application.

## 📁 Project Structure

```
sentiment-analysis-platform/
├── 📁 app/                 # Main application package
│   ├── main.py            # Flask application and routes
│   ├── 📁 templates/      # HTML templates
│   ├── 📁 static/         # CSS, JS, images
│   └── 📁 utils/          # Utility modules
├── 📁 config/             # Configuration files
├── 📁 docs/               # Documentation
├── 📁 tests/              # Test suite
├── 📁 uploads/            # File upload directory
├── run.py                 # Application entry point
├──