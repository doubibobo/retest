import json
import os
import random

from flask import render_template, request, current_app, jsonify, session
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import pymysql
from flask_session import Session

app = Flask(__name__)

bootstrap = Bootstrap(app)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
Session(app)

login_manager = LoginManager(app)
login_manager.login_view = 'teacher_login'
login_manager.login_message = '未授权用户，请登陆后进行访问'
login_manager.login_message_category = "info"


# 设置登录视图的名称，如果一个未登录用户请求一个只有登录用户才能访问的视图，
# 则闪现一条错误消息，并重定向到这里设置的登录视图。
# 如果未设置登录视图，则直接返回401错误。
# 设置当未登录用户请求一个只有登录用户才能访问的视图时，闪现的错误消息的内容，
# 默认的错误消息是：Please log in to access this page.。
# 设置闪现的错误消息的类别


class Database:
    # 初始化配置
    def __init__(self):
        host = "39.108.154.79"
        user = "root"
        password = "SiCong>1"
        db = "role"
        self.con = pymysql.connect(
            host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    # 列出学生信息
    def list_students(self, test_card):
        if test_card is None:
            sql = "select test_id, test_name, test_type, test_room, test_number from test_student"
        else:
            sql = "select test_name, test_type from test_student where test_id = \'" + test_card + "\'"
        self.cur.execute(sql)
        result = self.cur.fetchall()
        return result

    # 查看所有考生的选题信息
    def list_chose(self):
        self.cur.execute("select test_student.id, test_type, test_id, test_name, test_room, test_number, test_paper, "
                         "paper_question, paper_flag "
                         "from test_paper, test_student "
                         "where test_student.test_paper = test_paper.id "
                         "order by test_room asc")
        result = self.cur.fetchall()
        return result

    # 添加题目
    def question_adding(self, content, which):
        sql = "insert into test_question(question_content, question_type) values (\'" + content + '\', ' + which + ")"
        result = self.cur.execute(sql)
        self.con.commit()
        return result

    # 查找所有题目
    def question_listing(self):
        self.cur.execute(
            "select id, question_content, question_type from test_question"
        )
        result = self.cur.fetchall()
        return result

    # 根据类型查找所有的题目
    def question_listing_with_type(self, which):
        self.cur.execute(
            "select id, question_content, question_type from test_question where question_type = " + which
        )
        result = self.cur.fetchall()
        return result

    # 为每套题目生成具体的5个问题
    def add_data(self):
        cou = 1
        while cou <= 100:
            a = random.randint(1, 4)
            b = random.randint(5, 6)
            c = random.randint(7, 8)
            d = random.randint(9, 10)
            e = random.randint(11, 12)
            s = str(a) + ";" + str(b) + ";" + str(c) + ";" + str(d) + ";" + str(e)
            # print(s)
            sql = "INSERT INTO test_paper(paper_question,paper_flag) VALUES('" + s + "',0)"
            self.cur.execute(sql)
            self.con.commit()
            cou += 1

    # 根据学生的准考证号和抽取到的试题编号汇总学生的信息
    def student_information(self, student_id, paper_id, test_room, test_number):
        """ 根据考生抽取到的题号更新考生表
            如果sql语句中的条件值是变量，变量要定义成str类型，在sql语句中用'"+s+"'表示
        """
        update = "update test_student set test_paper = '" + paper_id + "', test_room = '" \
                 + test_room + "', test_number = '" + test_number + "' where test_id='" + student_id + "' "
        self.cur.execute(update)
        self.con.commit()

        """根据题号到试卷表中找到该套题包含了哪些题目"""
        paper_content = "select paper_question from test_paper where id= " + paper_id
        print(paper_content)
        self.cur.execute(paper_content)
        content = self.cur.fetchall()
        question = content[0]

        """将字符串值转化为整数"""
        l = len(question['paper_question'])
        s = ""
        A = []
        cou = 1
        for i in range(l):
            if question['paper_question'][i] != ";":
                s = s + question['paper_question'][i]
            else:
                A.append(int(s))
                s = ""
                cou += 1
        A.append(int(s))

        """到question表中获取每一道题目的具体内容"""
        Q = []
        for i in A:
            i = str(i)
            sql = "select question_content from test_question where id ='" + i + "' "
            self.cur.execute(sql)
            content = self.cur.fetchall()
            Q.append(content)
        return Q


class User(UserMixin):
    pass


# 用户记录表
users = [
    {'username': 'hzausky001', 'password': 'hzausky001'},
    {'username': 'hzausky002', 'password': 'hzausky002'},
    {'username': 'hzausky003', 'password': 'hzausky003'},
    {'username': 'hzausky004', 'password': 'hzausky004'},
    {'username': 'hzausky005', 'password': 'hzausky005'}
]


# 通过用户名，获取用户记录，如果不存在，则返回None
def query_user(username):
    for user in users:
        if user['username'] == username:
            return user


# 如果用户名存在则构建一个新的用户类对象，并使用用户名作为ID
# 如果不存在，必须返回None
@login_manager.user_loader
def load_user(username):
    if query_user(username) is not None:
        curr_user = User()
        curr_user.id = username
        return curr_user


# 如果用户名存在则构建一个新的用户类对象，并使用用户名作为ID
# 如果不存在，必须返回None
@login_manager.request_loader
def load_user_from_request(user_request):
    username = user_request.args.get('token')
    if query_user(username) is not None:
        test_current_user = User()
        test_current_user.id = username
        return test_current_user


# 图标加载函数
@app.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('favicon.ico')


# 图片加载函数
@app.route('/img/<picture>', methods=["GET"])
def get_picture(picture):
    print(picture)
    return current_app.send_static_file("img/" + picture)


@app.errorhandler(404)
def page_not_found(e):
    render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    render_template('500.html'), 500


@app.route('/login', methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        username = request.form.get('username')
        user = query_user(username)
        # 验证表单中提交的用户名和密码
        if user is not None and request.form['password'] == user['password']:
            login_current_user = User()
            login_current_user.id = username

            # 通过Flask-Login的login_user方法登录用户
            login_user(login_current_user)

            return jsonify({
                "status": 200,
                "message": "登陆成功！"
            })
        return jsonify({
            "status": 201,
            "message": "用户名或密码错误！"
        })
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template("login.html")


@app.route('/')
@login_required
def hello_world():
    return 'Hello %s!' % current_user.get_id()


# 根据考生号查找考生姓名
@app.route('/find/tester', methods=["POST"])
@login_required
def find_tester():
    print(json.loads(request.form.get("data")))
    tester = json.loads(request.form.get("data"))['tester']
    database = Database()
    results = jsonify({
        "status": 200,
        "list": database.list_students(tester)
    })
    return results


# 考生选题及页面展示
@app.route('/question', methods=["GET", "POST"])
@login_required
def retest_question():
    if request.method == "POST":
        login_message = json.loads(request.form.get("data"))
        test_number = login_message['test_number']
        test_room = login_message['test_room']
        test_location = login_message['test_location']
        paper_number = login_message['paper_number']
        database = Database()
        results = jsonify({
            "status": 200,
            "lists": database.student_information(test_number, paper_number, test_room, test_location)
        })
        return results
    return render_template('question.html')


# 技术人员添加一道题目
@app.route('/insert', methods=["GET", "POST"])
@login_required
def question_insert():
    if request.method == "POST":
        content = request.form['content']
        which = request.form['type']
        database = Database()
        results = jsonify({
            "status": 200,
            "lists": database.question_adding(content, which)
        })
        return results
    return render_template('add.html')


if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    app.run(debug=True)
