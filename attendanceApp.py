from kivy.app import App

ckApp_version = '1.01'

import requests
import datetime
from time import sleep

from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock


Window.size = (600, 850)

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label

from kivy.properties import ListProperty
from kivy.properties import StringProperty
from kivy.properties import BooleanProperty

g_lessonType_colours = {
    'excur': (.6, .8, .5, 1),
    'formclass': (.9, .8, .7, 1),
    'moving': (.7, .8, .9, 1),
    'lesson': (.9, .7, .8, 1),
    'own': (.7, .9, .8, 1)}

g_absence_colours = {
    "Present": (0.6, 1, 1, 1),
    "Absent": (1, 0.0, 1, 1),
    "Late": (1, 1, 0.6, 1),
    "Sick": (1, 0.7, 0.7, 1),
    "Excused": (0.7, 0.7, 1, 1),
    "-": (1, 1, 1, 1),
    "?": (.7, 0.2, 0.7, 1)}

g_absent_name = []
for absent_name in g_absence_colours:
    g_absent_name.append(absent_name)


g_absence_code_colours = {
    "H": (0.6, 1, 1, 1),
    "A": (1, 0.0, 1, 1),
    "T": (1, 1, 0.6, 1),
    "S": (1, 0.7, 0.7, 1),
    "I": (0.7, 0.7, 1, 1),
    "-": (1, 1, 1, 1),
    "?": (.7, 0.2, 0.7, 1)}



g_studentAtt = {}
g_lessonsDict = {}
g_absent_dict_code_title = {}
g_absent_dict_title_code = {}


g_lesson_data = ''
g_formclass_id = ''
g_current_date = ''
g_student_nopin = ''
g_instructor_id = ''
g_previous_screen = ''
g_selected_group_id = ''
g_schYr = 2018

sm = ''


g_flask_addr = ''
g_image_path = ''

def try_local():
    global g_flask_addr, g_image_path
    g_flask_addr = 'http://192.168.0.254:5000'

    g_image_path = 'http://192.168.0.254/smsicons'
    link = '%s%s' % (g_flask_addr, '/version')
    try:
        resp = requests.get(link)
        return resp.text

    except requests.exceptions.RequestException as e:
        print('exception:',e)
        return ''

def try_remote():
    global g_flask_addr, g_image_path
    g_flask_addr = 'http://110.232.86.18:5000'
    g_image_path = '110.232.86.18:9000/smsicons'
    link = '%s%s' % (g_flask_addr, '/version')
    try:
        resp = requests.get(link)
        return resp.text

    except requests.exceptions.RequestException as e:
        print('exception:', e)
        return ''

def getver():
    var = try_local()
    if var:
        app.title = 'Local network'
        return var
    else:
        var = try_remote()
        if var:
            app.title = 'Remote network'
            return var

    return ''

