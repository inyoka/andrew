# #!flask/bin/python

import datetime
import json
import mysql.connector as SQLconn
import secret

from flask import Flask, Response, request, jsonify, render_template, url_for

app = Flask(__name__)


def connection():
    retried = 0
    connected = False
    while not connected:
        try:
            db =   SQLconn.connect(**secret.config_remote)
            dbcur = db.cursor(dictionary=True)
            connected = True
        except Exception as e:
            print ('Exception:',e)
            retried += 1
        if retried>9:
            print('Retried 10 times, please check network connection')
            return False, False
    return db, dbcur

c, cur = connection()
print ('connection', c , cur)


@app.route('/')
@app.route('/register', methods=["GET", "POST"])
def register_page():
    try:
        print(connection())
        return ("====okay. we are connected ===")

    except Exception as e:
        str = "Can't connect:%s" % str(e)
        return (str)

register_page()

def flaskAll(sql):
    c, cur = connection()
    cur.execute(sql)
    res = cur.fetchall()
    cur.close()
    return jsonify(res)

def flaskAllplain(sql):
    c, cur = connection()
    if cur:
        cur.execute(sql)
        res =cur.fetchall()
        cur.close()
        return res
    else:
        return ''

def flaskOne(sql):
    c, cur = connection()
    if cur:
        cur.execute(sql)

        res = cur.fetchone()
        cur.close()
        return jsonify(res)
    else:
        return ''

def flaskOneItem(sql, item, elseStr):
    c, cur = connection()
    if cur:
        cur.execute(sql)

        res = cur.fetchone()
        cur.close()

        try:
            if res:
                item = res[item]
                if item:
                    return item
                else:
                    return elseStr
            else:
                return elseStr
        except: return elseStr
    else:
        return elseStr

def flaskOneplain(sql):
    c, cur = connection()
    if cur:
        cur.execute(sql)
        res = cur.fetchone()
        cur.close()
        return res
    else:
        return ''

def flaskPost(sql):
    c, cur = connection()
    if cur:
        r=cur.execute(sql)
        r=c.commit()
    else:
        return ''

# @app.route("/login", methods=["GET","PUT"])
# def login():
#     render_template('login.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        return auth(request.form['user_id'], request.form['password'])

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('login.html', error=error)


@app.route("/validate", methods=["GET","PUT"])
def validate():
    content = request.get_json()

    user_id=content['user_id']
    password = content['password']
    return auth(user_id,password)

def auth(user_id, password):
    # clean up input strings
    user_id = user_id.strip()
    password = password.strip()

    if not user_id: return 'User ID missing'
    if not password: return 'Password missing'

    sql = "SELECT user_id FROM se_user WHERE user_id = '%s'" % user_id

    if not flaskOneplain(sql):
        return 'User not found'

    sql = "SELECT user_id FROM se_user \
             WHERE user_id = '%s' \
               AND user_pwd = PASSWORD('%s') " % (user_id, password)

    if not flaskOneplain(sql):
        return 'ID or password incorrect'
    else:
        return 'Valid'


@app.route("/absent_dict")
def absent_dict():
    sql="SELECT * FROM tbljenisabsen"
    res = flaskAllplain(sql)
    return jsonify(res)


@app.route("/version")#, methods=["GET","PUT"])
def version():
    sql = "SELECT ver  FROM ck_app_version"
    res = flaskOneplain(sql)
    return str(res['ver'])

@app.route("/student_details")
def student_details():
    content = request.get_json()

    sch_div = content['sch_div']
    student_id = content['student_nopin']

    sql = "SELECT * FROM siswa_%s \
            WHERE siswa_nopin='%s'" % (sch_div, str(student_id))

    res= flaskOneplain(sql)
    for row in res:# because jsonify can't serialise decimals
        res[row]=str(res[row])
        # convert id to full name - sure we can do this in sql
        if  'faith' in row: res[row]=_faith(res[row])

    return jsonify(res)


@app.route("/post_lesson_att")
def post_lesson_att():
    content = request.get_json()

    lesson_type = content['lesson_data']['lesson_type']
    if lesson_type=='excur': ts= post_excur(content) # should return a timestamp
    else: ts= post_lesson(content) # should return a timestamp

    return jsonify(ts)


def post_lesson(content):
    submitDict = content['submitDict']

    schYr = content['schYr']
    date = content['date']
    lesson_data = content['lesson_data']

    class_id = lesson_data['kelas_id']
    lesson_type = lesson_data['lesson_type']

    subject_id = lesson_data['pelajaran_id']
    instructor_id = lesson_data['instructor_id']
    sch_div = lesson_data['sch_div']
    '''
    attendance of subject classes full and moving - not formclass
    absent_code limited to H(hadir,attend) or A(absent)'''

    hadir, sakit, ijin, alpa, late = 0, 0, 0, 0, 0
    # if lesson_type == 'moving':
    #     self.absent_id = "%s%s%s%s" % (date, subject_id, class_id, instructor_id.lower())
    # else:

    absent_id = "%s%s%s%s" % (date, subject_id, class_id, instructor_id.lower())

    for student_id in submitDict:
        #rowData = submitDict[student_id]
        absent_code = submitDict[student_id]
        #absent_code = rowData['absent_code']
        if absent_code == 'A':
            sql = "REPLACE INTO siswa_absendetail%s \
                            (absen_id, absen_siswa_nopin, absen_nilai) \
                     VALUES ('%s', '%s', '%s')" % (sch_div, absent_id,
                                                   student_id, absent_code)
            flaskPost(sql)

        if absent_code == 'H': hadir += 1
        else: alpa += 1

    timestamp =_record_lesson_absence_head( sch_div, absent_id,
                                            subject_id, class_id,
                                            hadir, sakit, ijin, alpa, late,
                                            instructor_id, schYr, date)
    print('_record_lesson_absence_head:', timestamp)
    return timestamp



def post_excur(content):
    submitDict = content['submitDict']
    schYr = content['schYr']
    date = content['date']
    lesson_data = content['lesson_data']

    lesson_type = lesson_data['lesson_type']
    kelas_id = lesson_data['kelas_id']
    sch_div = lesson_data['sch_div']
    # post_excur for each student
    for student_id in submitDict:
        #print()
        absent_code = submitDict[student_id]
        #print(rowData)
        #absent_code = rowData['absent_code']
        if absent_code != 'H':
            sql = "REPLACE INTO ck_absen_siswa \
                            (sch_div, schYr, date, group_id, student_id, absent_code, lesson_type ) \
                     VALUES ('%s', %d, '%s', '%s', '%s', '%s', '%s')" % (
                            sch_div, int(schYr), date, kelas_id, student_id, absent_code, lesson_type)
            print(sql)
            flaskPost(sql)

    # record time abcense taken
    timestamp = datetime.datetime.now()
    sql = "REPLACE INTO ck_absen_head \
                (lesson_type, sch_div, schYr, date, class_id,  timestamp) \
         VALUES ('%s', '%s', %d, '%s', '%s', '%s')" % (
                 'excur', sch_div, int(schYr), date, kelas_id, timestamp)
    flaskPost(sql)
    print('post_excur   >  REPLACE INTO ck_absen_head', timestamp)
    return timestamp


@app.route("/all_groups", methods=["GET", "POST"])
def all_groups():
    content = request.get_json()

    teacher_id = content['teacher_id']
    schYr = content['schYr']

    groups = {}
    for sch_div in _sch_divs():
        groups = _add_formclasses(groups, sch_div, teacher_id, schYr)
        groups = _add_lessons(groups, sch_div, teacher_id, schYr)

        if sch_div in ['sd','smp','sma']:
            groups = _add_excuric(groups, sch_div, teacher_id, schYr)

    # {1:{lesson_type:eg.'formclass' ,display_items:[element1,element2}, data:{},
    return jsonify(groups)


