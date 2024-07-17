## Installation and run project
#### Create virtual environment and use pip to install packages in project:
```python
python pip install -r requirements.txt
```

#### Configure the postgres database and abrarvan cloud storage in the settings.py file and run the following commands:
```python
python manage.py makemigrations
python manage.py migrate
```

#### Run project:
```python
python manage.py runserver
```
