from myapp import app
from flask import render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "student_data.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# Define 'db' so that it can be imported by models

app.secret_key = "aswzdexfrcgtvnijklomjnihbgvftdrsewazdx"

import myapp.models as models
# Allowing SQLAlchemy to be used

common_ethnicities = ["NZ European", "Maori", "African", "American",
                      "Australian", "British", "Chinese", "French",
                      "German", "Indian", "Italian", "Japanese",
                      "Korean", "Russian", "Samoan"]
# These are the common ethnicities that is in the drop down list
# It is defined so that it could be used later, when we are selecting from "common ethnicities"
# Or used for "ethnicities" that aren't common


@app.route("/")
def home():
    return render_template("home.html", page_title='Home')
    # Route to home.html


@app.route("/option")
def option():
    return render_template("option.html")
    # Route for users to choose whether they want to use the "subject_trend_filter" or "dropout_trend_filter"


@app.route("/subject_trend_filter1")
def subject_trend_filter1():
    return render_template("subject_trend_filter1.html")
    # Get the primary filters for the subject_trend_graph -- Year of Start and Year of Ending, Subject


@app.route("/subject_trend_filter2", methods=["GET", "POST"])
def subject_trend_filter2():
    # Get the secondary filters -- Standard and Ethnicity

    if ('start_year' in request.form) and ('end_year' in request.form) and ('course' in request.form):
        # This codes checks whether those "keywords" are in the request form from the previous filter
        pass
    else:
        return render_template('error_404.html')
    # Ensuring the form data exist, or else this route will not work....

    if int(request.form['start_year']) <= int(request.form['end_year']):
        session['start_year'] = request.form['start_year']
        session['end_year'] = request.form['end_year']
    else:
        session['start_year'] = request.form['end_year']
        session['end_year'] = request.form['start_year']
    session['course'] = request.form['course']
    # Keep these "keywords" from the form, s
    # So that I don't have to pass this through different functions multiple times

    course_list_result = models.Standard.query.filter(models.Standard.course == (session['course'])).all()
    # Get all the information of the course (like "9DGT") from the "Standard" table on the database
    session['course_list'] = []
    # Using this session of the "course_list" in the HTML
    # It will have all the names of the standards (such as Comp Sci) for this course
    for result in course_list_result:
        session['course_list'].append(result.name)

    session['course_list'].sort()
    return render_template("subject_trend_filter2.html")


def get_trend_result(start_year, end_year, standard, ethnicities):
    # This is a helper function for the function {subject_trend_graph}
    # This helper function is used to query result
    # by taking in the 4 parameters from the filters, or from {subject_trend_graph}

    # It will get and return 3 lists:
    # candidate_id_list (basically student name list)
    # candidate_grade_list (what the above student gets)
    # candidate_year_list (when is the result recorded)

    # This is necessarily as the three lists described what the result is clearly
    # And this allows any future percentages calculations
    # And function seperated results from different years, so we don't have to query individually for a lot of years

    candidate_id_list = []
    candidate_grade_list = []
    candidate_year_list = []
    # This 3 lists will be returned

    for year in range(start_year, end_year+1):
        # E.g. from 2018 to 2022, so we must do range(2018, 2023)
        if len(ethnicities) == 0 or 'all' in ethnicities:
            # If no ethnicities were selected or "all" was selected, just query everything
            # No need to specify the ethnicities in the qury
            result_list = models.Result.query.filter(
                        and_(models.Result.standard_id == (standard),
                             models.Result.data_year == year)).all()
            # result_list will therefore has all the students' information on "9DGT" in "2021" (example)
            for result in result_list:
                candidate_id_list.append(result.candidate_id)
                candidate_grade_list.append(result.grade)
                candidate_year_list.append(result.data_year)
                # Now add the correspounding id, grade and data_year to the 3 lists
                # This will also ensure that they are in the correct order

        else:
            for ethnicity in ethnicities:
                # That is, if users are using other ethnicities that's not "all" and users selected other ethnicities
                if ethnicity == 'Others':
                    result_list = models.Result.query.join(models.Candidate).filter(
                                    and_(models.Candidate.ethnicity.notin_(common_ethnicities), models.Result.standard_id == (standard),
                                         models.Result.data_year == year)).all()
                    # All the students' information on "9DGT" in "2021" that aren't in the common_ethnicities list(example)
                else:
                    result_list = models.Result.query.join(models.Candidate).filter(
                                    and_(models.Candidate.ethnicity == ethnicity, models.Result.standard_id == (standard),
                                         models.Result.data_year == year)).all()
                    # All the students' information on "9DGT" in "2021" that are Maori(example)

                for result in result_list:
                    candidate_id_list.append(result.candidate_id)
                    candidate_grade_list.append(result.grade)
                    candidate_year_list.append(result.data_year)

    return candidate_id_list, candidate_grade_list, candidate_year_list
    # Returning the lists of id, grade and data_year from standards and ethnicities (with years)