@app.route("/get_attendance", methods=["GET", "POST"])
def get_attendance():
    content = request.get_json()

    schYr = content['schYr']
    date = content['date']
    lesson_data = content['lesson_data']
    _type = lesson_data['lesson_type']

    if _type == 'moving':
        att_data = _moving_att(schYr, date, lesson_data)

    elif _type == 'lesson':
        att_data = _lesson_att(schYr, date, lesson_data)

    elif _type == 'excur':
        att_data = _excur_att(schYr, date, lesson_data)

    elif _type == 'formclass' or _type == 'own':
        att_data = _form_att(schYr, date, lesson_data)

    return jsonify(att_data)


@app.route("/post_formclass_attendance", methods=["GET", "POST"])
def post_formclass_attendance():
    content = request.get_json()

    date = content['date']
    schYr = content['schYr']
    attDict = content['attDict']
    lesson_data = content['lesson_data']

    sch_div = lesson_data['sch_div']
    formclass_id = lesson_data['kelas_id']
    instructor_id = lesson_data['instructor_id']

    hadir, sakit, ijin, alpa, late = 0, 0, 0, 0, 0

    # record absence for each student
    for student_id in attDict:
        absent_code = attDict[student_id]

        hadir += absent_code == 'H'
        sakit += absent_code == 'S'
        ijin += absent_code == 'I'
        alpa += absent_code == 'A'
        late += absent_code == 'T'

        if absent_code in ['S', 'I', 'A', 'T']:
            # students are assumed to be present only no attendance needs to be recorded
            # klik
            _record_student_formclass_att(sch_div, schYr, formclass_id, date, student_id, absent_code)
            # our way
            _record_ck_absen_siswa('formclass', sch_div, schYr, date, formclass_id, student_id, absent_code)

    # post_formclass_att_head
    if formclass_id:   kelas_id = formclass_id
    else: kelas_id = ''

    timestamp = datetime.datetime.now()
    # time formclass attendance submitted post_formclass_attendance
    sql = "REPLACE INTO ck_absen_head \
                        (lesson_type, schYr, sch_div, class_id, guru_id, date, timestamp) \
                VALUES  ('formclass', %d, '%s', '%s', '%s', '%s', '%s') " % (
                        int(schYr), sch_div, kelas_id, instructor_id, date, timestamp)
    flaskPost(sql)
    print('post_formclass_attendance > REPLACE INTO ck_absen_head', timestamp)
    return timestamp


#---------------------------------------
# internal procedures
#---------------------------------------

def _form_att(schYr, date, lesson_data):
    sch_div = lesson_data['sch_div']
    formclass_id = lesson_data['kelas_id']
    absence_taken = _when_formclass_absence_taken(formclass_id, date, sch_div)
    student_list = _formclass_att_core(sch_div, schYr, date, formclass_id)
    attDict = {}
    for student in student_list:
        student_id = student['siswa_nopin']
        student['lesson_type'] = 'formclass'
        student['lesson_id'] = formclass_id
        student['sch_div'] = sch_div
        # Only non attendance is recorded otherwise regard as in attendance
        if absence_taken:
            if not student['f_att']:
                student['f_att'] = 'H'
        else:
            student['f_att'] = 'H'
        # put data back into dict
        attDict[student_id] = student
    return {'timestamp':absence_taken, 'students':attDict}


def _formclass_att_core(sch_div, schYr, date, formclass_id):
    sql = "SELECT s.siswa_nopin, s.siswa_nama_lengkap, a.absen_status AS f_att, \
                  sk.klapper_kelas_id AS formclass_id \
             FROM siswa_%s s  JOIN siswa_klapper%s sk \
               ON sk.klapper_siswa_nopin = s.siswa_nopin \
        LEFT JOIN siswa_absen%s a \
               ON a.absen_kelas_id = sk.klapper_kelas_id \
              AND a.absen_siswa_nopin= s.siswa_nopin \
              AND a.absen_tanggal = '%s' \
            WHERE sk.klapper_tahun_ajaran = %d \
              AND sk.klapper_kelas_id = '%s' \
            ORDER BY s.siswa_nama_lengkap " % (sch_div, sch_div, sch_div,
                                               date, int(schYr), formclass_id)
    return flaskAllplain(sql)


