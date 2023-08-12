from myapp import app
from flask import render_template, request, redirect, session
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

common_ethnicities = ["NZ European", "Maori", "African", "American", "Australian",
                        "British", "Chinese","French","German", "Indian","Italian", "Japanese",
                        "Korean","Russian","Samoan"]

@app.route("/")
def home():
    
    
    return render_template("home.html", page_title='Home')
    # Return all the data taken from the database


@app.route("/option")
def option():
    # Should have the boxes of pictures of which filter to use
    return render_template("option.html")



@app.route("/subject_trend_filter1")
def subject_trend_filter1():
    # Get the primary filters -- Year of Start and Year of Ending, Subject
    return render_template("subject_trend_filter1.html")

@app.route("/subject_trend_filter2", methods = ["GET","POST"])
def subject_trend_filter2():
    # Get the secondary filters -- Standard and Ethnicity
    session['start_year'] = request.form['start_year']
    session['end_year'] = request.form['end_year']
    session['course'] = request.form['course']
    
    course_list_result = models.Standard.query.filter(models.Standard.course == (session['course'])).all()
    # Get the information about the chosen course
    session['course_list'] = []
    for result in course_list_result:
        session['course_list'].append(result.name)
    
    session['course_list'].sort()
    return render_template("subject_trend_filter2.html")


def get_trend_result(start_year, end_year, standard, ethnicities):
    # This is a helper function for the {subject_trend_graph}
    
    # Get standard and ethnicities from {subject_trend_graph}, returning
    # candidate_id_list, candidate_grade_list, candidate_year_list
    candidate_id_list = []
    candidate_grade_list = []
    candidate_year_list = []
    for year in range(start_year, end_year+1):
        if len(ethnicities) == 0 or 'all' in ethnicities:
                result_A = models.Result.query.filter(
                            and_(models.Result.standard_id == (standard), 
                                models.Result.data_year == year)).all()
        else:
            for ethnicity in ethnicities:
                if ethnicity == 'Others':
                    result_A = models.Result.query.join(models.Candidate).filter(
                                    and_(models.Candidate.ethnicity.notin_(common_ethnicities), models.Result.standard_id == (standard),
                                        models.Result.data_year == year)).all()
            else:
                    result_A = models.Result.query.join(models.Candidate).filter(
                                    and_(models.Candidate.ethnicity == ethnicity, models.Result.standard_id == (standard),
                                        models.Result.data_year == year)).all()
        
        for result in result_A:
            candidate_id_list.append(result.candidate_id)
            candidate_grade_list.append(result.grade)
            candidate_year_list.append(result.data_year)
        
    return candidate_id_list, candidate_grade_list, candidate_year_list

E_grade = ['Excellent', 'Excellence', 'Excelling', 'Highly Competent', 'Very Good']
M_grade = ['Achieving Well', 'Merit', 'Good']
A_grade = ['Competent', 'Achieving']
D_grade = ['Developing Skill', 'Variable']
N_grade = ['Not Achieved', 'Experiencing Difficulty']

def process_grade_year(candidate_id_list, candidate_grade_list, candidate_year_list):
    # Get all the grades and put them into different groups
    
    Excellence = []
    Merit = []
    Achieve = []
    Develop = []
    Not_Achieve = []
    
    i = 0
    for result in candidate_grade_list:
        if result in E_grade:
            Excellence.append(['E', candidate_year_list[i], candidate_id_list[i]])
        elif result in M_grade:
            Merit.append(['M', candidate_year_list[i], candidate_id_list[i]])
        elif result in A_grade:
            Achieve.append(['A', candidate_year_list[i], candidate_id_list[i]])
        else:
            if result in D_grade:
                Develop.append(['D', candidate_year_list[i], candidate_id_list[i]])
            Not_Achieve.append(['NA', candidate_year_list[i], candidate_id_list[i]])
            
    return Excellence, Merit, Achieve, Develop, Not_Achieve


@app.route("/subject_trend_graph", methods = ["GET","POST"])
def subject_trend_graph():
    # Using the information from both filters to display the bar graph
    start_year = int(session['start_year'])
    end_year = int(session['end_year'])
    subject = session['subject']
    
    
    
    # The current idea is, I have the user {{standard_A}} and {{standard_B}}, extract the standard_id of these from 
    # the data base table "standard"
    # Then select the {id} from result where standard_id = ?
    standard_A = request.form['standard_A']
    ethnicity_A = request.form.getlist('ethnicity_A')
    standard_A = models.Standard.query.filter(models.Standard.name == (standard_A)).all()[0].id
    candidate_id_list_A, candidate_grade_list_A, candidate_year_list_A = get_trend_result(start_year, end_year, standard_A, ethnicity_A)
    # Got lists of student_id, grades, and the year they belong to
    # Pass this grade through the HTML, display it in Chart.JS using different stacking
    
    Excellence_A, Merit_A, Achieve_A, Develop_A, Not_Achieve_A = process_grade_year(candidate_id_list_A, candidate_grade_list_A, candidate_year_list_A)

    standard_B = None
    ethnicity_B = None
    candidate_id_list_B = None
    candidate_grade_list_B = None
    candidate_year_list_B = None
    
    Excellence_B, Merit_B, Achieve_B, Develop_B, Not_Achieve_B = None, None, None, None, None
    
    if request.form.get("appliable_B"):
        standard_B = request.form['standard_B']
        ethnicity_B = request.form.getlist('ethnicity_B')
        standard_B = models.Standard.query.filter(models.Standard.name == (standard_B)).all()[0].id
        candidate_id_list_B, candidate_grade_list_B, candidate_year_list_B = get_trend_result(start_year, end_year, standard_B, ethnicity_B)
        
        Excellence_B, Merit_B, Achieve_B, Develop_B, Not_Achieve_B = process_grade_year(candidate_id_list_B, candidate_grade_list_B, candidate_year_list_B)
    # Same thing is done to curve B
    
    
    return render_template("subject_trend_graph.html", start_year =start_year,
                        end_year = end_year, subject = subject,
                        
                        standard_A = standard_A, standard_B = standard_B,
                        ethnicity_A = ethnicity_A, ethnicity_B = ethnicity_B,
                        
                        candidate_id_list_A = candidate_id_list_A,
                        candidate_grade_list_A = candidate_grade_list_A,
                        candidate_year_list_A = candidate_year_list_A,
                        
                        candidate_id_list_B = candidate_id_list_B,
                        candidate_grade_list_B = candidate_grade_list_B,
                        candidate_year_list_B = candidate_year_list_B,
                        
                        Excellence_A = Excellence_A, 
                        Merit_A = Merit_A, 
                        Achieve_A = Achieve_A,
                        Develop_A = Develop_A, 
                        Not_Achieve_A = Not_Achieve_A,
                        
                        Excellence_B = Excellence_B, 
                        Merit_B = Merit_B, 
                        Achieve_B = Achieve_B,
                        Develop_B = Develop_B, 
                        Not_Achieve_B = Not_Achieve_B,
                        )




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