E_grade = ['Excellent', 'Excellence', 'Excelling', 'Highly Competent', 'Very Good']
M_grade = ['Achieving Well', 'Merit', 'Good']
A_grade = ['Competent', 'Achieving', 'Achieved']
D_grade = ['Developing Skill', 'Variable']
N_grade = ['Not Achieved', 'Experiencing Difficulty']
# These are all the grades in different names recorded in the database
# Listing them out so we can convert them to NDAME scheme
# D_grade is a type of NA as well


def process_grade_year(candidate_id_list, candidate_grade_list, candidate_year_list):
    # Get all the grades with different names and put them into their categories

    Excellence = []
    Merit = []
    Achieve = []
    Develop = []
    Not_Achieve = []
    # These are the lists that contain many [grade, year, id]
    # Thus we can easily identify who are in Merit list and who are in Excellence list
    number_student_dict = {}
    # This dictionary will record the amount of students that in that year
    # Like: (key - 2018, vaule - 21), (key - 2019, value - 37) etc...

    i = 0
    for result in candidate_grade_list:
        if result in E_grade:
            Excellence.append(['E', candidate_year_list[i], candidate_id_list[i]])
        elif result in M_grade:
            Merit.append(['M', candidate_year_list[i], candidate_id_list[i]])
        elif result in A_grade:
            Achieve.append(['A', candidate_year_list[i], candidate_id_list[i]])
        elif result in D_grade:
            Develop.append(['D', candidate_year_list[i], candidate_id_list[i]])
            Not_Achieve.append(['NA', candidate_year_list[i], candidate_id_list[i]])
            # D_grade is a type of NA
        elif result in N_grade:
            Not_Achieve.append(['NA', candidate_year_list[i], candidate_id_list[i]])
        else:
            pass

        if number_student_dict.get(candidate_year_list[i], 0) == 0:
            number_student_dict[candidate_year_list[i]] = 1
        else:
            number_student_dict[candidate_year_list[i]] += 1
        i += 1

    return Excellence, Merit, Achieve, Develop, Not_Achieve, number_student_dict
    # returns the lists of E, M, A, D, NA students
    # and the number of student for each year


def get_grade_percentage(Excellence, Merit, Achieve, Not_Achieve, number_student_dict):
    # Get the dictionary of number_student_dict from above
    # for calculate the percentage of E, M, A, NA over many years, I need how many students are in that year

    # This is the percentages for just 1 curve
    # Return a list of percentages:
    # [[E, E, E, E], [M, M, M, M] ...]
    # [E, E, E, E] is actually like [93%, 36%, 32%, 71%] for 2016, 2017... for example
    keys = list(number_student_dict.keys())

    grade_percentage = []
    # I will fill all the E_list, M_list, A_list etc into this "grade_percentage"
    E_list = []
    M_list = []
    A_list = []
    NA_list = []
    # Define them so I can use them in the for loop to store the percentages each year

    for i in range(int(session['start_year']), int(session['end_year']) + 1):
        # Loop through all the year that are required to

        E = 0
        M = 0
        A = 0
        NA = 0
        # Define the number of N A M E in each year

        for j in range(len(Excellence)):
            if Excellence[j][1] == i:
                # For all the students in the Excellence list
                # If the "year" of data recorded is the current year that's in the loop
                # Increase count by 1
                E += 1
        for j in range(len(Merit)):
            if Merit[j][1] == i:
                M += 1
        for j in range(len(Achieve)):
            if Achieve[j][1] == i:
                A += 1
        for j in range(len(Not_Achieve)):
            if Not_Achieve[j][1] == i:
                NA += 1

        if i in keys:
            value = number_student_dict[i]
            E_list.append(round(E / value * 100, 1))
            M_list.append(round(M / value * 100, 1))
            A_list.append(round(A / value * 100, 1))
            NA_list.append(round(NA / value * 100, 1))
            # If there are values for that year, then get the percentage in 1dp

        else:
            E_list.append(round(0.0, 1))
            M_list.append(round(0.0, 1))
            A_list.append(round(0.0, 1))
            NA_list.append(round(0.0, 1))
            # Else let it be blank, thus 0

    grade_percentage.append(E_list)
    grade_percentage.append(M_list)
    grade_percentage.append(A_list)
    grade_percentage.append(NA_list)
    # Now this big list containing all the percentages of each grade can be used easier
    # Example of the "grade_percentage" list is
    # [ [93, 36, 32, 71], [3, 23, 14, 18], ....]
    # is in the format of [ [E, E, E, E], [M, M, M, M]... ]
    return grade_percentage


@app.route("/subject_trend_graph", methods=["GET", "POST"])
def subject_trend_graph():
    # Using the information from both filters to display the bar graph

    if 'standard_A' in request.form:
        pass
    else:
        return render_template('error_404.html')
    # Just ensure that the previous two filters are used to avoid errors

    start_year = int(session['start_year'])
    end_year = int(session['end_year'])
    subject = session['course']
    # Obtain the previous filter result

    # The current idea is, I have the user {{standard_A}} and {{standard_B}}
    # Now, extract the standard_id of these from the database table "standard"
    # Then select the {id} from the "result" table where standard_id = ?
    standard_A_name = request.form['standard_A']
    ethnicity_A = request.form.getlist('ethnicity_A')

    standard_A_id = models.Standard.query.filter(models.Standard.name == (standard_A_name)).all()[0].id
    candidate_id_list_A, candidate_grade_list_A, candidate_year_list_A = get_trend_result(start_year, end_year, standard_A_id, ethnicity_A)
    # Got lists of student_id, grades, and the year of data recorded
    # More description on how that's achieved, see the function comments on "get_trend_result"

    Excellence_A, Merit_A, Achieve_A, Develop_A, Not_Achieve_A, number_student_dict_A = process_grade_year(candidate_id_list_A, candidate_grade_list_A, candidate_year_list_A)
    # Get the lists of E, M, A, D, NA students and how many students are actually in each year
    # Note the "develop" variable is kept as it will be used if there were future imrpovement
    grade_percentage_A = get_grade_percentage(Excellence_A, Merit_A, Achieve_A, Not_Achieve_A, number_student_dict_A)
    # The grade_percentage obtain will have all the % of each grade for each year
    # E.g. [ [93, 36, 32, 71], [3, 23, 14, 18], ....]
    # is in the format of [ [E, E, E, E], [M, M, M, M]... ]

    grade_percentage_B = None
    # To define the varibles as we have if statement used
    # It must be defined since it's passed to the HTML

    if request.form.get("appliable_B"):
        standard_B_name = request.form['standard_B']
        ethnicity_B = request.form.getlist('ethnicity_B')
        standard_B_id = models.Standard.query.filter(models.Standard.name == (standard_B_name)).all()[0].id
        candidate_id_list_B, candidate_grade_list_B, candidate_year_list_B = get_trend_result(start_year, end_year, standard_B_id, ethnicity_B)

        Excellence_B, Merit_B, Achieve_B, Develop_B, Not_Achieve_B, number_student_dict_B = process_grade_year(candidate_id_list_B, candidate_grade_list_B, candidate_year_list_B)
        grade_percentage_B = get_grade_percentage(Excellence_B, Merit_B, Achieve_B, Not_Achieve_B, number_student_dict_B)
        # Same as the "A part"
    else:
        standard_B_name = None
        # Ensure that "standard_B_name" is defined as there is an if statement to see whether we have standard A

    stack_A = []
    stack_B = []
    stack_A.append(f"{subject} {standard_A_name} - E")
    stack_A.append(f"{subject} {standard_A_name} - M")
    stack_A.append(f"{subject} {standard_A_name} - A")
    stack_A.append(f"{subject} {standard_A_name} - NA")
    # Adding the "labels" for each stack in the chart.js

    if standard_B_name:
        # The title names will be different depending on how many things are selected
        title = f"Grade Trend of '{subject} {standard_A_name}' VS '{subject} {standard_B_name}' from {start_year} to {end_year}"
        stack_B.append(f"{subject} {standard_B_name} - E")
        stack_B.append(f"{subject} {standard_B_name} - M")
        stack_B.append(f"{subject} {standard_B_name} - A")
        stack_B.append(f"{subject} {standard_B_name} - NA")
    else:
        title = f"Grade Trend of '{subject} {standard_A_name}' from {start_year} to {end_year}"

    labels = [year for year in range(start_year, end_year+1)]
    # Define the x-labels for the bar graph in advance and pass it down

    return render_template("subject_trend_graph.html", start_year=start_year,
                           title=title, labels=labels,
                           grade_percentage_A=grade_percentage_A,
                           grade_percentage_B=grade_percentage_B,
                           stack_A=stack_A, stack_B=stack_B)
    # start_year can calculate the ticks for the x-labels
    # title and labels can set the name and x-axis of the chart.js graph
    # grade_percentage gives you the data of the graph
    # stack will distinguish the different groups in the graph


