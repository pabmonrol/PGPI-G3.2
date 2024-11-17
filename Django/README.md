# Installation

git clone https://github.com/tu-usuario/ecomerce.git
cd ecommerce
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver