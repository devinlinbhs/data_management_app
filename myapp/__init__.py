from flask import Flask


app = Flask(__name__)


from myapp import route


app.run(debug=True)