digital_course = ["9DGT", "9ELT", "10DGT", "10ELT", "11DTE", "11DTG", "11DTT",
                  "11DTP", "11PCE"]
# Defining some the courses that are available from yr9 to 11


@app.route("/dropout_trend_filter")
def dropout_trend_filter():
    return render_template("dropout_trend_filter.html")
    # Get the filters for the dropout_trend_filter -- Continous/drop out, year of start and year of ending
    # From a subject to another subject
    # The ethnicities, the amount of curves (from 1 to 3 curves)


def time_taken(start_course, end_course):
    """Helper function for dropout_trend_graph"""
    # To calculate the time it takes for a student from a starting course to an end course

    if start_course[0] == '9':
        start_course_year = 9
    else:
        start_course_year = int(start_course[0]+start_course[1])

    if end_course[0] == '9':
        end_course_year = 9
    else:
        end_course_year = int(end_course[0]+end_course[1])
    # To get the number from the name of the courses

    course_should_reverse = False
    # Define a varible to see whether the courses are at the right order
    year_taken = end_course_year - start_course_year
    # See the difference
    if year_taken < 0:
        year_taken = -year_taken
        course_should_reverse = True
        # If that's the wrong order, record that they should be reversed
        # If exactly 0, it's going to be fine even though the user might not supposed to do the same course
        # The result will be obviously 100% continued becuase they are at the course at the end...

        # But there is a reason for keeping the 0, if more data is added in, and the user chooses like:
        # 10DGT to 10ELT (if there is 10ELT), then we can see of the students who took 10DGT who did 10ELT

    return year_taken, course_should_reverse


