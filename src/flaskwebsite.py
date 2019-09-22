# from flask import Flask, render_template

# # app = Flask(__name__)

# # @app.route("/")
# # def home():
# #     return render_template("upload.html")
    
# # # @app.route("/about")
# # # def about():
# # #     return render_template("about.html")
    
# # if __name__ == "__main__":
# #     app.run(debug=True)



# from flask import Flask, render_template
# # from werkzeug import secure_filename
# app = Flask(__name__)

# @app.route('/')
# def upload_file():
#    return render_template('upload.html')
	
# # @app.route('/uploader', methods = ['GET', 'POST'])
# # def upload_file():
# #    if request.method == 'POST':
# #       f = request.files['file']
# #       f.save(secure_filename(f.filename))
# #       return 'file uploaded successfully'
		
# if __name__ == '__main__':
#    app.run(debug = True)



from flask import render_template,Flask
from flask import request, redirect, url_for,flash
from werkzeug.utils import secure_filename
# from app import app
import os
app = Flask(__name__)
# APP_ROOT = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = "/home/kayadev-gpu-2/Desktop/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def tmrf():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
    return 'file uploaded successfully'


if __name__ == '__main__':
   app.run(debug = True)










