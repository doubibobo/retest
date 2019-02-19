from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/index')
def retest_index():
    return render_template('index.html')

@app.route('/question')
def retest_question():
    return render_template('question.html')

if __name__ == '__main__':
    app.run()