def get_continue_rate(start_course, end_course, start_year, end_year, ethnicities):
    """Helper function for dropout_trend_graph"""
    # Calculate the continue rate given by a start course and an end course

    continue_rate = []
    # A list of continue rate from looping through start_year to end_year

    year_taken, course_should_reverse = time_taken(start_course, end_course)
    if course_should_reverse:
        start_course, end_course = end_course, start_course

    all_start_student_list = []
    all_end_student_list = []
    # So the idea is, that "all_start_student_list" record the data year for students (that's on the starting course) over every year
    # So does "all_end_student_list"

    # While start_student_list is different, its purpose is recorder the number of students
    # This is becuase when you query, there are many result about the same student
    # Mainly becuase he sat many exams, so using a list can see whether a student is recorded
    # So it's just a measure of how many students in a year... len(start_student_list)
    # Similar for end_student_list
    for year in range(start_year, end_year + 1):
        # year is the current looping year

        # Loop the result entry for the start course
        start_student_list = []

        if len(ethnicities) == 0 or 'all' in ethnicities:
            start_course_entry = models.Result.query.filter(and_(models.Result.course == start_course, models.Result.data_year == year)).all()
            # Now we have a list of student who is in the course (intially)

            for entry in start_course_entry:
                student = entry.candidate_id
                if student not in start_student_list:
                    start_student_list.append(student)
                    # If this student is not yet recorded as the number of students doing the course this year
                    # thus not repeated, add him to the list
                    if [student, year] not in all_start_student_list:
                        all_start_student_list.append([student, year])
                        # If this student is not yet recorded on the list for every year, add him to the list

        else:
            for ethnicity in ethnicities:
                # The ethnicities filters, it works basically like before, I have commented how it works on subject_filters
                # Basically loop through the ethnicies and add the result of each ethnicity query one after one all together
                if ethnicity == 'Others':
                    start_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Candidate.ethnicity.notin_(common_ethnicities), models.Result.course == start_course,
                                             models.Result.data_year == year)).all()
                else:
                    start_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Result.course == start_course, models.Result.data_year == year,
                                             models.Candidate.ethnicity == ethnicity)).all()

                for entry in start_course_entry:
                    # Same thing as above
                    student = entry.candidate_id
                    if student not in start_student_list:
                        start_student_list.append(student)
                        if [student, year] not in all_start_student_list:
                            all_start_student_list.append([student, year])

        # Query for the result entry for the end_course that's also in start_course
        end_student_list = []
        # Measure of how many students

        if len(ethnicities) == 0 or 'all' in ethnicities:
            end_course_entry = models.Result.query.filter(and_(models.Result.course == end_course, models.Result.data_year == year + year_taken)).all()

            for entry in end_course_entry:
                student = entry.candidate_id
                if student not in end_student_list and student in start_student_list:
                    # If this student is not yet recorded as the number of students on the end_course this year
                    # thus not repeated, add him to the end_list
                    end_student_list.append(student)
                    if [student, year] not in all_end_student_list:
                        all_end_student_list.append([student, year])
                        # Also add him to the end_list that's for every year if he's not yet there

        else:
            # Similar to above and except the ethnicities different making the query different
            # Everything else basically the same
            for ethnicity in ethnicities:
                if ethnicity == 'Others':
                    end_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Candidate.ethnicity.notin_(common_ethnicities), models.Result.course == end_course,
                                             models.Result.data_year == year + year_taken)).all()
                else:
                    end_course_entry = models.Result.query.join(models.Candidate).filter(
                                        and_(models.Result.course == end_course, models.Result.data_year == year + year_taken,
                                             models.Candidate.ethnicity == ethnicity)).all()

                for entry in end_course_entry:
                    student = entry.candidate_id
                    if student not in end_student_list and student in start_student_list:
                        end_student_list.append(student)
                        if [student, year] not in all_end_student_list:
                            all_end_student_list.append([student, year])

        # Now we have a list of student in both courses, for this specific year
        if len(start_student_list) > 0:
            continue_rate.append(len(end_student_list)/len(start_student_list) * 100)
        else:
            continue_rate.append(None)
        # Percentage calculate!

    return continue_rate, all_start_student_list, all_end_student_list
    # Return percentage, and who took the starting_course, who took the ending_course


