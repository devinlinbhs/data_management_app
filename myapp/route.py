from myapp import app
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, and_, or_
import numpy as np
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
    
    
    return render_template("home.html", page_title='Home')
    # Return all the data taken from the database


@app.route("/option")
def option():
    # Should have the boxes of pictures of which filter to use
    return render_template("option.html")

@app.route("/subject_trend_filter")
def subject_trend_filter():
    # Should have the boxes of pictures of which filter to use
    return render_template("subject_trend_filter.html")


@app.route("/dropout_trend_filter")
def dropout_trend_filter():
    # Should have the boxes of pictures of which filter to use
    return render_template("dropout_trend_filter.html")


digital_course = ["9DGT","9ELT","10DGT","10ELT","11DTE","11DTG","11DTT","11DTP",
                "11PCE","12DTE","12DTG","12DTM","12DTP","12PCE","13PCE","13DTE",
                "13DTG","13DTM","13DTP","13DTS"]
# NEED TO ASK WHAT COURSES ARE DIGI COURSES


@app.route("/data", methods = ["GET","POST"])
def data():
    infile = open("student_list.csv", "r")
    result = infile.read().splitlines()
    infile.close()
    
    student_list = []
    
    
    for line in result:
        line = line.replace(' (Specify Date, incl Days)', "")
        line = line.replace('years,', "years")
        line = line.replace('months,', "months")
        student = line.split(',')
        del student[6]
        courses = student[7].split(';')
        student_digital_course = [course for course in courses if course in digital_course]
        
        """
        The list of student has:
        student[0]: Unique ID
        student[1]: Gender
        student[2]: Level
        student[3]: Form class
        student[4]: Ethnicity
        student[5]: Age in full
        student[6]: Attendance -Present in full days
        student[7]: All the courses taken
        student[8]: NCEA credits
        ...
        """
        
        student_np = np.array(student)
        student = list(student_np[:8])
        if len(student_digital_course) > 0:
            student[7] = student_digital_course
        else:
            del student[7]
        student_list.append(student)
        
        digi_student_list = []
        for student in student_list:
            if len(student) == 8:
                digi_student_list.append(student)

        initial_student = []
        final_student = []
        for digi_student in digi_student_list:
            if '9DGT' in digi_student[7]:
                initial_student.append(digi_student)
                if '10DGT' in digi_student[7]:
                    final_student.append(digi_student)
        
    return render_template("data.html", student_list = student_list,
                        student_digital_course = student_digital_course,
                        digi_student_list = digi_student_list,
                        initial_student = initial_student,
                        final_student = final_student)


# The codes below functions properly but shouldn't be confused in with the rest of the codes yet
# They are not going to be used for a long time

@app.route("/subject_trend_graph", methods = ["GET","POST"])
def subject_trend_graph():
    # Should have the boxes of pictures of which filter to use
    return render_template("subject_trend_graph.html")


def get_continue_rate(start_course, end_course, start_year, end_year):
    """helper function which returns the continue rate given by a start course and an end course"""
    # For Curve A:
    start_course_entry = models.Result.query.filter(and_(models.Result.course == start_course, models.Result.data_year == start_year)).all()
    # All the result entry for the course 1
    start_student_list = []
    for entry in start_course_entry:
        student = entry.candidate_id
        if student not in start_student_list:
            # If this student is new, add him to the list
            start_student_list.append(student)
    # Now we have a list of student who is in the course
    
    end_course_entry = models.Result.query.filter(and_(models.Result.course == end_course, models.Result.data_year == end_year)).all()
    # All the result entry for the course 2
    end_student_list = []
    for entry in end_course_entry:
        student = entry.candidate_id
        if student not in end_student_list and student in start_student_list:
            # If this student is new and also taken the prerequisite
            # Add the student into the "continue category"
            end_student_list.append(student)
    # Now we have a list of student in both courses
    if len(start_student_list) >0:
        continue_rate = len(end_student_list)/len(start_student_list) *100
    else:
        continue_rate = -1
    
    return continue_rate


@app.route("/dropout_trend_graph", methods = ["GET","POST"])
def dropout_trend_graph():
    # to see whether the user would like to have 1 or 2 graphs in the same time
    appliable_A, appliable_B = None, None
    group_A, group_B = None, None
    from_year_A, from_year_B = None, None
    to_year_A, to_year_B = None, None
    from_subject_A, from_subject_B = None, None
    to_subject_A, to_subject_B = None, None
    if request.method == 'POST':
        if request.form.get("appliable_A"):
            appliable_A = request.form['appliable_A']
            group_A = request.form['group_A']
            start_year_A = request.form['from_year_A']
            end_year_A = request.form['to_year_A']
            start_course_A = request.form['from_subject_A']
            end_course_A = request.form['to_subject_A']
        if request.form.get("appliable_B"):
            appliable_B = request.form['appliable_B']
            group_B = request.form['group_B']
            start_year_B = request.form['from_year_B']
            end_year_B = request.form['to_year_B']
            start_course_B = request.form['from_subject_B']
            end_course_B = request.form['to_subject_B']
            
    '''Looks complicated, actually you get something like
    appliable continous
    2021 2022
    9DGT 10DGT
    
    appliable continous
    2021 2023
    9DGT 11DTP
    
    indicating that user want to know 
    Line A: students who continued from 2021 9DGT to 2022 10DGT
    Line B: students who continued from 2021 9DGT to 2023 11DTP
    '''
    continue_rate_A, continue_rate_B = 0,0
    if appliable_A:
        continue_rate_A = get_continue_rate(start_course_A, end_course_A, start_year_A, end_year_A)
    if appliable_B:
        continue_rate_B = get_continue_rate(start_course_B, end_course_B, start_year_B, end_year_B)



    return render_template("dropout_trend_graph.html", 
                        appliable_A = appliable_A,
                        group_A = group_A,
                        from_year_A = from_year_A,
                        to_year_A = to_year_A,
                        from_subject_A = from_subject_A,
                        to_subject_A = to_subject_A,
                        
                        appliable_B = appliable_B,
                        group_B = group_B,
                        from_year_B = from_year_B,
                        to_year_B = to_year_B,
                        from_subject_B = from_subject_B,
                        to_subject_B = to_subject_B,

                        continue_rate_A = continue_rate_A,
                        continue_rate_B = continue_rate_B
)