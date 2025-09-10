#!/usr/bin/env python3
"""
Sara AI Receptionist Setup Script
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def setup_virtual_environment():
    """Set up virtual environment"""
    if not os.path.exists("venv"):
        return run_command("python -m venv venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
        return True

def install_dependencies():
    """Install Python dependencies"""
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
    
    return run_command(f"{activate_cmd} && pip install --upgrade pip && pip install -r requirements.txt", 
                      "Installing dependencies")

def setup_environment_file():
    """Set up environment file"""
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ Created .env file from env.example")
            print("⚠️  Please edit .env file with your API keys and configuration")
            return True
        else:
            print("❌ env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
        return True

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "alembic/versions"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Created necessary directories")
    return True

def setup_database():
    """Set up database migrations"""
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
    
    return run_command(f"{activate_cmd} && alembic upgrade head", "Setting up database")

def main():
    """Main setup function"""
    print("🚀 Setting up Sara AI Receptionist...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Creating directories", create_directories),
        ("Setting up virtual environment", setup_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment file", setup_environment_file),
        ("Setting up database", setup_database),
    ]
    
    failed_steps = []
    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    print("=" * 50)
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease fix the errors and run setup again.")
        sys.exit(1)
    else:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Download Google Calendar credentials.json")
        print("3. Run: python app/main.py")
        print("4. Or run with Docker: docker-compose up -d")

if __name__ == "__main__":
    main()