@app.route("/dropout_trend_filter")
def dropout_trend_filter():
    # Should have the boxes of pictures of which filter to use
    return render_template("dropout_trend_filter.html")


def time_taken(start_course, end_course):
    """To calculate the time it takes for a student from a starting course to an end course"""

    if start_course[0] == '9':
        start_course_year = 9
    else:
        start_course_year = int(start_course[0]+start_course[1])
    
    end_course_year = int(end_course[0]+end_course[1])
    year_addition = end_course_year - start_course_year
    
    return year_addition

def get_continue_rate(start_course, end_course, start_year, end_year, ethnicities, all_start_student_list, all_end_student_list):
    """helper function which returns the continue rate given by a start course and an end course"""
    
    # A list of continue rate from looping through start_year to end_year
    continue_rate = []
    year_addition = time_taken(start_course, end_course)
    
    for year in range(start_year, end_year +1):
        # year is the current looping year
            
        # For Curve 1:
        # All the result entry for the course 1
        start_student_list = []
        if len(ethnicities) == 0 or 'all' in ethnicities:
            start_course_entry = models.Result.query.filter(and_(models.Result.course == start_course, models.Result.data_year == year)).all()
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
                if [student, year] not in all_start_student_list:
                    all_start_student_list.append([student, year])
                        
                        
                        
        # All the result entry for the course 2 that's also in course 1
        end_student_list = []
        if len(ethnicities) == 0 or 'all' in ethnicities:
            end_course_entry = models.Result.query.filter(and_(models.Result.course == end_course, models.Result.data_year == year + year_addition)).all()
            
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
                # If this student is new and also taken the prerequisite
                # Add the student into the "continue category"
                end_student_list.append(student)
                if [student, year] not in all_end_student_list:
                    all_end_student_list.append([student, year])
                
                
        # Now we have a list of student in both courses
        if len(start_student_list) >0:
            continue_rate.append(len(end_student_list)/len(start_student_list) *100)
        else:
            continue_rate.append(None)
    
    return continue_rate, all_start_student_list, all_end_student_list


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
    
    
    continue_rate_A, continue_rate_B, continue_rate_C = [],[],[]
    all_start_student_list = []
    all_end_student_list = []
    continue_rate_A, all_start_student_list, all_end_student_list = get_continue_rate(start_course, end_course, start_year, end_year, 
                                        ethnicity_A, all_start_student_list, all_end_student_list)
    if appliable_B:
        continue_rate_B, all_start_student_list, all_end_student_list = get_continue_rate(start_course, end_course, start_year, end_year, 
                                        ethnicity_B, all_start_student_list, all_end_student_list)
    if appliable_C:
        continue_rate_C, all_start_student_list, all_end_student_list = get_continue_rate(start_course, end_course, start_year, end_year, 
                                        ethnicity_C, all_start_student_list, all_end_student_list)

    # "all_start_student_list" is all the student chosen the start course
    # "all_end_student_list" is all the student chosen the end course
    
    # "student_of_interest" is all the id for the student dropped out
    # "student_of_interest_year" indicate which year they took the starting subject
    # "student_of_interest_result" is the result from sqlalchemy with the input of those "student_of_interest"
    student_of_interest = [student[0] for student in all_start_student_list if student not in all_end_student_list]
    student_of_interest_year = [student[1] for student in all_start_student_list if student not in all_end_student_list]
    student_of_interest_result = models.Candidate.query.filter(models.Candidate.id.in_(student_of_interest)).all()
    
    # "student_not_interest" is the students who stayed
    student_not_interest = [student[0] for student in all_end_student_list]
    student_not_interest_year = [student[1] for student in all_end_student_list]
    student_not_interest_result = models.Candidate.query.filter(models.Candidate.id.in_(student_not_interest)).all()
    
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
                        
                        student_of_interest_year = student_of_interest_year,
                        student_of_interest_result = student_of_interest_result,
                        student_not_interest_year = student_not_interest_year,
                        student_not_interest_result = student_not_interest_result,
                        # Below is unnecesary but for testing
                        ethnicity_A = ethnicity_A,
                        ethnicity_B = ethnicity_B,
                        ethnicity_C = ethnicity_C,
                        
                        start_course = start_course,
                        end_course = end_course,
                        start_year = start_year,
                        end_year = end_year,
)