Builder.load_string('''
<LoginScreen>
    BoxLayout:
        orientation:'vertical'

        GridLayout:
            cols:1
            padding:20
            spacing:10
            row_default_height:60
            row_force_default:True
            Label:
                text:'UserID'
            TextInput:
                id:userid

            Label:
                text:'Password'
            TextInput:
                id:pwd
                password:True
                multiline:False

            Widget:
            Button:
                text:'Enter'
                on_press:root.login(userid.text, pwd.text)
            Widget:
            Label:
                text:root.attention_notice


<GroupsScreen>
    BoxLayout:
        orientation:'vertical'
        HLayout
            Button:
                text: '...'
                size_hint_x:None
                width:self.height
                on_press: root.manager.current = 'login'
        HLayout
            id:g_header
            Label:
                text:root.username
        SortableListView:
            id:listctrl


<HLayout@BoxLayout>
    size_hint_y:None
    height:60


<GroupDetailsScreen>
    BoxLayout:
        orientation:'vertical'
        HLayout
            Button:
                text: '...'
                size_hint_x:None
                width:self.height
                on_press: root.manager.current = 'attendance'
            Label
                text:'Group Details'
            Label
                text:root.group_name
        HLayout
            Label:
                text:'Type'
            Label:
                text:root.lesson_type


        HLayout
            Label:
                text:'Type'
            Label:
                text:root.lesson_type


        Widget


<AttendanceScreen>
    BoxLayout:
        orientation:'vertical'
        HLayout
            Button:
                text: '...'
                size_hint_x:None
                width:self.height
                on_press: root.manager.current = 'groups'
            Button:
                on_press:root.manager.current='group_details'
                text:root.class_name
            Label:
                size_hint_x:None
                width:btn_submit.width+btn_all.width
                text:root.population

        HLayout
            Label:
                text:root.absence_taken
            Button
                id:btn_submit
                text:'Submit'
                disabled:root.btnSubmit_disable
                size_hint_x:None
                width:120
                on_release:root.submit()
            Button
                id:btn_all
                text:'All'
                disabled:root.btnAll_disable
                size_hint_x:None
                width:self.height*1.5
                on_press:root.change_all(self)
        ScrollView:
            StackLayout:
                id:listlayout
                size_hint_y:None
                height: self.minimum_height


<StudentDataRow>:
    size_hint_y:None
    height:30
    Label:
        text:root.label_str
    Label:
        text:root.data_str
        size_hint_x:2


<DetailsScreen>
    BoxLayout:
        orientation:'vertical'

        HLayout
            Button:
                text:'...'
                size_hint_x:None
                width:self.height
                on_press: root.manager.current = 'attendance'
            Label:
                text:root.student_nopin
        BoxLayout:
            size_hint_y:None
            height:220
            AsyncImage:
                source:root.student_image
                allow_stretch:True
                size_hint_x:None
                width:self.height*.8
            BoxLayout:
                orientation:'vertical'
                Label:
                    text:root.student_name
                Label:
                    text:root.formclass

        ScrollView:
            id:sv
            StackLayout:
                id:studentdata
                size_hint_y:None
                height:self.minimum_height
                do_scroll_x:False


<LessonButton>:
    size_hint_y:None
    height:40
    group:'a'
    selected:1, 1, 1, .9
    BoxLayout:
        id:btnlayout
        spacing:1
        pos: self.parent.pos
        size: self.parent.size
        orientation: 'horizontal'


<SortableListView>:
    orientation:'vertical'
    canvas.before:
        Color:
            rgba:1,1,1,.5
        Rectangle:
            pos: self.pos
            size:self.size
    HLayout:
        id:listheader
    ScrollView:
        StackLayout:
            id:listlayout
            size_hint_y:None
            height: self.minimum_height

<Att_CheckBox>:
    size_hint_x:None
    width:self.height

<Spin>:
    size_hint_x:None
    width:80
    Button
        text:'-'
        size_hint_x:None
        width:20
        on_press:root.change_mins(-1)
    TextInput:
        text:root.mins
        font_size:36
        size_hint_x:None
        width:40
    Button
        text:'+'
        size_hint_x:None
        width:20
        on_press:root.change_mins(+1)


<StudentAttWdg>
    size_hint_y:None
    height:80
    id:wdg
    Button:
        text:root.student_name
        on_press:
            root.on_select_student(wdg.student_id)
            app.sm.current = 'details'
        AsyncImage:
            source:root.image_path
            y: self.parent.y +2
            x: self.parent.x
            height: self.parent.height-3
            width:self.height*.8
    BoxLayout
        orientation:'vertical'
        id:layout_tardy
        size_hint_x:None
        width:40
        Button
            id:btn_f_att
            text:root.f_att
            disabled:True
            background_color:root.btn_f_att_colour
            background_disabled_normal: self.background_normal

    Button
        text:root.absent_name
        size_hint_x:None
        width:120
        #disabled:root.btn_disable
        background_color:root.btn_colour
        background_disabled_normal: self.background_normal
        on_press:root.on_btn_absent(self)

''')

class Spin(BoxLayout):
    mins=StringProperty('5')
    def change_mins(self,val):
        self.mins =str(int(val)+int(self.mins))

class LoginScreen(Screen):
    attention_notice = StringProperty()
    userid = StringProperty()
    pwd = StringProperty()

    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.connect, 2)

    def connect(self, *args):
        ver = ''
        while not ver:
            ver = getver()
            if ver:
                self.attention_notice = "CK attendance V.%s " % ver
            else:
                self.attention_notice = "No Connection, check network"
            sleep(2)

    def login(self, user_id='', password=''):
        global g_instructor_id
        self.attention_notice = ''

        try:
            link = '%s/%s' % (g_flask_addr, 'version')
            ver = requests.get(link).text
            if ckApp_version != ver:
                app.title = "%s %s" % ('new ver required, please update')
                notice = "%s %s" % ('new ver required, please update')
            else:
                app.title = 'CK v.%s' % ver

                # try: # request returns userid if ok, error message, or none
                link = '%s/%s' % (g_flask_addr, 'validate')
                notice = requests.get(link, json={"user_id": user_id,
                                                  "password": password}).text

                if notice == 'Valid': self.successfull_login(user_id)

        except:
            notice = 'Could not connect to server, please try later'

        self.attention_notice = notice

    def successfull_login(self, user_id):
        global g_absent_dict_code_title, g_absent_dict_title_code, g_instructor_id
        g_instructor_id = user_id

        # requests found
        link = '%s/%s' % (g_flask_addr, 'absent_dict')
        resp = requests.get(link)
        absent_dict = resp.json()

        for row in absent_dict:
            g_absent_dict_code_title[row['absen_id']] = row['absent_name']
            g_absent_dict_title_code[row['absent_name']] = row['absen_id']

        sm.current = 'groups'


