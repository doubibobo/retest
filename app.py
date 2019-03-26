import os
import platform
import pymysql
import json
import random
import gevent

from flask import Flask, copy_current_request_context
from flask import render_template, request, current_app, jsonify
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_session import Session

from mailmerge import MailMerge

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
        host = "127.0.0.1"
        user = "root"
        password = "Ph!7fz2ayn[EV1Tu"
        db = "test"
        self.con = pymysql.connect(
            host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    # 添加学生信息
    def student_adding(self, student_id, name, student_type):
        # 查询该考生是否已经录入，以考生号为准
        select_sql = "select count(id) as number from test_student where test_id = " + student_id
        result = self.cur.execute(select_sql)
        message = self.cur.fetchall()
        if message[0]['number'] == 1:
            print("重复添加")
            return 300
        sql = "insert into test_student(test_id, test_name,test_type) values ('" + student_id + "','" + name + "','" + student_type + "')"
        self.cur.execute(sql)
        self.con.commit()
        return 200

    # 删除学生
    def student_deleting(self, student_id):
        sql = "delete from test_student where id = " + student_id
        result = self.cur.execute(sql)
        self.con.commit()
        return result

    # 查询学生总数
    def count_students(self):
        sql = "select count(test_id) as number from" \
              " test_student order by test_id"
        self.cur.execute(sql)
        result = self.cur.fetchall()
        return result[0]['number']

    # 列出学生信息
    def list_students(self, start, size, test_card):
        if test_card is None:
            sql = "select id, test_id, test_name, test_type, test_room, test_number from" \
                  " test_student order by test_id limit %s, %s" % (start, size)
            print(sql)
        else:
            sql = "select test_id, test_type, test_room, test_number from test_student where test_name = '" + test_card + "\'"
        self.cur.execute(sql)
        result = self.cur.fetchall()
        return result

    # 查看所有考生的选题信息
    def list_chose(self, test_room):
        sql = "select test_student.test_id, test_student.test_name, test_student.test_type, " \
              "test_student.test_room, test_student.test_number," \
              "test_student.test_paper1, test_paper.paper_question as paper1_question, " \
              "test_student.test_paper2, a.paper_question as paper2_question " \
              "from (select * from test_paper) as a " \
              "right join test_student on test_paper2 = a.id " \
              "left join test_paper on test_paper1 = test_paper.id "
        if test_room == "all":
            sql += "order by test_room asc;"
            self.cur.execute(sql)
        else:
            sql += "where test_student.test_room = '%s' order by test_room asc;" % test_room
            print(sql)
            self.cur.execute(sql)
        result = self.cur.fetchall()
        return result

    # 添加题目
    def question_adding(self, content, which):
        sql = "insert into test_question(question_content, question_type) values (\'" + content + '\', ' + which + ")"
        result = self.cur.execute(sql)
        self.con.commit()
        return result

    # 删除题目
    def question_deleting(self, question_id):
        sql = "delete from test_question where id = " + question_id
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
            sql = "INSERT INTO test_paper(paper_question, paper_flag) VALUES('" + s + "',0)"
            self.cur.execute(sql)
            self.con.commit()
            cou += 1

    # 查询每套题的具体题目
    def paper_list_everyone(self, paper_id):
        """根据题号到试卷表中找到该套题包含了哪些题目"""
        paper_content = "select paper_question from test_paper where id= " + paper_id
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
            Q.append(content[0])
        return Q

    # 根据学生的准考证号和抽取到的试题编号汇总学生的信息
    def student_information(self, student_id, paper_id, test_room, test_number, test_name, test_type):

        """ 判断考生选取的题目是否可选，判断考生是否已经选题
        """
        print(paper_id + " " + student_id)
        self.cur.execute("select paper_flag from test_paper where id = " + paper_id)
        is_choose_message = self.cur.fetchall()
        print(is_choose_message)
        if is_choose_message[0]['paper_flag'] == 1:
            return None

        self.cur.execute("select test_paper1, test_paper2 from test_student where test_id = '" + student_id + "'")
        is_student_choose_message = self.cur.fetchall()
        print(is_student_choose_message)

        """ 根据考生抽取到的题号更新考生表
            如果sql语句中的条件值是变量，变量要定义成str类型，在sql语句中用'"+s+"'表示
            更新题目的状态
        """
        if is_student_choose_message[0]['test_paper1'] != 0:
            if is_student_choose_message[0]['test_paper2'] != 0:
                return None
            else:
                update = "update test_student set test_paper2 = '" + paper_id + "', test_room = '" \
                         + test_room + "', test_number = '" + test_number + "' where test_id='" + student_id + "' "
        else:
            update = "update test_student set test_paper1 = '" + paper_id + "', test_room = '" \
                     + test_room + "', test_number = '" + test_number + "' where test_id='" + student_id + "' "
        self.cur.execute(update)
        self.con.commit()

        paper_update = "update test_paper set paper_flag = 1 where id = " + paper_id
        self.cur.execute(paper_update)
        self.con.commit()

        Q = self.paper_list_everyone(paper_id)

        # 将选题信息写入word文档
        doxManagement = DoxManagement()
        doxManagement.born_word(test_name, test_type, test_number,
                                Q[0]['question_content'], Q[1]['question_content'], Q[2]['question_content'],
                                Q[3]['question_content'], Q[4]['question_content'],
                                student_id)
        gevent.spawn(copy_current_request_context(doxManagement.born_pdf(student_id)))
        return Q

    # 获得所有题目的状态信息
    def paper_list_information(self):
        sql = "select id, paper_flag from test_paper"
        self.cur.execute(sql)
        content = self.cur.fetchall()
        return content

    # 获得所有题目列表
    def get_paper_question(self, start, size, count):
        if count is None:
            sql = 'select a.id, a.paper_flag, a.question1, a.question2, a.question3, a.question4, a.question5,' \
                  ' b.question_content as content_1, b.question_code as code_1,' \
                  ' c.question_content as content_2, c.question_code as code_2,' \
                  ' d.question_content as content_3, d.question_code as code_3,' \
                  ' e.question_content as content_4, e.question_code as code_4,' \
                  ' f.question_content as content_5, f.question_code as code_5' \
                  ' from (select test_paper.id, test_paper.paper_flag, ' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 1), ";", -1) as question1,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 2), ";", -1) as question2,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 3), ";", -1) as question3,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 4), ";", -1) as question4,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 5), ";", -1) as question5' \
                  '       from test_paper) as a' \
                  '  left join test_question as b on question1 = b.id' \
                  '  left join test_question as c on question2 = c.id' \
                  '  left join test_question as d on question3 = d.id' \
                  '  left join test_question as e on question4 = e.id' \
                  '  left join test_question as f on question5 = f.id' \
                  '  limit %s, %s' % (start, size)
        else:
            sql = 'select count(a.id) as number' \
                  ' from (select test_paper.id, test_paper.paper_flag, ' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 1), ";", -1) as question1,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 2), ";", -1) as question2,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 3), ";", -1) as question3,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 4), ";", -1) as question4,' \
                  '         substring_index(substring_index(test_paper.paper_question, ";", 5), ";", -1) as question5' \
                  '       from test_paper) as a' \
                  '  left join test_question as b on question1 = b.id' \
                  '  left join test_question as c on question2 = c.id' \
                  '  left join test_question as d on question3 = d.id' \
                  '  left join test_question as e on question4 = e.id' \
                  '  left join test_question as f on question5 = f.id'
        self.cur.execute(sql)
        content = self.cur.fetchall()
        return content

    # 获得题目的信息
    def get_question_items(self, start, size, count):
        if count is None:
            sql = 'select id, question_type, question_code, question_content from test_question limit %s, %s' % (
                start, size)
        else:
            sql = 'select count(id) as number from test_question'
        self.cur.execute(sql)
        content = self.cur.fetchall()
        return content


