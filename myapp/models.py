from myapp.route import db
# db is defined at route

# Setting up all the tables for the SQLAlchemy
class Candidate(db.Model):
    __tablename__ = "Candidate"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    student_id = db.Column(db.Integer())
    nsn = db.Column(db.Integer())
    gender = db.Column(db.Text())
    ethnicity = db.Column(db.Text())
    student_year_level = db.Column(db.Integer())
    data_year_id = db.Column(db.Integer, db.ForeignKey("Data_year.id"))
    # Only 1 foreign key from "Data_year" table
    # With 1 primary key

class Data_year(db.Model):
    __tablename__ = "Data_year"
    id = db.Column(db.Integer, primary_key=True)
    year_of_data = db.Column(db.Integer())
    
    
class Course_information(db.Model):
    __tablename__ = "Course_information"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    course_code = db.Column(db.Text())
    level = db.Column(db.Integer())
    data_year_id = db.Column(db.Integer, db.ForeignKey("Data_year.id"))
    
    
class Senior_standard(db.Model):
    __tablename__ = "Senior_standard"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    standard_year_level = db.Column(db.Integer())
    assessment_type = db.Column(db.Text())
    standard_code = db.Column(db.Integer())
    credit = db.Column(db.Integer())
    version = db.Column(db.Integer())
    data_year_id = db.Column(db.Integer, db.ForeignKey("Data_year.id"))
    

class Grade_obtained(db.Model):
    __tablename__ = "Grade_obtained"
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Text())
    
    
class Overall_management(db.Model):
    __tablename__ = "Overall_management"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("Candidate.id"))
    course_information_id = db.Column(db.Integer, db.ForeignKey("Course_information.id"))
    senior_standard_id = db.Column(db.Integer, db.ForeignKey("Senior_standard.id"))
    grade_obtained_id = db.Column(db.Integer, db.ForeignKey("Grade_obtained.id"))
    data_year_id = db.Column(db.Integer, db.ForeignKey("Data_year.id"))