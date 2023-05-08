from flask import Flask


app = Flask(__name__)
# Define app so other files can import 'app' from the parent file 'myapp'

from myapp import route


app.run(debug=True)
# This ensures the websites update themselves when you save your files