class DoxManagement:

    def __init__(self):
        print(platform.system())
        self.path = os.path.abspath('.') + "/static/word"
        self.pdf = os.path.abspath('.') + "/static/pdf"
        self.template = "test_template.docx"
        self.document_1 = MailMerge(self.template)

    # 文档生成
    def born_word(self, student_name, student_type, room_number,
                  question_1, question_2, question_3, question_4, question_5,
                  student_number):
        print("Fields included in {}: {}".format(self.template, self.document_1.get_merge_fields()))
        self.document_1.merge(
            test_name=student_name,
            test_type=student_type,
            test_number=room_number,
            question_1=question_1,
            question_2=question_2,
            question_3=question_3,
            question_4=question_4,
            question_5=question_5
        )
        # 普通 word 文档生成
        self.document_1.write(self.path + '/paper-' + student_number + '.docx')

    def born_pdf(self, student_number):
        command = "libreoffice --headless --convert-to pdf --outdir " + self.pdf + " " + self.path + '/paper-' + student_number + '.docx'
        print(command)
        try:
            status = os.system(command)
            print(status)
        except:
            print("libreoffice convert word to pdf is wrong")
        finally:
            print("libreoffice convert word to pdf")


class User(UserMixin):
    pass


# 用户记录表
users = [
    {'username': 'mishu001', 'password': 'hzau-sky-mishu-001'},
    {'username': 'mishu002', 'password': 'hzau-sky-mishu-002'},
    {'username': 'mishu003', 'password': 'hzau-sky-mishu-003'},
    {'username': 'mishu004', 'password': 'hzau-sky-mishu-004'},
    {'username': 'mishu005', 'password': 'hzau-sky-mishu-005'},
    {'username': 'mishu006', 'password': 'hzau-sky-mishu-006'},
    {'username': 'mishu007', 'password': 'hzau-sky-mishu-007'},
    {'username': 'mishu008', 'password': 'hzau-sky-mishu-008'},
    {'username': 'mishu009', 'password': 'hzau-sky-mishu-009'}
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


# 下载试卷接口
@app.route('/download/<paper>', methods=['GET'])
@login_required
def paper_download(paper):
    print(paper)
    print("word/paper/" + paper + ".docx")
    return current_app.send_static_file("word/paper-" + paper + ".docx")


# 查看试卷接口
@app.route('/download/pdf/<paper>', methods=['GET'])
@login_required
def pdf_download(paper):
    print(paper)
    return current_app.send_static_file("pdf/paper-" + paper + ".pdf")


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
        else:
            return jsonify({
                "status": 201,
                "message": "用户名或密码错误！"
            })
    else:
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
    tester = json.loads(request.form.get("data"))['tester']
    database = Database()
    results = jsonify({
        "status": 200,
        "list": database.list_students(None, None, tester)
    })
    return results


# 考生选题及页面展示
@app.route('/question', methods=["GET", "POST"])
@login_required
def retest_question():
    if request.method == "POST":
        login_message = json.loads(request.form.get("data"))
        # 考生号
        test_number = login_message['test_number']
        # 考场号
        test_room = login_message['test_room']
        # 座号
        test_location = login_message['test_location']
        # 选题
        paper_number = login_message['paper_number']
        # 姓名
        test_name = login_message['test_name']
        # 类型
        test_type = login_message['test_type']

        database = Database()
        result = database.student_information(test_number, paper_number, test_room,
                                                                                 test_location,
                                                                                 test_name, test_type)
        if result is None:
            return jsonify({
                "status": 300,
                "error": "考生已经选过题目或该题目已被选"
            })
        else:
            return jsonify({
                "status": 200,
                "lists": result
            })
    return render_template('question.html')


# 考生选题展示页面
@app.route('/list', methods=["GET", "POST"])
@login_required
def list_student():
    if request.method == "POST":
        test_room = json.loads(request.form.get("data"))['test_room']
        database = Database()
        results = jsonify({
            "status": 200,
            "lists": database.list_chose(test_room)
        })
        return results
    return render_template('list.html')


# 获得所有题目的状态信息
@app.route('/paper', methods=['GET'])
@login_required
def list_paper_message():
    database = Database()
    results = jsonify({
        "status": 200,
        "lists": database.paper_list_information()
    })
    return results


# 添加学生信息
@app.route('/student', methods=['GET', 'POST', 'PATCH'])
@login_required
def student_adding():
    if request.method == "POST":
        database = Database()

        student_id = request.form['id']
        which = request.form['name']
        student_type = request.form['type']

        if student_id == "" or which == "" or student_type == "":
            return "error"

        status = database.student_adding(student_id, which, student_type)
        results = jsonify({
            "status": status,
        })
        return results
    if request.method == "PATCH":
        data = json.loads(request.form.get("data"))
        database = Database()
        results = jsonify({
            "status": 200,
            "lists": database.list_students(data['start'], data['size'], None),
            "number": database.count_students()
        })
        return results
    return render_template('student.html')


# 试卷内容的查询
@app.route('/paper/list', methods=['GET', 'PATCH'])
@login_required
def paper_list():
    if request.method == "PATCH":
        data = json.loads(request.form.get("data"))
        database = Database()
        results = jsonify({
            "status": 200,
            "lists": database.get_paper_question(data['start'], data['size'], None),
            "number": database.get_paper_question(None, None, True)[0]['number']
        })
        return results
    return render_template('paper.html')


# 技术人员添加一道题目
@app.route('/insert', methods=["GET", "POST"])
@login_required
def question_insert():
    if request.method == "POST":
        content = request.form['content']
        which = request.form['type']
        if content == "" or which == "":
            return "error"
        database = Database()
        results = jsonify({
            "status": 200,
            "lists": database.question_adding(content, which)
        })
        return results
    return render_template('add.html')


# 题目删除操作
@app.route('/question/delete/<question_id>', methods=["DELETE"])
@login_required
def delete_question(question_id):
    database = Database()
    results = jsonify({
        "status": 200,
        "lists": database.question_deleting(question_id)
    })
    return results


# 学生删除操作
@app.route('/student/delete/<student_id>', methods=["DELETE"])
@login_required
def delete_student(student_id):
    database = Database()
    results = jsonify({
        "status": 200,
        "lists": database.student_deleting(student_id)
    })
    return results


# 获得所有题目的信息
@app.route('/question/list', methods=["PATCH"])
@login_required
def test_question_lists():
    data = json.loads(request.form.get("data"))
    database = Database()
    results = jsonify({
        "status": 200,
        "lists": database.get_question_items(data['start'], data['size'], None),
        "number": database.get_question_items(None, None, True)[0]['number']
    })
    return results


if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    app.run(threaded=True)