def table_information(all_start_student_list, all_end_student_list):
    """Helper function for dropout_trend_graph"""
    # Take in the students who was at the course and the students who's also in the ending course
    # Returns a list containing the [student-data-year, student-information] for both continued and dropout students

    # "all_start_student_list" is all the student chosen the start course
    # "all_end_student_list" is all the student chosen the end course

    # all_start_student_list example:[ [33, 2021], [15, 2021], [24, 2021], [123, 2021] ]
    # First item in each list is unique id for students, second one is year they belong to

    student_of_interest = [student[0] for student in all_start_student_list if student not in all_end_student_list]
    # "student_of_interest" is all the id for the student dropped out
    student_of_interest_year = [student[1] for student in all_start_student_list if student not in all_end_student_list]
    # "student_of_interest_year" indicate which year they took the starting subject
    student_of_interest_result = models.Candidate.query.filter(models.Candidate.id.in_(student_of_interest)).all()
    # "student_of_interest_result" is the result from sqlalchemy with the input of those "student_of_interest"

    # "student_not_interest" is the students who are at the end_course
    student_not_interest = [student[0] for student in all_end_student_list]
    student_not_interest_year = [student[1] for student in all_end_student_list]
    student_not_interest_result = models.Candidate.query.filter(models.Candidate.id.in_(student_not_interest)).all()

    curve_information = [student_of_interest_year, student_of_interest_result, student_not_interest_year, student_not_interest_result]
    # This gives a list containing many lists of students information
    # "student_of_interest_result" and "student_not_interest_result" are sqlquery results
    # They will be processed to break them down to id, gender, ethnicities etc
    # Then they will be passed to HTML on the table, and then printed by for loop, one by one
    return curve_information


def get_table_student(curve_information, group):
    """Helper function for dropout_trend_graph"""
    """This function return the students and the information of the students
    so that they can be displayed in the table inside HTML
    Note, it's taking in {{curve_information}}

        curve_information[0] is a list of year of the students (in the starting_subject)
        curve_information[1] is a list of sql item e.g. [ <candidate 134>, <candidate 279> ]
        curve_information[2] is a list of year of the students (in the ending_subject)
        curve_information[3] is also a list of sql item e.g. [ <candidate 134>, <candidate 279> ]
    """

    student_list = []
    # This is what's sent to the HTML
    for i in range(len(curve_information[1])):
        student = []
        student.append(curve_information[0][i])
        student.append('Dropped out')

        student.append(curve_information[1][i].name)
        student.append(curve_information[1][i].gender)
        student.append(curve_information[1][i].ethnicity)
        student.append(curve_information[1][i].attendance)

        student_list.append(student)
        # student_list e.g. [ [2020, 'Dropped out', 33, M, French, 93], [2020, 'Dropped out', 37, F, Korean, 23]... ]

    for i in range(len(curve_information[3])):
        student = []
        student.append(curve_information[2][i])
        student.append('Continued')

        student.append(curve_information[3][i].name)
        student.append(curve_information[3][i].gender)
        student.append(curve_information[3][i].ethnicity)
        student.append(curve_information[3][i].attendance)

        student_list.append(student)
        # student_list e.g. [ ... [2021, 'Continued', 89, F, American, 56] ... ]
    if group == 'continue':
        student_list.sort(key=lambda x: (x[1], x[0], x[4]))

    else:
        student_list.sort(key=lambda x: (x[1], x[0], x[4]), reverse=True)
        # Sorting the groups of students first
        # Then sort by data year's order
        # Lastly sort by ethnicies by alphebetical order
    return student_list


def get_line_name(ethnicity):
    if len(ethnicity) == 0:
        string = 'All Ethnicities'

    elif 'all' in ethnicity:
        string = 'All Ethnicities'

    else:
        string = ''
        for i in range(len(ethnicity)):
            string += f'{ethnicity[i]}'
            if i != len(ethnicity)-1:
                string += f' & '
        # Combining the names of the ethnicities
    return string
    # Returning the title for the graph


