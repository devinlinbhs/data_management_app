from myapp.route import db
# db is defined at route

# Setting up all the tables for the SQLAlchemy
class Candidate(db.Model):
    __tablename__ = "Candidate"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    gender = db.Column(db.Text())
    student_year_level = db.Column(db.Integer())
    ethnicity = db.Column(db.Text())
    attendance = db.Column(db.Integer())
    course = db.Column(db.Text())
    data_year_id = db.Column(db.Integer())
    # Only 1 foreign key from "Data_year" table
    # With 1 primary key

    
class Standard(db.Model):
    __tablename__ = "Standard"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    year_level = db.Column(db.Integer())
    assessment_type = db.Column(db.Text())
    standard_code = db.Column(db.Integer())
    course = db.Column(db.Text())
    standard_type = db.Column(db.Text())

    
    
class Result(db.Model):
    __tablename__ = "Result"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("Candidate.id"))
    standard_id = db.Column(db.Integer, db.ForeignKey("Standard.id"))
    course = db.Column(db.Text())
    grade = db.Column(db.Text())
    data_year = db.Column(db.Integer())