def _lesson_att(schYr, date, lesson_data):
    sch_div = lesson_data['sch_div']
    subject_id = lesson_data['pelajaran_id']
    formclass_id = lesson_data['kelas_id']
    instructor_id = lesson_data['instructor_id']

    absent_id = "%s%s%s%s" % (date, subject_id, formclass_id, instructor_id.lower())

    absence_taken = _when_lesson_absence_taken(sch_div, absent_id)

    # get list of students for formclass and their morning attendance
    student_list = _formclass_att_core(sch_div, schYr, date, formclass_id)

    # add lesson lesson attendance (g_att) to each student
    absent_id = "%s%s%s" % (date, sch_div, subject_id)
    attDict = {}
    for student in student_list:
        student_id = student['siswa_nopin']
        student['lesson_type'] = 'lesson'
        student['sch_div'] = sch_div

        if not student['f_att']:  student['f_att']='-'

        # get attendance for lesson
        if absence_taken:
            ab = _student_attend_lesson(student_id, sch_div, absent_id, absence_taken)
            if ab: student['g_att'] == ab
            else:  student['g_att'] = 'H'
        else: student['g_att'] = 'H'

        attDict[student_id] = student

    return {'timestamp': absence_taken, 'students': attDict}


def _formclass_name(sch_div, formcalss_id):
    sql = "SELECT kelas_nama FROM tblkelas%s \
            WHERE kelas_id='%s'" % (sch_div, formcalss_id)
    return flaskOneItem(sql, 'kelas_nama', '')


def _excur_att(schYr, date, lesson_data):
    sch_div = lesson_data['sch_div']
    kelas_id = lesson_data['kelas_id']
    absence_taken = _when_excur_absence_taken(sch_div, schYr, date, kelas_id)
      # get a list of students for the group_id
    sql = "SELECT s.siswa_nopin, s.siswa_nama_lengkap \
            FROM siswa_ekskulraport%s er JOIN siswa_%s s \
              ON s.siswa_nopin = er.raport_siswa_nopin \
            WHERE er.raport_tahun_ajaran = '%s' \
            AND raport_ekskul_id ='%s'" % (sch_div, sch_div, int(schYr), kelas_id)
    students = flaskAllplain(sql)

    attDict = {}
    for student in students:
        siswa_nopin = student['siswa_nopin']

        f_att = _student_formclasses_absence(sch_div, siswa_nopin, date, schYr)
        g_att = _excur_absence_for_student(sch_div, schYr,  date, kelas_id, siswa_nopin)
        student['g_att'] = g_att
        student['f_att'] = f_att
        student['sch_div'] = sch_div
        student['lesson_type'] = 'excur'

        attDict[siswa_nopin] = student

    return {'timestamp':absence_taken, 'students':attDict}

def _moving_att(schYr, date, lesson_data):
    print('_moving_att lesson_data:',lesson_data)
    sch_div = lesson_data['sch_div']
    group_id = lesson_data['kelas_id']
    subject_id = lesson_data['pelajaran_id']
    instructor_id = lesson_data['instructor_id']
    #, group_id, subject_id, instructor_id):
    # 2018-10-05 | bDT00006 | KLS019 | s0478
    absent_id = "%s%s%s%s" % (  date, subject_id, group_id, instructor_id.lower())

    absence_taken = _when_lesson_absence_taken(sch_div, absent_id)

    sql = "SELECT s.siswa_nopin, s.siswa_nama_lengkap, kmc.klapper_keterangan \
             FROM siswa_klappermovingclass%s kmc  JOIN siswa_%s s \
               ON s.siswa_nopin = kmc.klapper_siswa_nopin \
            WHERE kmc.klapper_kelas_id='%s' \
            ORDER BY s.siswa_nama_lengkap" % (sch_div, sch_div, group_id)
    students = flaskAllplain(sql)

    attDict = {}
    for student in students:
        siswa_nopin = student['siswa_nopin']

        f_att = _student_formclasses_absence(sch_div, siswa_nopin, date, schYr)
        g_att = _movingclass_absence_for_student(sch_div, absent_id, siswa_nopin)

        if absence_taken and not g_att:
            g_att ='H'
        student['g_att'] = g_att
        student['f_att'] = f_att
        student['sch_div'] = sch_div
        student['lesson_type'] = 'moving'

        attDict[siswa_nopin] = student

    return {'timestamp': absence_taken, 'students': attDict}


