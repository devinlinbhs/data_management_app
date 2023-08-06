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


def time_taken(start_course, end_course):
    """To calculate the time it takes for a student from a starting course to an end course"""

    if start_course[0] == '9':
        start_course_year = 9
    else:
        start_course_year = int(start_course[0]+start_course[1])
    
    end_course_year = int(end_course[0]+end_course[1])
    year_addition = end_course_year - start_course_year
    
    return year_addition

def get_continue_rate(start_course, end_course, start_year, end_year, ethnicities):
    """helper function which returns the continue rate given by a start course and an end course"""
    common_ethnicities = ["NZ European", "Maori", "African", "American", "Australian",
                        "British", "Chinese","French","German", "Indian","Italian", "Japanese",
                        "Korean","Russian","Samoan"]
    # A list of continue rate from looping through start_year to end_year
    continue_rate = []
    year_addition = time_taken(start_course, end_course)
    
    for year in range(start_year, end_year +1):
        # i is the current looping year
            
        # For Curve 1:
        # All the result entry for the course 1
        start_student_list = []
        if len(ethnicities) == 0 or 'all' in ethnicities:
            start_course_entry = models.Result.query.filter(and_(models.Result.course == start_course, models.Result.data_year == year)).all()
            for entry in start_course_entry:
                student = entry.candidate_id
                if student not in start_student_list:
                    # If this student is new, add him to the list
                    start_student_list.append(student)
            # Now we have a list of student who is in the course
        else:
            for ethnicity in ethnicities:
                if ethnicity == 'Others':
                    start_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Candidate.ethnicity.notin_(common_ethnicities), models.Result.course == start_course,
                                            models.Result.data_year == year)).all()
                else:
                    start_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Result.course == start_course, models.Result.data_year == year, 
                                            models.Candidate.ethnicity == ethnicity)).all()
                for entry in start_course_entry:
                    student = entry.candidate_id
                    if student not in start_student_list:
                        # If this student is new, add him to the list
                        start_student_list.append(student)
                        
                        
        # All the result entry for the course 2 that's also in course 1
        end_student_list = []
        if len(ethnicities) == 0 or 'all' in ethnicities:
            end_course_entry = models.Result.query.filter(and_(models.Result.course == end_course, models.Result.data_year == year + year_addition)).all()
            for entry in end_course_entry:
                student = entry.candidate_id
                if student not in end_student_list and student in start_student_list:
                    # If this student is new and also taken the prerequisite
                    # Add the student into the "continue category"
                    end_student_list.append(student)
                
        else:
            for ethnicity in ethnicities:
                if ethnicity == 'Others':
                    end_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Candidate.ethnicity.notin_(common_ethnicities), models.Result.course == end_course,
                                            models.Result.data_year == year + year_addition)).all()
                else:
                    end_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Result.course == end_course, models.Result.data_year == year + year_addition, 
                                            models.Candidate.ethnicity == ethnicity)).all()
                for entry in end_course_entry:
                    student = entry.candidate_id
                    if student not in end_student_list and student in start_student_list:
                        end_student_list.append(student)
        
                
        # Now we have a list of student in both courses
        if len(start_student_list) >0:
            continue_rate.append(len(end_student_list)/len(start_student_list) *100)
        else:
            continue_rate.append(None)
    
    return continue_rate, end_student_list


@app.route("/dropout_trend_graph", methods = ["GET","POST"])
def dropout_trend_graph():
    # to see whether the user would like to have 1 or 2 graphs in the same time
    appliable_B, appliable_C = None, None
    group = None
    start_year = None
    end_year  = None
    start_course = None
    end_course = None
    ethnicity_B, ethnicity_C  = None, None
    if request.method == 'POST':
        
        
        group = request.form['group']
        start_year = int(request.form['start_year'])
        end_year = int(request.form['end_year'])
        start_course = request.form['start_subject']
        end_course = request.form['end_subject']
        # Common information field
        
        ethnicity_A = request.form.getlist('ethnicity_A')
        # Compulsory field
        
        if request.form.get("appliable_B"):
            appliable_B = request.form['appliable_B']
            ethnicity_B = request.form.getlist('ethnicity_B')
            
        if request.form.get("appliable_C"):
            appliable_C = request.form['appliable_C']
            ethnicity_C = request.form.getlist('ethnicity_C')
            
    '''Looks complicated, actually you get something like
    appliable continue
    2021 2022
    9DGT 10DGT
    
    appliable continue
    2021 2023
    9DGT 11DTP
    
    indicating that user want to know 
    Line A: students who continued from 2021 9DGT to 2022 10DGT
    Line B: students who continued from 2021 9DGT to 2023 11DTP
    '''
    end_student_list_A, end_student_list_B, end_student_list_C = None, None, None
    continue_rate_A, continue_rate_B, continue_rate_C = [],0,0
    continue_rate_A, end_student_list_A = get_continue_rate(start_course, end_course, start_year, end_year, ethnicity_A)
    if appliable_B:
        continue_rate_B, end_student_list_B = get_continue_rate(start_course, end_course, start_year, end_year, ethnicity_B)
    if appliable_C:
        continue_rate_C, end_student_list_C = get_continue_rate(start_course, end_course, start_year, end_year, ethnicity_C)

    labels = []
    for i in range(abs(end_year - start_year)+1):
        labels.append(f'{start_year+i} rate of {group} for {start_course} to {end_course} students')

    return render_template("dropout_trend_graph.html", 
                        group = group,
                        appliable_B = appliable_B,
                        appliable_C = appliable_C,
                        continue_rate_A = continue_rate_A,
                        continue_rate_B = continue_rate_B,
                        continue_rate_C = continue_rate_C,
                        labels = labels,
                        
                        # Below is unnecesary but for testing
                        ethnicity_A = ethnicity_A,
                        ethnicity_B = ethnicity_B,
                        ethnicity_C = ethnicity_C,

                        end_student_list_A =end_student_list_A,
                        end_student_list_B = end_student_list_B,
                        end_student_list_C = end_student_list_C,
                        
                        start_course = start_course,
                        end_course = end_course,
                        start_year = start_year,
                        end_year = end_year,
)