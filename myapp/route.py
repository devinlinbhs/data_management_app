from myapp import app
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(basedir,"student_data.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# Define 'db' so that it can be imported by models

app.secret_key ="aswzdexfrcgtvnijklomjnihbgvftdrsewazdx"

import myapp.models as models
# Allowing SQLAlchemy to be used

@app.route("/")
def home():
    # Currently testing whether SQLAlchemy works
    candidates_list = models.Candidate.query.all()
    course_information_list = models.Course_information.query.all()
    senior_standard_list = models.Senior_standard.query.all()
    grade_obtained_list = models.Grade_obtained.query.all()
    data_year_list = models.Data_year.query.all()
    overall_management_list = models.Overall_management.query.all()
    
    return render_template("home.html", page_title='Home', candidates_list = candidates_list, course_information_list = course_information_list, 
                        senior_standard_list = senior_standard_list, grade_obtained_list = grade_obtained_list, 
                        data_year_list = data_year_list, overall_management_list = overall_management_list)
    # Return all the data taken from the database