def _when_formclass_absence_taken(formclass_id, date, sch_div):
    sql = "SELECT timestamp FROM ck_absen_head \
            WHERE lesson_type = 'formclass' \
              AND sch_div = '%s' \
              AND class_id ='%s' \
              AND date ='%s' " % (sch_div, formclass_id, date)
    return flaskOneItem(sql, 'timestamp', '')


def _when_lesson_absence_taken(sch_div, absent_id):
    # ck
    # sql = "SELECT timestamp \
    #              FROM ck_absen_head \
    #             WHERE lesson_type = 'lesson' \
    #               AND sch_div = '%s' \
    #               AND class_id ='%s' \
    #               AND date ='%s' " % (sch_div, formclass_id, date)
    # klik
    # 2018-10-05   bDT00007   KLS001  s0478
    sql = "SELECT absen_timestamp FROM siswa_absenhead%s \
                           WHERE absen_id = '%s'" % (sch_div, absent_id)
    return flaskOneItem(sql, 'absen_timestamp', '')


def _when_excur_absence_taken(sch_div, schYr, date, group_id):
    sql = "SELECT timestamp FROM ck_absen_head \
                            WHERE lesson_type = 'excur' \
                              AND sch_div = '%s' \
                              AND class_id ='%s' \
                              AND date ='%s'" % (sch_div, group_id, date)
    return flaskOneItem(sql, 'timestamp', '')


def _faith(agama_id):
    sql = "SELECT agama_nama  FROM tblagama  WHERE agama_id = '%s'" % agama_id
    return flaskOneItem(sql, 'agama_nama', '')


def _sch_divs():
    return ['pre', 'tk', 'sd', 'smp', 'smu', 'smk']

def _formclass_name_lain(sch_div, kelas_id):
    sql = "SELECT kelas_nama_lain FROM tblkelas%s \
            WHERE kelas_id='%s'" % (sch_div, kelas_id)
    return flaskOneItem(sql, 'kelas_nama_lain', '')

def _formclasses_for_teacher(guru_id, sch_div, schYr):
    mylist = []
    sql = "SELECT * FROM tblguru%s g JOIN tblkelas%s k \
                      ON g.guru_wali_kelasid = k.kelas_id \
                   WHERE k.kelas_not_active <> 'Y' \
                     AND g.guru_id = '%s'" % (sch_div, sch_div, guru_id)
    res = flaskAllplain(sql)
    if res:
        #try:
        for row in res:
            row_data = [row['kelas_id'], row['kelas_nama_lain'], sch_div, 'formclasses']
            mylist.append(row_data)
        #except:
        #    pass
    return mylist

def _lessons_for_teacher(sch_div, teacher_id, schYr):
    sql = "SELECT p.pelajaran_id, p.pelajaran_nama, \
                  gd.guru_pelajaran_kelas_id  AS kelas_id \
             FROM tblgurudetil%s gd \
             JOIN tblpelajaran%s p ON gd.guru_pelajaran_id = p.pelajaran_id \
            WHERE gd.guru_id = '%s' \
            ORDER BY p.pelajaran_urut" % (sch_div, sch_div, teacher_id)
    res = flaskAllplain(sql)
    try: return [row for row in res]
    except: return []


def _formclass_short_name( sch_div, kelas_id):
    sql = "SELECT kelas_nama_lain FROM tblkelas%s \
            WHERE kelas_id='%s'" % (sch_div, kelas_id)
    return flaskOneItem(sql, 'kelas_nama_lain', '')


def _is_formclass_for_teacher(sch_div, kelas_id, teacher_id):
    sql = "SELECT guru_wali_kelasid FROM tblguru%s \
            WHERE guru_id = '%s' AND guru_wali_kelasid='%s'" % (sch_div, teacher_id, kelas_id)
    res = flaskOneplain(sql)
    if res: return True
    else: return False

