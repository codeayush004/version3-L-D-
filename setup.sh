#!/bin/bash

# L&D Portal Setup Script
# This script automates the installation of backend and frontend dependencies.

echo "🚀 Starting L&D Portal Setup..."

# 1. Backend Setup
echo "📂 Setting up Backend..."
cd backend || { echo "❌ Backend directory not found!"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Install requirements
echo "Installing backend dependencies..."
./venv/bin/pip install -r requirements.txt

# Create .env example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating template .env file..."
    echo "MONGO_URI=mongodb://localhost:27017/ld_portal" > .env
    echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
    echo "⚠️  Please update backend/.env with your actual credentials."
fi

cd ..

# 2. Frontend Setup
echo "📂 Setting up Frontend..."
cd frontend || { echo "❌ Frontend directory not found!"; exit 1; }

echo "Installing frontend dependencies..."
npm install

cd ..

echo "✅ Setup Complete!"
echo "--------------------------------------------------"
echo "To run the application:"
echo "1. Backend: cd backend && ./venv/bin/python run.py"
echo "2. Frontend: cd frontend && npm run dev"
echo "--------------------------------------------------"