class GroupDetailsScreen(Screen):
    group_name = StringProperty()
    lesson_type = StringProperty()
    def __init__(self, **kwargs):
        super(GroupDetailsScreen, self).__init__(**kwargs)
        self.group_name = 'group name'


class Att_CheckBox(CheckBox):
    def __init__(self, g_att='', **kwargs):
        super(Att_CheckBox, self).__init__(**kwargs)
        self.active = (g_att == 'H')


class StudentDataRow(BoxLayout):
    label_str = StringProperty()
    data_str = StringProperty()

    def __init__(self, label_str, data_str, **kwargs):
        super(StudentDataRow, self).__init__(**kwargs)
        self.label_str = label_str
        self.data_str = data_str


class StudentAttWdg(BoxLayout):
    btn_disable = BooleanProperty(True)
    btn_colour = ListProperty([1, 1, 1, 1])
    btn_f_att_colour =  ListProperty([1, 1, 1, 1])
    cbox_state = StringProperty('normal')
    image_path = StringProperty('')
    f_att = StringProperty('H')
    absent_name = StringProperty('Present')
    student_name = StringProperty()

    def __init__(self, data, **kwargs):
        super(StudentAttWdg, self).__init__(**kwargs)
        self.set_student_data(data)

    def set_student_data(self, data):
        self.data = data

        self.student_name = data['siswa_nama_lengkap']
        self.student_id = data['siswa_nopin']
        self.sch_div = data['sch_div']

        # create student image path and copt to student data
        self.image_path = get_student_image(kelamin_id='',
                                            sch_div=self.sch_div,
                                            pin=self.student_id)

        data['image_path'] = self.image_path

        try:  self.g_att = data['g_att']
        except: self.g_att = ''

        self.f_att = data['f_att']
        btn_f_att = self.ids.btn_f_att

        if data['lesson_type'] in ['formclass', 'own']:
            self.remove_widget(btn_f_att)
            self.absent_code = self.f_att

        else:
            self.absent_code = data['g_att']

            btn_f_att.text = data['f_att']
            self.btn_f_att_colour = g_absence_code_colours[data['f_att']]

        try:  self.set_absent_name(g_absent_dict_code_title[self.absent_code])
        except Exception as e:
            print('!! self.f_att:', self.absent_code, e)

    def set_absent_name(self, absent_name):
        print('absent_name', absent_name,g_absence_colours)
        #print('g_absent_dict_code_title',g_absent_dict_code_title)
        self.absent_name = absent_name

        self.btn_colour = g_absence_colours[absent_name]


    def on_btn_absent(self, btn):

        if btn.text=='Late':
            self.remove_widget(self.tardy)

        idx=g_absent_name.index(btn.text)
        try: txt = g_absent_name[idx + 1]
        except: txt = g_absent_name[0]
        self.set_absent_name(txt)

        if txt=='Late':
            self.tardy=Spin()
            layout = self.ids.layout_tardy
            layout.add_widget(self.tardy)

        self.absent_code = g_absent_dict_title_code[txt]


    def on_select_student(self, student_nopin):
        global g_student_nopin
        g_student_nopin = student_nopin




class LessonButton(ToggleButton):
    def __init__(self, **kwargs):
        super(LessonButton, self).__init__(**kwargs)

    def add_data(self, key, data):
        display_items = data['display_items']
        lesson_type = data['data']['lesson_type']
        self.background_color = g_lessonType_colours[lesson_type]
        self.id = key
        first_item = True
        for item in display_items:
            lbl = Label(text=item.title())
            if first_item:
                lbl.size_hint_x = 2
                first_item = False
            self.ids.btnlayout.add_widget(lbl)


