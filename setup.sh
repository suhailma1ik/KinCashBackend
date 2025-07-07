#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting H.E.L.P Backend project setup..."

# Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "Python 3 could not be found. Please install Python 3.10+."
    exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null
then
    echo "pip3 could not be found. Please install pip for Python 3."
    exit 1
fi

echo "1. Creating virtual environment..."
python3 -m venv venv

echo "2. Activating virtual environment..."
source venv/bin/activate

echo "3. Installing dependencies from requirements/dev.txt..."
pip install --upgrade pip
pip install -r requirements/dev.txt

echo "4. Copying .env.example to .env (if it doesn't exist)..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit the .env file with your specific configurations."
else
    echo ".env file already exists. Skipping copy."
fi

echo "5. Running database migrations..."
python manage.py migrate

echo "\nSetup complete!"
echo "\nNext steps:"
echo "- If you haven't already, edit the .env file with your database credentials and other settings."
echo "- Create a superuser: python manage.py createsuperuser"
echo "- Run the development server: python manage.py runserver"
echo "\nTo deactivate the virtual environment, run: deactivate"