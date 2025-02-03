from flask import Flask, render_template, redirect, url_for, request, flash , jsonify
from models import db, User, RoleRequirement
from flask_bcrypt import Bcrypt
import time , os
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_dropzone import Dropzone
from final import analyze_resume_job_fit , findResume

app = Flask(__name__)

app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] =   'postgresql://postgres:59035903@localhost:5432/Analyzer' #"<your database access link>"
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'application/pdf'
app.config['DROPZONE_MAX_FILE_SIZE'] = 3
app.config['DROPZONE_MAX_FILES'] = 1

bcrypt = Bcrypt()
bcrypt.init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

dropzone = Dropzone(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error_message = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            user.is_active = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Login Successfull !")
            # Redirect to dashboard upon successful login
            return redirect(url_for('dashboard'))
        else:
            error_message = 'Invalid email or password, please try again.'
            # return "Invalid email or password, please try again."

    return render_template('login.html', error_message=error_message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = ''
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        email_id = User.query.filter_by(email=email).first()
        user_name = User.query.filter_by(username=name).first()

        if user_name:
            error_message = 'This username is already registered !, please try again with different username.'
        elif email_id:
            error_message = 'This email is already registered !, please try again with different email address.'
        elif len(password) < 8 or not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password) or not any(char in '!@#$%&*' for char in password):
            error_message = 'password must be 8 character long and must contains atleast one alphabate , one digit and one special chatacter (!@#$%&*)'
        elif password != confirm_password:
            error_message = 'password do not match , please try again'
        else:
            hashed_password = bcrypt.generate_password_hash(
                password).decode('utf-8')
            new_user = User(username=name, email=email,
                            password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration Successfull !  Redirecting to the login page ...')
            # return redirect(url_for('success'))
    return render_template('register.html', error_message=error_message)


@app.route('/success')
def success():
    time.sleep(3)
    return (redirect(url_for('login')))

@app.route('/dashboard')
@login_required
def dashboard():
    roles = RoleRequirement.query.all()
    return render_template('dashboard.html', roles=roles)


global_role_id = None
global_role_description = None


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    global global_role_id  
    role_id = request.form.get('role')
    global_role_id = role_id
    role = RoleRequirement.query.get(role_id)
    print(f"Received role_id: {role_id}")
    print(f"Received global_role_id: {global_role_id}")
    print(f"Received role: {role}")

    if 'file' not in request.files:
        print("No file part in the request")
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    print(f"Received file: {file.filename}")

    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400

    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_path = os.path.join(upload_folder, file.filename)
    print(f"Saving file to: {file_path}")
    file.save(file_path)

    return jsonify({'success': True, 'file_path': file_path , 'message' : 'Role_I'})



@app.route('/role_description' , methods = ['GET'])
def role_description():
    global global_role_id
    global global_role_description
    if global_role_id:
        role = RoleRequirement.query.get(global_role_id)
        if role:
            global_role_description = role.description
            print('role description :' , global_role_description)
            return jsonify({'role_id' : global_role_id , 'role_description' : global_role_description})
        else:
            return jsonify({'error' : 'role not found'}) , 404
    else:
        return jsonify({'error' : 'global role id not found'}) , 400


@app.route('/logout')
def logout():
    user = current_user
    user.is_active = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))


@app.route('/process_resume', methods = ['GET'])
def process_resume():
    role_description()
    resume = findResume()
    global global_role_description
    print("here is the global des-----" , global_role_description)
    description = global_role_description
    if resume != '' and description != '':
        result = analyze_resume_job_fit(resume , description)
        print(result)
        return result
    else:
        return jsonify({'Error' : 'Error procesiing resume'})
    
@app.route('/description', methods = ['GET','POST']) 
def description():
    error_message = ''
    if request.method == 'POST':
        role_name = request.form['role_name']
        description = request.form['description']
        temp_role_name = RoleRequirement.query.filter_by(role_name = role_name).first()
        if temp_role_name:
            error_message = 'Role already exists !  please try again with different role name'
        else:
            role = RoleRequirement(role_name = role_name , description = description)
            db.session.add(role)
            db.session.commit()
            flash('Role added successfully !')
    return render_template('description.html' , error_message = error_message)  


def printgd():
    global global_role_description
    print("here is the value of ----- description: " , global_role_description)
printgd()

if __name__ == '__main__':
    app.run(debug=True)