class SortableListView(BoxLayout):
    column_widths = ListProperty([])

    def __init__(self, **kwargs):
        super(SortableListView, self).__init__(**kwargs)

    def set_listctrl_data(self, list_data=[]):
        self.ids.listlayout.clear_widgets()
        if list_data:
            self.add_widgets(list_data)

    def add_widgets(self, list_data):
        for key in list_data:
            row_data = list_data[key]
            b = LessonButton()
            b.add_data(key, row_data)
            b.bind(on_press=self.parent_screen.on_select_group)
            self.ids.listlayout.add_widget(b)

    def set_parent_screen(self, screen):
        self.parent_screen = screen



class GroupsScreen(Screen):
    username = StringProperty('')
    def __init__(self, **kwargs):
        super(GroupsScreen, self).__init__(**kwargs)

    def on_enter(self, *args):
        print('Groups on enter g_instructor_id=', g_instructor_id)
        self.username = 'Welcome %s' % g_instructor_id
        self.load_groups()

    def load_groups(self):
        global g_lessonsDict, g_current_date

        # if self.first_time:
        link = '%s/%s' % (g_flask_addr, 'all_groups')
        resp = requests.get(link, json={"teacher_id": g_instructor_id,
                                        "schYr": g_schYr})
        g_lessonsDict = resp.json()
        g_current_date = datetime.date.today()

        self.ids.listctrl.set_parent_screen(self)
        self.ids.listctrl.set_listctrl_data(g_lessonsDict)

    def on_select_group(self, wdg):
        global g_selected_group_id, g_lesson_data
        g_selected_group_id = wdg.id
        g_lesson_data = g_lessonsDict[g_selected_group_id]['data']
        sm.current = 'attendance'


class AttendanceScreen(Screen):
    btnAll_disable = BooleanProperty(False)
    btnSubmit_disable = BooleanProperty(False)
    class_name = StringProperty()
    absence_taken = StringProperty()
    population = StringProperty()

    def __init__(self, data='', **kwargs):
        super(AttendanceScreen, self).__init__(**kwargs)
        self.kelas_id = ''
        self.formclass_id = ''
        self.movingclass_id = ''
        self.selected_group_id = ''
        self.lesson_type = ''

    def on_enter(self):
        global g_formclass_id, g_studentAtt

        _type = g_lesson_data['lesson_type']
        # g_lesson_data: {'lesson_type': 'lesson   ', 'kelas_id': 'KLS005', 'pelajaran_id': 'bDT00008', 'pelajaran_nama': 'Design & Technology', 'sch_div': 'smp'}
        # g_lesson_data: {'lesson_type': 'moving   ', 'kelas_id': 'MC0001', 'pelajaran_id': 'bIDT0009', 'pelajaran_nama': 'IGCSE 1 Design & Technology', 'sch_div': 'smp'}
        # g_lesson_data: {'lesson_type': 'own      ', 'kelas_id': 'KLS001', 'pelajaran_id': 'bPKN0001', 'pelajaran_nama': 'Pendidikan Kewarganegaraan', 'sch_div': 'sd'}
        # g_lesson_data: {'lesson_type': 'formclass', 'kelas_id': 'KLS001', 'sch_div': 'sd'}
        # g_lesson_data: {'lesson_type': 'excur    ', 'kelas_id': 'CTM2',  'day': '4,', 'group_id': 'CTM2', 'group_name': 'Cooking and Table Manner Thursday', 'sch_div': 'sd'}

        self.btnSubmit_disable = (_type == 'own')
        self.btnAll_disable = (_type == 'own' or _type == 'formclass')

        # to prevent unnecessary reloading
        if g_selected_group_id == self.selected_group_id: return
        self.selected_group_id = g_selected_group_id

        self.attendance_layout = self.ids.listlayout
        self.attendance_layout.clear_widgets()

        self.lesson_type = _type
        self.kelas_id = g_lesson_data['kelas_id']
        self.sch_div = g_lesson_data['sch_div']

        self.class_name = g_lesson_data['group_name'].title()

        self.absent_id = ''
        g_lesson_data['instructor_id'] = g_instructor_id

        link = '%s/%s' % (g_flask_addr, 'get_attendance')
        resp = requests.get(link, json={'schYr': str(g_schYr),
                                        'date': str(g_current_date),
                                        'lesson_data': g_lesson_data
                                        })
        res = resp.json()

        timestamp = res['timestamp']
        g_studentAtt = res['students']
        self.population = "%d students" % len(g_studentAtt)
        self.display_timestamp(timestamp)

        if g_studentAtt:
            for pin in g_studentAtt:
                wdg = StudentAttWdg(data=g_studentAtt[pin])
                g_studentAtt[pin]['wdg'] = wdg
                self.attendance_layout.add_widget(wdg)

    def display_timestamp(self, timestamp):
        if timestamp:
            self.absence_taken = "Submitted: %s" % str(timestamp)
        else:
            self.absence_taken = "-none-"

    def change_all(self, btn):
        global g_studentAtt

        if btn.text == 'All':
            g_att = 'H'
            btn.text = 'None'
        else:
            g_att = 'A'
            btn.text = 'All'

        for key in g_studentAtt:
            data = g_studentAtt[key]
            wdg = g_studentAtt[key]['wdg']
            wdg.checkbox.active = g_att == 'H'
            data.update({'g_att': g_att})
            g_studentAtt.update({key: data})

    def submit(self):
        t = self.lesson_type
        if t == 'lesson' or t == 'moving' or t == 'excur':
            timestamp = self.submit_lesson_att()

        else:
            timestamp = self.submit_formclass_att()
        self.display_timestamp(timestamp)

    def submit_formclass_att(self):
        print('submit_formclass_att')
        formclass_id = g_lesson_data['kelas_id']
        if not self.absent_id:
            self.absent_id = "%s%s%s" % (g_current_date, self.sch_div, formclass_id)

        # prepare data for submition
        submitDict = {}
        for student_nopin in g_studentAtt:
            rowdict = g_studentAtt[student_nopin]
            absent_code = g_absent_dict_title_code[rowdict['wdg'].absent_name]
            submitDict[student_nopin] = absent_code

        link = '%s/%s' % (g_flask_addr, 'post_formclass_attendance')
        json_file = {'date': str(g_current_date),
                     'schYr': str(g_schYr),
                     'attDict': submitDict,
                     'lesson_data': g_lesson_data}

        resp = requests.get(link, json=json_file)
        return resp.json()

    def submit_lesson_att(self):
        t = self.lesson_type

        # prepare data for submision
        submitDict = {}
        for student_id in g_studentAtt:
            absent_code = g_studentAtt[student_id]['wdg'].absent_code
            submitDict[student_id] = absent_code

        link = '%s/%s' % (g_flask_addr, 'post_lesson_attV2')
        resp = requests.get(link, json={'submitDict': submitDict,
                                        'lesson_data': g_lesson_data,
                                        'schYr': str(g_schYr),
                                        'date': str(g_current_date)})
        # after flask should return time of submision or '' if submision failed
        return resp.text