def _student_formclasses_absence(sch_div, siswa_nopin, date, schYr):
    sql = "SELECT sa.absen_status as f_att \
             FROM siswa_klapper%s sk JOIN siswa_absen%s sa \
               ON sk.klapper_siswa_nopin = sa.absen_siswa_nopin \
            WHERE sk.klapper_siswa_nopin = '%s' \
              AND absen_tanggal = '%s'" % (sch_div, sch_div, siswa_nopin, date)
    return flaskOneItem(sql, 'f_att', '-')

def _movingclass_absence_for_student( sch_div, absent_id, siswa_nopin):
    sql = "SELECT absen_nilai FROM siswa_absendetail%s \
            WHERE absen_id = '%s' \
              AND absen_siswa_nopin = '%s'" % (sch_div,
                                               absent_id,
                                               siswa_nopin)
    return flaskOneItem(sql, 'absen_nilai', '')

def _excur_absence_for_student(sch_div, schYr, date, group_id, siswa_nopin):
    sql = "SELECT absent_code FROM ck_absen_siswa \
            WHERE sch_div = '%s' AND date='%s' \
              AND group_id='%s'  AND student_id = '%s' \
              AND lesson_type='excur'" % (sch_div, date, group_id, siswa_nopin)

    return flaskOneItem(sql, 'absent_code', '-')

def _student_attend_lesson(student_nopin, sch_div, absent_id, absence_taken):
    if not absence_taken: return 'H'
    sql = "SELECT absen_nilai FROM siswa_absendetail%s \
            WHERE absen_siswa_nopin = '%s' \
                AND absen_id = '%s'" % (sch_div, student_nopin, absent_id)
    return flaskOneItem(sql, 'absen_nilai', '')


def _add_formclasses(all_list_data, sch_div, teacher_id, schYr):
    idx=len(all_list_data)
    formclasses = _formclasses_for_teacher(teacher_id, sch_div, schYr)
    for classdata in formclasses:

        formclass_name = classdata[1]

        group_name = "Formclass:%s" % classdata[1]

        group_data =dict(sch_div=sch_div,
                         kelas_id=classdata[0],
                         group_name=group_name,
                         lesson_type='formclass')

        isi = dict(display_items=['formclass', formclass_name], data=group_data)
        all_list_data[idx] = isi
        idx+=1

    return all_list_data

def _add_lessons(all_list_data, sch_div, teacher_id, schYr):
    idx=len(all_list_data)
    lessons = _lessons_for_teacher(sch_div, teacher_id, schYr) # flask
    #if lessons:
    for lesson in lessons:
        #pelajaran_id = lesson['pelajaran_id']
        subject = lesson['pelajaran_nama']
        kelas_id = lesson['kelas_id']
        subject_id = lesson['pelajaran_id']
        #lesson_id = "%s %s" % (pelajaran_id, kelas_id)  # create a unique id

        lesson['sch_div'] = sch_div
        if kelas_id[:2] == "MC":
            lesson_type = 'moving'
            linked_classes = _classes_linked_to_movingclass(sch_div, kelas_id)# flask
        else:
            linked_classes = _formclass_short_name(sch_div, kelas_id)# flask
            if _is_formclass_for_teacher(sch_div, kelas_id, teacher_id):# flask
                lesson_type = 'own'
            else:
                lesson_type = 'lesson'

        group_data = dict(sch_div=sch_div,
                          kelas_id=kelas_id,
                          pelajaran_id=subject_id,
                          group_name=subject,
                          lesson_type=lesson_type)
        print(group_data)
        data_dict = dict(display_items=[subject, linked_classes], data=group_data)
        all_list_data[idx] = data_dict
        idx += 1

    return all_list_data


def _add_excuric(all_list_data, sch_div, teacher_id, schYr):
    idx=len(all_list_data)
    excur_groups = _excuric_for_teacher(sch_div, teacher_id, schYr)  # flask

    #if excur_groups:
    for group in excur_groups:
        kelas_id = group['kelas_id']
        title = group['group_name']

        daynames=[]
        daynumbers = group['day']

        if '1' in daynumbers: daynames.append('Mon')
        if '2' in daynumbers: daynames.append('Tue')
        if '3' in daynumbers: daynames.append('Wed')
        if '4' in daynumbers: daynames.append('Thur')
        if '5' in daynumbers: daynames.append('Fri')
        days = "/".join(daynames)

        sub_title = 'excul %s: %s ' % (sch_div, days)

        group_data = dict(sch_div=sch_div,
                          kelas_id=kelas_id,
                          group_name=title,
                          lesson_type='excur')

        data_dict = dict(display_items=[title, sub_title], data=group_data)
        all_list_data[idx] = data_dict
        idx += 1

    return all_list_data


