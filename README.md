# libraries2025
python -m venv myworld

source libenv/bin/activate

python -m pip install Django

django-admin startproject libraries .

python manage.py runserver

python manage.py startapp library