@app.route("/dropout_trend_graph", methods=["GET", "POST"])
def dropout_trend_graph():
    # Don't worry about the variables
    # They are there just to ensure if it's not defined, my program will know they are "none"
    # So my program will know whether they exist and deal with them without crashing
    appliable_B, appliable_C = None, None
    # These two typically see whether the users want curve B and curve C

    group = None
    # Dropout/continuous

    start_year = None
    end_year = None
    # From when to when?

    start_course = None
    end_course = None
    # From which starting_course and what is the ending_course

    ethnicity_B, ethnicity_C = None, None
    # What ethnicities they are

    if 'group' in request.form:
        pass
    else:
        return render_template("error_404.html")
        # That's if the users didn't use the filter, thus my page gets no data from form

    if request.method == 'POST':
        group = request.form['group']
        start_year = int(request.form['start_year'])
        end_year = int(request.form['end_year'])
        start_course = request.form['start_subject']
        end_course = request.form['end_subject']
        # Retrieve all the users' filters

        ethnicity_A = request.form.getlist('ethnicity_A')
        # It's a multiselect, so it's a list

        if request.form.get("appliable_B"):
            appliable_B = request.form['appliable_B']
            ethnicity_B = request.form.getlist('ethnicity_B')
            # Don't get them unless user selected to show curve B

        if request.form.get("appliable_C"):
            appliable_C = request.form['appliable_C']
            ethnicity_C = request.form.getlist('ethnicity_C')
            # Same for C

    # defining variables, ensuring my program will not crash even if these data are not used
    # Becuase they will be passed to HTML, and see whether they were "none" or something else defined
    continue_rate_B = []
    continue_rate_C = []
    all_start_student_list_B = []
    all_start_student_list_C = []
    all_end_student_list_B = []
    all_end_student_list_C = []
    student_list_B = None
    student_list_C = None
    line_B_name = None
    line_C_name = None

    continue_rate_A, all_start_student_list_A, all_end_student_list_A = get_continue_rate(start_course, end_course, start_year, end_year,
                                                                                          ethnicity_A)
    # Return "percentage", and who took the "starting_course", who took the "ending_course" over many years
    curve_A_information = table_information(all_start_student_list_A, all_end_student_list_A)
    # How does it work, well, see comments for "table_information" function
    """"curve_information[0] is a list of year of the students (in the starting_subject)
        curve_information[1] is a list of sql item e.g. [ <candidate 134>, <candidate 279> ]
        curve_information[2] is a list of year of the students (in the ending_subject)
        curve_information[3] is also a list of sql item e.g. [ <candidate 134>, <candidate 279> ]
    """
    student_list_A = get_table_student(curve_A_information, group)
    # student_list e.g. [ ... [2021, 'Continued', 89, F, American, 56] ... ]
    line_A_name = get_line_name(ethnicity_A)
    # Get the tile for the graphs as well

    if appliable_B:
        # Same thing but for the parameters is B
        continue_rate_B, all_start_student_list_B, all_end_student_list_B = get_continue_rate(start_course, end_course, start_year, end_year,
                                                                                              ethnicity_B)
        curve_B_information = table_information(all_start_student_list_B, all_end_student_list_B)

        student_list_B = get_table_student(curve_B_information, group)
        line_B_name = get_line_name(ethnicity_B)

    if appliable_C:
        # Same thing but for the parameters is C
        continue_rate_C, all_start_student_list_C, all_end_student_list_C = get_continue_rate(start_course, end_course, start_year, end_year,
                                                                                              ethnicity_C)
        curve_C_information = table_information(all_start_student_list_C, all_end_student_list_C)

        student_list_C = get_table_student(curve_C_information, group)
        line_C_name = get_line_name(ethnicity_C)

    labels = []
    # The labels for the line graph when hover over them
    for i in range(abs(end_year - start_year)+1):
        labels.append(f'{start_year+i} rate of {group} for {start_course} to {end_course} students')

    return render_template("dropout_trend_graph.html", group=group,
                           appliable_B=appliable_B, appliable_C=appliable_C,
                           # Group is used to see whether dropout/continous is on
                           # Appliable is see how many curves are on

                           continue_rate_A=continue_rate_A,
                           continue_rate_B=continue_rate_B,
                           continue_rate_C=continue_rate_C,
                           # Continue_rate is basically the data that has to be graphed

                           student_list_A=student_list_A,
                           student_list_B=student_list_B,
                           student_list_C=student_list_C,
                           # student_list is the table information has to be looped

                           line_A_name=line_A_name,
                           line_B_name=line_B_name,
                           line_C_name=line_C_name,
                           # line_name is the name of the line

                           start_course=start_course,
                           end_course=end_course,
                           start_year=start_year,
                           labels=labels  # To name the start and end course
                           # with the starting year to calculate the right x-ticks
                           # labels to name the curve labels
                           )


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_404.html'), 404
    # If page not exists, leads to 404 page to tell the user the page has gone wrong