def _excuric_for_teacher(sch_div, teacher_id, schYr):

    sql = "SELECT je.ekskul_id AS kelas_id, \
                  je.ekskul_nama AS group_name, \
                  je.ekskul_hari AS day \
             FROM tblgurudetil%s gd JOIN tbljenisekskul%s je \
               ON gd.guru_pelajaran_id = je.ekskul_id \
            WHERE gd.guru_pelajaran_kelas_id = '-' \
              AND gd.guru_id = '%s'" % (sch_div, sch_div, teacher_id)
    res = flaskAllplain(sql)
    if res: return [row for row in res]
    else: return []


def _classes_linked_to_movingclass(sch_div, movingclass_id):
    sql = "SELECT class_ids FROM tblmovingclasshead%s \
                WHERE kelas_id = '%s' " % (sch_div, movingclass_id)
    class_ids = flaskOneItem(sql,'class_ids',[])
    return  _short_names(sch_div, class_ids)

def _short_names(sch_div, class_ids):
    if not class_ids:return ''
    formclass_names_list = []
    for formclass_id in class_ids:
        formclass_names_list.append(_formclass_name_lain(sch_div, formclass_id))

    return ", ".join(formclass_names_list)


def _record_lesson_absence_head(sch_div, absent_id, subject_id, formclass_id,
                               hadir, sakit, ijin, alpa, late, instructor_id,
                               schYr, date):
    '''time lesson attendance submitted and totals
    currently only  total_hadir and total_alpa recorded'''
    instructor_id = instructor_id.lower()
    timestamp = datetime.datetime.now()
    sql = "REPLACE INTO siswa_absenhead%s (\
                        absen_id, absen_tahun_ajaran, absen_tanggal, \
                        absen_pelajaran_id, absen_kelas_id,  absen_guru_id, \
                        absen_total_hadir, absen_total_sakit, absen_total_ijin, absen_total_alpa, \
                        absen_total_terlambat, absen_timestamp, absen_sistem_id, absen_sistem_urut, absen_flag) \
                VALUES ('%s', %d, '%s', \
                        '%s', '%s', '%s',\
                         %d, %d, %d, %d, %d, '%s',\
                         'SM', 1,'bbbbb') " % (sch_div,
                        absent_id, int(schYr),  date,
                        subject_id, formclass_id, instructor_id,
                        hadir, sakit, ijin, alpa, late, timestamp)
    flaskPost(sql)
    return timestamp


def _record_student_formclass_att(sch_div, schYr, kelas_id, date, student_nopin, absen_code):
    # for klik
    # daily attendance / formclass - absen_status should be I,T,S or A
    sql = "REPLACE INTO siswa_absen%s \
                    (absen_tahun_ajaran, absen_kelas_id, \
                    absen_tanggal, absen_siswa_nopin, absen_status) \
            VALUES (%d, '%s', \
                    '%s', '%s','%s' )" % (sch_div,
                    int(schYr), date,
                    kelas_id, student_nopin, absen_code)
    flaskPost(sql)

def _record_ck_absen_siswa(lesson_type, sch_div, schYr, date,
                           class_id, student_id, absent_code, subject_id=''):
    sql = "REPLACE INTO ck_absen_siswa \
                        (lesson_type, sch_div, schYr, date, \
                        group_id, student_id, absent_code, subject_id) \
                VALUES ('%s', '%s', %d, '%s', \
                        '%s', '%s','%s','%s' )" % (
                        lesson_type, sch_div, int(schYr), date,
                        class_id, student_id, absent_code, subject_id)
    flaskPost(sql)


if __name__ == '__main__':
    app.run()
