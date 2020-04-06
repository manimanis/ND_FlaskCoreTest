pip install flask_sqlalchemy
pip install flask_cors
pip install flask --upgrade
pip uninstall flask-socketio -y
rem service postgresql start
psql -U postgres < backend\setup.sql
psql -U student bookshelf < ..\backend\books.psql