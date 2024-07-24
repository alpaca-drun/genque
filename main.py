from flask import Flask, request, render_template, url_for, redirect, session, jsonify
import boto3
import json
import logging
import pymysql
from datetime import datetime
import os

from botocore.exceptions import ClientError
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경 변수 로드
load_dotenv()

# API_KEY 가져오기
api_key = os.getenv('API_KEY')

# OpenAI API 키 설정
os.environ['OPENAI_API_KEY'] = api_key


# model = ChatOpenAI(model="gpt-4o", temperature=0)  # 또는 원하는 모델 선택


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=api_key,
)

def generate_text(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션 암호화를 위한 시크릿 키 설정


@app.route('/')
def frontpage():
    return render_template('index.html')





@app.route('/passage_gen')
def passage_gen():
    db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
    # 커서 생성
    cursor = db.cursor()
    cursor.execute("SELECT id, title, passages FROM passages")
    results = cursor.fetchall()
    cursor.close()
    db.close()
    print(results)

    return render_template('passage_gen.html', passages = results)


@app.route('/create3', methods=['GET', 'POST'])
def create3():
    if request.method == 'POST':
        level = request.form['level']
        t1 = request.form['text_input']
        t2 = request.form['text_input2']
        t2_1 = request.form['text_input2_1']
        t2_2 = request.form['text_input2_2']
        t3 = request.form['text_input3']
        t3_1 = request.form['text_input3_1']
        t3_2 = request.form['text_input3_2']
        
        now = datetime.now()
        time = now.strftime('%Y-%m-%d %H:%M:%S')

        # topic = f'다음 내용에 대해 영어로 답변해줘 한국 고등학생들이 푸는 영어 문제의 지문을 생성해줘. 응답은 안내문구 없이 결과만 출력해줘. 주제는 {t1} 이고 지문의 전개 순서 다음과 같이 작성해줘 "{t2}, {t2_1}, {t2_2}, {t3}, {t3_1}, {t3_2}" '
        # response = retrieve(topic)
        
        user_prompt = f'''
        다음 내용에 대해 영어로 답변해줘 한국 고등학생들이 푸는 영어 문제의 지문을 생성해줘. 
        응답은 안내문구 없이 결과만 출력해줘.
        주제는 {t1} 이고 지문의 전개 순서 다음과 같이 작성해줘 
        "{t2}, {t2_1}, {t2_2}, {t3}, {t3_1}, {t3_2}"
        난이도는 {level}로 설정하고 만들어진 문장에서 어려운 단어 3개를 찾아서 알려줘

        결과 출력 형식은 
        제목
        ///
        본문
        ///
        어려운 단어 1 : nn
        ///
        어려운 단어 2 : nn
        ///
        어려운 단어 3 : nn
        형식으로 출력해줘  
        '''
        response = generate_text(user_prompt)
        print(response)
        # response_text = response[0]['text']
        title = response.split('///')[0]
        content = response.split('///')[1].lstrip()
        word1 = response.split('///')[2].split(': ')[1]
        word2 = response.split('///')[3].split(': ')[1]
        word3 = response.split('///')[4].split(': ')[1]
        print(word1)
        print(word2)
        print(word3)
        category = '객관식 문제'
        owner = 'user1'
        lang = '영어'
        config = '지문1'
        update_date = time
        length = len(content)
        

        db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        # 커서 생성
        cursor = db.cursor()
        # 파라미터화된 쿼리 작성
        query = "INSERT INTO passages (passages, title, category, owner, lang, config, update_date, word1, word2, word3, level, length) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (content, title, category, owner, lang, config, update_date, word1, word2, word3, level, length))
        # print('query')
        # 변경사항 커밋
        db.commit()
        pid = cursor.lastrowid

        # 연결 종료
        cursor.close()
        db.close()
        

        session['text'] = content
        session['pid'] = pid
        
        return redirect(url_for('question_gen'))
        # return render_template('create3.html', user_input=response)
    return render_template('create3.html', user_input='')


@app.route('/success')
def success():
    response_text= session.get('text')
    return render_template('success.html', user_input = response_text)


# 텍스트 수정 후 저장
@app.route('/save_passage', methods=['POST'])
def save_passage():
    # JSON 데이터를 받아옴
    data = request.get_json()
    passage = data.get('passage')
    id = data.get('id')
    print(data)
    if id == 'new_index':
        print('if')

        now = datetime.now()
        time = now.strftime('%Y-%m-%d %H:%M:%S')
        title = data.get('title')
        # title = 'title'
        category = '객관식 문제'
        owner = 'user1'
        lang = '영어'
        config = '지문1'
        update_date = time

        
        db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        # 커서 생성
        cursor = db.cursor()
        # 파라미터화된 쿼리 작성
        query = "INSERT INTO passages (passages, title, category, owner, lang, config, update_date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (passage, title, category, owner, lang, config, update_date))
        # print('query')
        # 변경사항 커밋
        db.commit()


        passageID = id
        updated_html = render_template('question_gen.html', passage=passage, passageID=passageID)
    
        return jsonify({'html': updated_html})
    
    else :
        #print('else')
        #print(id)
        id = str(int(id) + 1)

        now = datetime.now()
        time = now.strftime('%Y-%m-%d %H:%M:%S')

        db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        # 커서 생성
        cursor = db.cursor()
        # 파라미터화된 쿼리 작성
        query = "UPDATE passages SET passages = %s, update_date = %s WHERE id = %s"
        cursor.execute(query, (passage, time, id))
        # print('query')
        # 변경사항 커밋
        db.commit()

        # 연결 종료
        cursor.close()
        db.close()

        # 성공적으로 처리되었음을 응답
        return jsonify({'status': 'success', 'message': 'Passage saved successfully'})







@app.route('/question_gen', methods=['GET', 'POST'])
def question_gen():
    # question.html의 '불러오기'로부터 POST
    # 지문의 본문과 id를 전달받음
    if request.method == 'POST':
        pid = request.form['action1'] # passages 본문
        db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        cursor = db.cursor()
        # SQL 쿼리 작성
        sql = "SELECT passages FROM passages WHERE id = %s"
        # 쿼리 실행
        cursor.execute(sql, (pid,))
        # 결과 가져오기
        results = cursor.fetchone()
        cursor.close()
        db.close()
        result = results[0]

        # question_gen.html으로 본문과 id 값 전달
        return render_template('question_gen.html', passage = result, passageID = pid)
    else : 
        response_text = session.get('text')
        # db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        # # 커서 생성
        # cursor = db.cursor()
        # cursor.execute("SELECT id, title, passages FROM passages")
        # results = cursor.fetchall()
        # cursor.close()
        # db.close()

        pid = session.get('pid')
        
        # print(response_text )
        session['text'] = ''
        #print('results is')
        #print(results)

        
        return render_template('question_gen.html', passage = response_text, passageID = pid)







@app.route('/question', methods=['GET', 'POST'])
def question():
    db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
    # 커서 생성
    cursor = db.cursor()
    cursor.execute("SELECT id, title, passages FROM passages")
    results = cursor.fetchall()
    cursor.close()
    db.close()
    print(results)

    # question_gen.html 혹은 question.html 에서 /question으로 post 함 
    if request.method == 'POST':
        pid = request.form['action1'] # 지문 번호
        print('pid is')
        print(pid)
        db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        cursor = db.cursor()
        # SQL 쿼리 작성
        sql = "SELECT passages FROM passages WHERE id = %s"
        # 쿼리 실행
        cursor.execute(sql, (pid,))
        # 결과 가져오기
        result = cursor.fetchone()
        print(result)
        # result는 딕셔너리 형태로 반환됩니다. 예: {'passage': 'your_passage_value'}
        q1 = result[0]

        print('pid is')
        print(pid)
        #q1 = selected_value[2]
        print('q1 is')
        print(q1)
        q2 = request.form['action2'] # 문제 유형 

        if q2 == "주제 찾기":
            category_message = '윗 글의 주제로 가장 적절한 것은?'
        if q2 == "주장 찾기":
            category_message = '윗 글의 주장으로 가장 적절한 것은?'

        topic = f'''
        {q2} 형식에 맞게 {q1}을 이용한 5지 선다 문제를 만들어줘

        답변 형식은 
        {category_message}
        ///
        1. 1번답안
        ///
        2. 2번답안
        ///
        3. 3번답안
        ///
        4. 4번답안
        ///
        5. 5번답안
        ///
        정답 : n번
        ///
        해설 : 해설내용
        ///
        예상 정답률 : n%
        ///
        선택지별 예상 채택률 : 1) n%, 2) n%, 3) n%, 4) n%, 5) n%
        
        형식으로 만들어줘, 선택지별 예상 채택률 총 합은 100%로 만들어줘
        어려운 지문일수록 예상 채택률을 낮게, 쉬운 지문일수록 예상 채택률을 높게 설정해줘
        '''

        response = generate_text(topic)
        result = response.split('///')
        print(result)
        ans1 = result[1].strip()
        ans2 = result[2].strip()
        ans3 = result[3].strip()
        ans4 = result[4].strip()
        ans5 = result[5].strip()
        ans_num = result[6].strip().split(': ')[-1]
        explain = result[7].strip().split(': ')[1]
        correct = result[8].strip().split(': ')[1]
        select1 = result[9].strip().split(') ')[1].split(',')[0]
        select2 = result[9].strip().split(') ')[2].split(',')[0]
        select3 = result[9].strip().split(') ')[3].split(',')[0]
        select4 = result[9].strip().split(') ')[4].split(',')[0]
        select5 = result[9].strip().split(') ')[5].split(',')[0]

        category = q2

        db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
        # 커서 생성
        cursor = db.cursor()
        # 파라미터화된 쿼리 작성
        query = "INSERT INTO question (question, pid, category, category_message, ans1, ans2, ans3, ans4, ans5, ans_num, exp, correct, select1, select2, select3, select4, select5) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (response, pid, category, category_message, ans1, ans2, ans3, ans4, ans5, ans_num, explain, correct, select1, select2, select3, select4, select5))
        # print('query')
        # 변경사항 커밋
        db.commit()
        last_inserted_id = cursor.lastrowid
        # 연결 종료
        cursor.close()
        db.close()

        session['question'] = last_inserted_id
        
        return redirect(url_for('success_que'))
        
    # question.html의 불러오기의 passages로 값 전달
    return render_template('question.html', passages = results)



@app.route('/success_que')
def success_que():
    qid = session.get('question')
    db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
    # 커서 생성
    cursor = db.cursor()

    cursor.execute("SELECT pid, category, category_message, exp, ans1, ans2, ans3, ans4, ans5, ans_num, select1, select2, select3, select4, select5, correct FROM question WHERE qid = %s", (qid))
    question = cursor.fetchall()
    print('question is')
    print(question)
    pid = question[0][0]
    print('pid is')
    print(pid)
    cursor.close()

    cursor = db.cursor()

    cursor.execute("SELECT passages, title, lang, category, config, owner  FROM passages WHERE id = %s", (pid))
    passage = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('success_question.html', passage = passage, question = question )



@app.route('/question_home', methods=['GET', 'POST'])
def question_home():
    
    db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
    # 커서 생성
    cursor = db.cursor()
    cursor.execute("SELECT id, title, lang, category, config, owner, update_date FROM passages")
    results = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('question_home.html', results = results)



@app.route('/question_content/<id>', methods=['GET', 'POST'])
def question_content(id):
    
    db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
    # 커서 생성
    cursor = db.cursor()
    cursor.execute("SELECT title, passages, lang, category, config, owner, update_date, word1, word2, word3, level, length FROM passages WHERE id = %s", (id))
    results = cursor.fetchall()
    cursor.execute("SELECT question, category, category_message, exp, ans1, ans2, ans3, ans4, ans5, ans_num, select1, select2, select3, select4, select5, correct FROM question WHERE pid = %s", (id))
    question = cursor.fetchall()

    cursor.close()
    db.close()
    # print(id)
    #if not question:


    return render_template('question_content.html', results = results, question = question)



@app.route('/save', methods=['GET', 'POST'])
def save():
    db = pymysql.connect(host='localhost', port = 3300, user='root', password='8800', db="genque", charset='utf8')
    # 커서 생성
    cursor = db.cursor()
    cursor.execute("SELECT id, title, lang, category, config, owner, update_date FROM passages")
    results = cursor.fetchall()
    cursor.close()
    db.close()
    # print(results[5][0])
    return render_template('save.html', results = results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)