class DetailsScreen(Screen):
    formclass = StringProperty()
    student_name = StringProperty()
    student_nopin = StringProperty('')
    student_image = StringProperty()

    def __init__(self, **kwargs):
        super(DetailsScreen, self).__init__(**kwargs)

    def on_enter(self):
        layout = self.ids.studentdata
        layout.clear_widgets()

        sch_div = g_lesson_data['sch_div']

        link = '%s/%s' % (g_flask_addr, 'student_details')
        resp = requests.get(link, json={'sch_div': sch_div, "student_nopin": g_student_nopin})
        res = resp.json()
        if not res:
            txt = ' no details for ' + g_student_nopin
            layout.add_widget(StudentDataRow('warning', txt))
            return

        self.student_name = res['siswa_nama_lengkap']
        self.student_image = get_student_image(kelamin_id='', sch_div=sch_div, pin=g_student_nopin)
        for fieldName in res:
            txt = str(res[fieldName])
            if txt:
                layout.add_widget(StudentDataRow(fieldName, txt))


def get_student_image(kelamin_id, sch_div, pin):
    try:
        student_image = "%s/%s/%s.jpg" % (g_image_path, sch_div, pin)
    except:
        if kelamin_id == 'P':
            student_image = "student_image_f.png"
        else:
            student_image = "student_image_m.png"
    return student_image


class MainApp(App):
    def build(self):
        global sm
        Window.bind(on_keyboard=self.key_input)

        self.sm = sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GroupsScreen(name='groups'))
        sm.add_widget(AttendanceScreen(name='attendance'))
        sm.add_widget(DetailsScreen(name='details'))
        sm.add_widget(GroupDetailsScreen(name='group_details'))
        return sm


    def key_input(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            sm.current = sm.previous()
            if sm.current=='LoginScreen':
                quit()
            return True  # override the default behaviour
        else:  # the key now does nothing
            return False


if __name__ == "__main__":
    app = MainApp()
    app.run()
