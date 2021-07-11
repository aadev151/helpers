
"""
HELPERS v2.0
https://www.helpers.today
Developer: Alex Anisimov (vomisina.xela@gmail.com)
"""


from flask import render_template, redirect, request, abort, jsonify, flash, Flask
from flask_login import current_user
from .models import User
from glob import glob
import hashlib
import json
from os import remove
from random import randint
from datetime import datetime
import flask_sqlalchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user


db = flask_sqlalchemy.SQLAlchemy()
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.view'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


ENCODING = 'utf-8'
DIR = '/Users/aleksandranisimov/PycharmProjects/helpers_2.0/project/'
TASKS_DIR = DIR + 'static/tasks/tasks.txt'
LAST_ID_DIR = DIR + 'static/tasks/last_id.txt'
FUNDS_DIR = DIR + 'static/funds/funds.txt'
API_DIR = DIR + 'static/api/tasks.json'
ALERTS_DIR = DIR + 'alerts/alerts.txt'
TOP_DIR = DIR + 'static/top/top.txt'
TAGS_DIR = DIR + 'static/tags/tags.txt'
PROFANITY_DIR = DIR + 'static/profanity.txt'


def task_matches(from_fund, query, tags, from_matches, query_matches, tag_matches):
    return not from_fund and not query and not tags \
           or from_fund and not query and not tags and from_matches \
           or from_fund and query and not tags and from_matches and query_matches \
           or from_fund and not query and tags and from_matches and tag_matches \
           or from_fund and query and tags and from_matches and query_matches and tag_matches \
           or not from_fund and query and not tags and query_matches \
           or not from_fund and query and tags and query_matches and tag_matches \
           or not from_fund and not query and tags and tag_matches


def create(name, info, tags, fund):
    last_id_file = open(LAST_ID_DIR, encoding=ENCODING)
    last_id = str(int(last_id_file.read()) + 1)
    last_id_file.close()
    last_id_file = open(LAST_ID_DIR, 'w', encoding=ENCODING)
    last_id_file.write(last_id)
    last_id_file.close()

    url = f'/task/{last_id}'

    with open(TASKS_DIR, 'a', encoding=ENCODING) as tasks_file:
        tasks_file.write(name + '|' + info + '|' + tags + '|' + fund + '|' +
                         datetime.strftime(datetime.now(), '%d.%m.%Y') + '|0|' + url + '\n')

    with open(FUNDS_DIR, encoding=ENCODING) as in_file:
        before_current_fund = ""
        current_fund_line = ""
        after_current_fund = ""
        found_current_fund = False
        for line in in_file:
            if line.strip().split('|')[0] != fund:
                if found_current_fund:
                    after_current_fund += line
                else:
                    before_current_fund += line
            else:
                current_fund_line = line.strip()
                found_current_fund = True

        current_fund_info = current_fund_line.split('|')

    with open(FUNDS_DIR, 'w', encoding=ENCODING) as out_file:
        out_file.write(before_current_fund)
        out_file.write(current_fund_info[0] + '|' + str(int(current_fund_info[1]) + 1) + '|' + current_fund_info[2])
        out_file.write('\n' + after_current_fund)

    with open(API_DIR, encoding='utf-8') as in_file:
        data = json.load(in_file)
        data[last_id] = {"number": last_id, "name": name, "info": info, "tags": tags, "fund": fund,
                         "url": "https://www.helpers.today" + url}

    with open(API_DIR, 'w', encoding='utf-8') as out_file:
        json.dump(data, out_file, ensure_ascii=False, indent='\t')

    return url


def edit(task, name, info, tags, fund):
    with open(TASKS_DIR, encoding=ENCODING) as in_file:
        before_current_task = ""
        current_task_line = ""
        after_current_task = ""
        found_current_task = False
        for line in in_file:
            if line.strip().split('/')[-1] != task:
                if found_current_task:
                    after_current_task += line
                else:
                    before_current_task += line
            else:
                current_task_line = line.strip()
                found_current_task = True

        current_fund_info = current_task_line.split('|')

    with open(TASKS_DIR, 'w', encoding=ENCODING) as out_file:
        out_file.write(before_current_task)
        out_file.write(name + '|' + info + '|' + tags + '|' + current_fund_info[-2] + '|' + current_fund_info[-1])
        out_file.write('\n' + after_current_task)

    with open(API_DIR, encoding='utf-8') as in_file:
        data = json.load(in_file)
        data[task] = {"number": task, "name": name, "info": info, "tags": tags, "fund": fund,
                      "url": "https://www.helpers.today" + current_fund_info[-1]}

    with open(API_DIR, 'w', encoding='utf-8') as out_file:
        json.dump(data, out_file, ensure_ascii=False, indent='\t')

    return current_fund_info[-1]


def delete(task, fund):
    """messages_files = glob(DIR + 'messages/*.txt')
    for filename in messages_files:
        message_info = filename.split('/')[-1].split('&')
        if message_info[-1][:-4] == task:
            first_user, second_user = message_info[0], message_info[1]

            try:
                remove(filename)
                remove(DIR + f'messages/{second_user}&{first_user}&{message_info[-1]}')
            except FileNotFoundError:
                continue

            if User.query.filter_by(username=first_user).first().who == 'performer':
                performer_user, fund_user = first_user, second_user
            else:
                performer_user, fund_user = second_user, first_user

            with open(ALERTS_DIR, encoding=ENCODING) as in_file:
                performer_line, fund_line = "", ""

                for line in in_file:
                    username = line.split('|')[0]
                    if username == performer_user:
                        performer_line = line.strip()
                    elif username == fund_user:
                        fund_line = line.strip()

            with open(ALERTS_DIR, encoding=ENCODING) as in_file:
                new_content = in_file.read()

                if performer_line != "":
                    new_content = new_content.replace(performer_line, performer_line + f'|Фонд {fund} удалил задание'
                                                                                       f'{task}, поэтому Ваша переписка'
                                                                                       f' с фондом об этом задании была'
                                                                                       f'также удалена\n')
                else:
                    new_content += f'{performer_user}|Фонд {fund} удалил задание {task}, ' \
                                   f'поэтому Ваша переписка с фондом об этом задании была также удалена\n'

                if fund_line != "":
                    new_content = new_content.replace(fund_line, fund_line + f'|Вы удалили задание {task}, поэтому '
                                                                             f'все Ваши переписки об этом задании были'
                                                                             f'также удалены\n')
                else:
                    new_content += f'{fund_user}|Вы удалили задание {task}, ' \
                                   f'поэтому все Ваши переписки об этом задании были также удалены\n'

            with open(ALERTS_DIR, 'w', encoding=ENCODING) as out_file:
                out_file.write(new_content.replace('\n\n', '\n'))"""

    with open(TASKS_DIR, encoding=ENCODING) as in_file:
        before_current_task = ""
        after_current_task = ""
        found_current_task = False
        for line in in_file:
            if line.strip().split('/')[-1] != task:
                if found_current_task:
                    after_current_task += line
                else:
                    before_current_task += line
            else:
                found_current_task = True

    with open(TASKS_DIR, 'w', encoding=ENCODING) as out_file:
        out_file.write(before_current_task)
        out_file.write(after_current_task)

    with open(FUNDS_DIR, encoding=ENCODING) as in_file:
        before_current_fund = ""
        current_fund_line = ""
        after_current_fund = ""
        found_current_fund = False
        for line in in_file:
            if line.split('|')[0] != fund:
                if found_current_fund:
                    after_current_fund += line
                else:
                    before_current_fund += line
            else:
                current_fund_line = line.strip()
                found_current_fund = True

        current_fund_info = current_fund_line.split('|')

    with open(FUNDS_DIR, 'w', encoding=ENCODING) as out_file:
        out_file.write(before_current_fund)
        out_file.write(current_fund_info[0] + '|' + str(int(current_fund_info[1]) - 1) + '|' + current_fund_info[2])
        out_file.write('\n' + after_current_fund)

    with open(API_DIR, encoding='utf-8') as in_file:
        data = json.load(in_file)
        del data[task]

    with open(API_DIR, 'w', encoding='utf-8') as out_file:
        json.dump(data, out_file, ensure_ascii=False, indent='\t')

    with open(FUNDS_DIR, encoding=ENCODING) as in_file:
        before_current_fund = ""
        current_fund_line = ""
        after_current_fund = ""
        found_current_fund = False
        for line in in_file:
            if line.strip().split('|')[0] != fund:
                if found_current_fund:
                    after_current_fund += line
                else:
                    before_current_fund += line
            else:
                current_fund_line = line.strip()
                found_current_fund = True

        current_fund_info = current_fund_line.split('|')

    with open(FUNDS_DIR, 'w', encoding=ENCODING) as out_file:
        out_file.write(before_current_fund)
        out_file.write(current_fund_info[0] + '|' + current_fund_info[1] + '|' + str(int(current_fund_info[2]) + 1))
        out_file.write('\n' + after_current_fund)


"""def check_profanity(text, user):
    with open()"""


def get_top():
    users = []
    with open(TOP_DIR, encoding=ENCODING) as file:
        for i, line in enumerate(file):
            user_info = line.strip().split('|')
            users.append((int(user_info[1]), 9999999999999999999 - i, user_info[0]))

    return sorted(users, reverse=True)


def tag_found(tag, performer_tags):
    i = 0
    for pt in performer_tags:
        if pt.split()[0] == tag:
            return True, i
        i += 1

    return False, i


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/profile')

    return render_template('index.html')


@app.route('/about')
def about():
    return redirect('https://helpers.pythonanywhere.com')


@app.route('/tasks')
def available_tasks():
    from_fund = request.args.get('from')
    query = request.args.get('query')
    tags = request.args.get('tags')

    tags = (tags.split(',') if tags else None)

    if query and query.lower().startswith('tags:'):
        query = None
        tags = query[4:].split(',')

    if tags and tags[-1] == '':
        del tags[-1]

    available_tags = set()
    with open(TASKS_DIR, encoding=ENCODING) as file:
        tasks = []
        for line in file:
            task_info = line.strip().split('|')

            for tag in task_info[2].split():
                available_tags.add(tag.lower())

            from_matches, query_matches, tag_matches = False, False, False
            if from_fund and task_info[3].lower() == from_fund.lower() or not from_fund:
                from_matches = True
            if query and query.lower() in line.lower():
                query_matches = True
            if tags:
                for tag in tags:
                    if tag.lower() in task_info[2].lower():
                        tag_matches = True

            if task_matches(from_fund, query, tags, from_matches, query_matches, tag_matches):
                tasks.append((task_info[-1].split('/')[-1], task_info, task_info[3], task_info[4], task_info[5]))

    sort_options = {'1': 'новизне', '2': 'популярности'}
    sort_by = request.args.get('sort_by')
    option = sort_options[sort_by] if sort_by else ''
    if sort_by == '1':
        tasks.sort(reverse=True, key=lambda t: (datetime.strptime(t[3], '%d.%m.%Y'), int(t[4])))
    elif sort_by == '2':
        tasks.sort(reverse=True, key=lambda t: (int(t[4]), datetime.strptime(t[3], '%d.%m.%Y')))

    return render_template('tasks.html', tasks=tasks, query=(query if query else ""), tags=list(available_tags),
                           reset=(from_fund or query or tags or sort_by), option=option)


@app.route('/profile')
def profile():
    if not current_user.is_authenticated:
        return redirect('/login')

    messages_files = glob(DIR + 'messages/*.txt')
    unread = 0
    for file in messages_files:
        if file.split('/')[-1].split('&')[0] == current_user.username:
            with open(file) as msg_file:
                for line in msg_file:
                    if line.strip().endswith('|to|new'):
                        unread += 1

    if current_user.who == 'performer':
        return render_template('performer_profile.html', name=current_user.name, unread=unread)

    return render_template('fund_profile.html', name=current_user.name, unread=unread)


@app.route('/create')
def create_task():
    if not current_user.is_authenticated:
        return redirect('/login')

    if current_user.who == 'fund':
        return render_template('create_task.html')

    return render_template('only_funds.html')


@app.route('/create', methods=["POST"])
def create_task_processing():
    if not current_user.is_authenticated:
        return redirect('/login')

    if current_user.who != 'fund':
        return render_template('oops.html',
                               error="Упс... На эту страницу не могут попасть исполнители :(",
                               mail="На /create ('POST') попал исполнитель")

    name = request.form.get('name')
    info = request.form.get('info')
    tags = request.form.get('tags')

    if '|' in name:
        flash('Пожалуйста, уберите знак \'|\' из названия задания. Это нужно по техническим причинам. '
              'Извините за неудобства.')
        return render_template('create_task.html', name=name, info=info, tags=tags)
    if '|' in info:
        flash('Пожалуйста, уберите знак \'|\' из описания задания. Это нужно по техническим причинам. '
              'Извините за неудобства.')
        return render_template('create_task.html', name=name, info=info, tags=tags)
    if '|' in tags:
        flash('Пожалуйста, уберите знак \'|\' из тегов. Это нужно по техническим причинам. '
              'Извините за неудобства.')
        return render_template('create_task.html', name=name, info=info, tags=tags)

    typed_tags = tags.split()
    for i in range(len(typed_tags)):
        for j in range(i + 1, len(typed_tags)):
            if typed_tags[i] == typed_tags[j]:
                flash('Теги не должны повторяться')
                return render_template('create_task.html', name=name, info=info, tags=tags)

    url = create(name, info, tags, current_user.name)

    return render_template('done.html', show_social=True, url=('https://www.helpers.today' + url), fund=current_user.name)


@app.route('/task/<task>')
def see_task(task):
    with open(TASKS_DIR, encoding=ENCODING) as in_file:
        before_current_task = ""
        current_task_line = ""
        after_current_task = ""
        found_current_task = False
        rating = ""
        for line in in_file:
            if line.strip().split('/')[-1] != task:
                if found_current_task:
                    after_current_task += line
                else:
                    before_current_task += line
            else:
                found_current_task = True
                current_task_line = line.strip()
                rating = line.split('|')[5]

    with open(TASKS_DIR, 'w', encoding=ENCODING) as out_file:
        out_file.write(before_current_task)
        out_file.write(current_task_line.replace('|' + rating + '|', '|' + str(int(rating) + 1) + '|'))
        out_file.write('\n' + after_current_task)

    with open(TASKS_DIR, encoding=ENCODING) as file:
        for line in file:
            if line.strip().split('/')[-1] == task:
                task_info = line.strip().split('|')
                return render_template('task.html', name=task_info[0], info=task_info[1].split('\\n'),
                                       fund=task_info[3], number=task, tags=task_info[2].split(),
                                       fund_username=User.query.filter_by(name=task_info[3]).first().username)


@app.route('/task/<task>/manage')
def manage_task(task):
    if not current_user.is_authenticated:
        return redirect('/login')

    if current_user.who != 'fund':
        return render_template('oops.html',
                               error="Упс... На эту страницу не могут попасть исполнители :(",
                               mail=f"На /task/{task}/manage попал исполнитель")

    with open(TASKS_DIR) as file:
        for line in file:
            if line.split('/')[-1].strip() == task:
                task_info = line.strip().split('|')
                return render_template('manage_task.html', name=task_info[0], info=task_info[1].split('\\n'),
                                       url=task_info[-1])


@app.route('/task/<task>/edit')
def edit_task(task):
    if current_user.who != 'fund':
        return render_template('oops.html',
                               error="Упс... На эту страницу не могут попасть исполнители :(",
                               mail=f"На /task/{task}/edit попал исполнитель")

    with open(TASKS_DIR) as file:
        for line in file:
            if line.split('/')[-1].strip() == task:
                task_info = line.strip().split('|')
                return render_template('edit_task.html', name=task_info[0],
                                       info=task_info[1].replace('\\n', '\n'), tags=task_info[2])


@app.route('/task/<task>/edit', methods=["POST"])
def edit_task_processing(task):
    if not current_user.is_authenticated:
        return redirect('/login')

    if current_user.who != 'fund':
        return render_template('oops.html',
                               error="Упс... На эту страницу не могут попасть исполнители :(",
                               mail=f"На /task/{task}/edit ('POST') попал исполнитель")

    name = request.form.get('name')
    info = request.form.get('info')
    tags = request.form.get('tags')

    if '|' in name:
        flash('Пожалуйста, уберите знак \'|\' из названия задания. Это нужно по техническим причинам. '
              'Извините за неудобства.')
        return render_template('edit_task.html', name=name, info=info, tags=tags)
    if '|' in info:
        flash('Пожалуйста, уберите знак \'|\' из описания задания. Это нужно по техническим причинам. '
              'Извините за неудобства.')
        return render_template('edit_task.html', name=name, info=info, tags=tags)
    if '|' in tags:
        flash('Пожалуйста, уберите знак \'|\' из тегов. Это нужно по техническим причинам. '
              'Извините за неудобства.')
        return render_template('edit_task.html', name=name, info=info, tags=tags)

    url = edit(task, name, info, tags, current_user.name)

    return render_template('done.html', show_social=True, url=('https://www.helpers.today' + url), fund=current_user.name)


@app.route('/task/<task>/delete', methods=["POST"])
def delete_task(task):
    if not current_user.is_authenticated:
        return redirect('/login')

    if current_user.who != 'fund':
        return render_template('oops.html',
                               error="Упс... На эту страницу не могут попасть исполнители :(",
                               mail="На /delete попал исполнитель")

    delete(task, current_user.name)

    return render_template('done.html', show_social=False)


@app.route('/my')
def my_tasks():
    if not current_user.is_authenticated:
        return redirect('/login')

    if current_user.who != 'fund':
        return render_template('oops.html',
                               error="Упс... На эту страницу не могут попасть исполнители :(",
                               mail="На /my попал исполнитель")

    fund = current_user.name
    tasks = []

    with open(TASKS_DIR, encoding=ENCODING) as file:
        i = 1
        for line in file:
            task_info = line.strip().split('|')
            if task_info[3] == fund:
                tasks.append((i, [task_info[0], task_info[-1]]))
                i += 1

    return render_template('my_tasks.html', tasks=tasks)


@app.route('/fund/<fund>')
def about_fund(fund):
    with open(FUNDS_DIR, encoding=ENCODING) as file:
        for line in file:
            fund_info = line.strip().split('|')
            if fund_info[0] == fund:
                posted = fund_info[1]
                performed = fund_info[2]
                break

    if current_user.is_authenticated and current_user.who == 'fund':
        return render_template('about_fund.html', name=fund, posted=posted, performed=performed, contact=False)

    return render_template('about_fund.html', name=fund, posted=posted, performed=performed, contact=True,
                           url=f'/fund/{fund}')


@app.route('/fund/<fund>/contact')
def contact_fund(fund):
    if fund == current_user.name:
        return render_template('same_fund.html')

    tasks = []
    with open(TASKS_DIR, encoding=ENCODING) as file:
        for line in file:
            if line.strip().split('|')[3] == fund:
                task_info = line.strip().split('|')
                tasks.append((task_info[0], task_info[-1].split('/')[-1]))

    user = User.query.filter_by(name=fund).first()
    return render_template('message_about_task.html', tasks=tasks, fund_username=user.username, fund=user.name,
                           email=user.email)


@app.route('/user/<user>')
def about_user(user):
    try:
        user = User.query.filter_by(username=user).first()
        if user.who == 'fund':
            return redirect(f'/fund/{user.name}')
    except AttributeError:
        return render_template('oops.html',
                               error="Упс... Данного пользователя не существует",
                               mail="/user/<user> несуществующий пользователь")

    tags = []
    with open(TAGS_DIR, encoding=ENCODING) as file:
        for line in file:
            user_info = line.strip().split('|')
            if user_info[0] == user.username:
                tags = user_info[1:]

    tags_frequency = tags[:]
    for i in range(len(tags)):
        tag_info = tags[i].split()
        tags[i] = tag_info[0]
        tags_frequency[i] = tag_info[1]

    position = None
    for i, top_user in enumerate(get_top()):
        if top_user[2] == user.username:
            position = i + 1

    print(position)

    with open(TOP_DIR, encoding=ENCODING) as file:
        for line in file:
            user_info = line.strip().split('|')
            if user_info[0] == user.username:
                return render_template('about_user.html', username=user.username, name=user.name,
                                       avatar=str(randint(1, 5)), completed=user_info[1], position=position,
                                       tags=tags, tags_frequency=tags_frequency,
                                       fund=(current_user.is_authenticated and current_user.who == 'fund'))

    return render_template('about_user.html', username=user.username, name=user.name,
                           avatar=str(randint(1, 5)), completed='0',  position=position,
                           tags=tags, tags_frequency=tags_frequency,
                           fund=(current_user.is_authenticated and current_user.who == 'fund'))


@app.route('/messages', methods=["GET", "POST"])
def messages():
    if not current_user.is_authenticated:
        return redirect('/login')

    messages_with = request.args.get('with')
    about_task = request.args.get('about')
    messages_files = glob(DIR + 'messages/*.txt')

    new = request.form.get('new')
    if new:
        with open(DIR + f'messages/{current_user.username}&{messages_with}&{about_task}.txt', 'a') as file:
            file.write(new + '|from|new\n')
        with open(DIR + f'messages/{messages_with}&{current_user.username}&{about_task}.txt', 'a') as file:
            file.write(new + '|to|new\n')

    if about_task and messages_with:
        try:
            with open(DIR + f'messages/{current_user.username}&{messages_with}&{about_task}.txt') as file:
                my_messages = []
                found_new = False
                for i, line in enumerate(file):
                    if i == 0:
                        continue

                    message_info = line.strip().split('|')
                    if message_info[1] == 'to' and message_info[2] == 'new' and not found_new:
                        my_messages.append(['\\hNEW\\h'])
                        found_new = True
                    my_messages.append((message_info[0], message_info[1], message_info[2]))

            messages_to = ""
            messages_from = ""
            task_name = ""
            with open(DIR + f'messages/{current_user.username}&{messages_with}&{about_task}.txt') as file:
                for i, line in enumerate(file):
                    if i == 0:
                        task_name = line
                        continue

                    if line.strip().endswith('|to|new'):
                        messages_to += line.strip()[:-7] + '|to|read' + '\n'
                        messages_from += line.strip()[:-7] + '|from|read' + '\n'
                    else:
                        messages_to += line
                        message_info = line.strip().split('|')
                        if message_info[1] == 'to':
                            messages_from += message_info[0] + '|from|' + message_info[2]
                        else:
                            messages_from += message_info[0] + '|to|' + message_info[2]
                        messages_from += '\n'

            with open(DIR + f'messages/{current_user.username}&{messages_with}&{about_task}.txt', 'w') as to_file, \
                    open(DIR + f'messages/{messages_with}&{current_user.username}&{about_task}.txt', 'w') as from_file:
                to_file.write(task_name)
                to_file.write(messages_to)
                from_file.write(task_name)
                from_file.write(messages_from)

            return render_template('messages.html', messages=my_messages, task=about_task, performer=messages_with)

        except FileNotFoundError:
            found = False
            task_name = ""
            with open(TASKS_DIR, encoding=ENCODING) as file:
                for line in file:
                    if line.strip().split('/')[-1] == about_task:
                        found = True
                        task_name = line.split('|')[0]
                        break

            if found:
                with open(DIR + f'messages/{current_user.username}&{messages_with}&{about_task}.txt', 'w') as file1, \
                        open(DIR + f'messages/{messages_with}&{current_user.username}&{about_task}.txt', 'w') as file2:
                    file1.write(task_name + '\n')
                    file2.write(task_name + '\n')

                return render_template('messages.html', messages=[], task=about_task, performer=messages_with)

            return render_template('oops.html',
                                   error=f"Задания {about_task} не существует",
                                   mail=f"/messages?with&about={about_task} (задания не существует)")

    if not about_task and not messages_with:
        query = request.args.get('query')
        message_matches = False

        my_messages = []
        msg_index = 1
        for file in messages_files:
            data = file.split('/')[-1].split('&')
            if data[0] == current_user.username:
                unread = 0
                with open(file) as msg_file:
                    for i, line in enumerate(msg_file):
                        if i == 0:
                            task_name = line.strip()
                            continue

                        if line.strip().endswith('|to|new'):
                            unread += 1
                        if query and query.lower() in line.split('|')[0].lower():
                            message_matches = True

                if not query or query.lower() in data[1].lower() or query.lower() in data[2][:-4].lower() or \
                        query.lower() in task_name.lower() or message_matches:
                    my_messages.append((data[1], data[2][:-4], f'Задание №{data[2][:-4]} '
                                                               f'({task_name})', unread, msg_index))
                    msg_index += 1

        return render_template('my_messages.html', messages=my_messages, query=(query if query else ''))

    abort(400)


@app.route('/message/<message>/delete', methods=["POST"])
def delete_message(message):
    if not current_user.is_authenticated:
        return redirect('/login')

    messages_files = glob(DIR + 'messages/*.txt')
    count = 0
    for file in messages_files:
        data = file.split('/')[-1].split('&')
        if data[0] == current_user.username:
            count += 1
        if count == int(message):
            remove(DIR + f'messages/{data[0]}&{data[1]}&{data[2]}')
            break

    return render_template('done.html', show_social=False)


@app.route('/completed')
def task_completed():
    if not current_user.is_authenticated:
        return redirect('/login')

    task = request.args.get('task')
    performer = request.args.get('performer')

    if current_user.who != 'fund':
        with open(TASKS_DIR, encoding=ENCODING) as file:
            for line in file:
                if line.strip().split('/')[-1] == task:
                    fund = User.query.filter_by(name=line.split('|')[3]).first()
                    return render_template('oops.html',
                                           error=f"Только фонды могут отметить задание выполненным. Если Вы уверены, "
                                                 f"что Вы выполнили "
                                                 f"<a href='/task/{task}' class='link'>задание {task}</a>, напишите"
                                                 f" фонду {fund.name} в "
                                                 f"<a href='/messages?with={fund.username}&about={task}' class='link'>"
                                                 f"личные сообщения</a>",
                                           mail="На /completed попал исполнитель")

    if not task and not performer:
        abort(400)

    if not task:
        tasks = []
        with open(TASKS_DIR, encoding=ENCODING) as file:
            for line in file:
                if line.strip().split('|')[3] == current_user.name:
                    task_info = line.strip().split('|')
                    tasks.append((task_info[0], task_info[-1].split('/')[-1]))

        return render_template('completed_what_task.html', performer=performer, tasks=tasks)

    with open(TASKS_DIR, encoding=ENCODING) as tasks_file:
        for line in tasks_file:
            if line.strip().split('/')[-1] == task:
                if line.strip().split('|')[3] != current_user.name:
                    return render_template('oops.html',
                                           error=f"Вы не можете отметить задание выполненным, так как "
                                                 f"оно было выложено другим фондом",
                                           mail="На /completed попал другой фонд")
                break

    performer_score = 0
    before_performer = ""
    after_performer = ""
    found_performer = False
    performer_info = []
    with open(TOP_DIR, encoding=ENCODING) as in_file:
        for line in in_file:
            performer_data = line.strip().split('|')
            if performer_data[0] != performer:
                if found_performer:
                    after_performer += line
                else:
                    before_performer += line
            else:
                found_performer = True
                performer_score = int(performer_data[1])
                performer_info = performer_data[:]

    if len(performer_info) == 2 or task not in performer_info[2:]:
        with open(TOP_DIR, 'w', encoding=ENCODING) as out_file:
            out_file.write(before_performer)

            out_file.write(performer + f'|{str(performer_score + 1)}|')
            for ct in performer_info[2:]:
                out_file.write(ct + '|')
            out_file.write(task + '\n')

            out_file.write(after_performer)

        tags = []
        with open(TASKS_DIR, encoding=ENCODING) as file:
            for line in file:
                if line.strip().split('/')[-1] == task:
                    tags = line.split('|')[2].split()
                    break

        before_performer = ""
        performer_line = ""
        after_performer = ""
        found_performer = False
        with open(TAGS_DIR, encoding=ENCODING) as in_file:
            for line in in_file:
                performer_data = line.strip().split('|')
                if performer_data[0] != performer:
                    if found_performer:
                        after_performer += line
                    else:
                        before_performer += line
                else:
                    found_performer = True
                    performer_line = line.strip()

        performer_tags = performer_line.split('|')
        new_tags = {}
        for tag in tags:
            tf = tag_found(tag, performer_tags)
            if tf[0]:
                new_tags[tag] = str(int(performer_tags[tf[1]].split()[1]) + 1)

            else:
                new_tags[tag] = '1'

        for i, tag in enumerate(performer_tags):
            if i == 0:
                continue

            tag_info = tag.split()
            if tag_info[0] not in new_tags:
                new_tags[tag_info[0]] = tag_info[1]

        with open(TAGS_DIR, 'w', encoding=ENCODING) as out_file:
            out_file.write(before_performer)

            out_file.write(performer + '|')
            for i, key in enumerate(new_tags.keys()):
                if i == len(new_tags.keys()) - 1:
                    out_file.write(f'{key} {new_tags[key]}\n')
                else:
                    out_file.write(f'{key} {new_tags[key]}|')

            out_file.write(after_performer)

        return render_template('task_completed.html', task=task, performer=performer,
                               url=f'https://www.helpers.today/user/{performer}')

    return render_template('oops.html',
                           error=f"Пользователь {performer} уже выполнил задание {task}",
                           mail=f"Пользователь {performer} уже выполнил задание {task}")


@app.route('/top')
def top():
    query = request.args.get('query')

    users = get_top()

    if query:
        users_match = []
        for i, user in enumerate(users):
            if query in user[2]:
                users_match.append((i + 1, user))
        return render_template('top.html', users_match=users_match, query=query)

    return render_template('top.html', users=enumerate(users), query='')


@app.route('/me')
def me():
    if not current_user.is_authenticated:
        return redirect('/login')

    return redirect(f'/user/{current_user.username}')


@app.route('/tags')
def all_tags():
    available_tags = set()
    with open(TASKS_DIR, encoding=ENCODING) as file:
        for line in file:
            task_info = line.strip().split('|')
            for tag in task_info[2].split():
                available_tags.add(tag.lower())

    return render_template('tags.html', tags=list(available_tags))


@app.route('/more')
def other_functions():
    return render_template('more.html')


@app.route('/ios')
def ios_app():
    return redirect('comingsoon.hlprs.xyz')


@app.route('/android')
def android_app():
    return redirect('comingsoon.hlprs.xyz')


@app.route('/huawei')
def huawei_app():
    return redirect('comingsoon.hlprs.xyz')


@app.route('/bot')
def telegram_bot():
    return redirect('comingsoon.hlprs.xyz')


@app.route('/api')
def api():
    with open(API_DIR, encoding='utf-8') as file:
        return jsonify(json.load(file))


@app.route('/external-create')
def external_create():
    password = request.args.get('password')

    if isinstance(password, str) and hashlib.sha224(bytes(password, 'utf-8')).hexdigest() == \
            'fe08e2dca23b362b24bb43566576c36c97810c5d8ce4a5dc86afc21c':
        create(request.args.get('name'), request.args.get('info'), request.args.get('tags'), request.args.get('fund'))
        return 'done'

    return 'declined'


@app.route('/external-edit')
def external_edit():
    password = request.args.get('password')

    if isinstance(password, str) and hashlib.sha224(bytes(password, 'utf-8')).hexdigest() == \
            'fe08e2dca23b362b24bb43566576c36c97810c5d8ce4a5dc86afc21c':
        edit(request.args.get('number'), request.args.get('name'), request.args.get('info'), request.args.get('tags'),
             request.args.get('fund'))
        return 'done'

    else:
        return 'declined'


@app.route('/external-delete')
def external_delete():
    password = request.args.get('password')

    if isinstance(password, str) and hashlib.sha224(bytes(password, 'utf-8')).hexdigest() == \
            'fe08e2dca23b362b24bb43566576c36c97810c5d8ce4a5dc86afc21c':
        delete(request.args.get('number'), request.args.get('fund'))
        return 'done'

    else:
        return 'declined'


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/logout')
def logout():
    if not current_user.is_authenticated:
        return redirect('/')

    logout_user()
    return redirect('/')


@app.route('/signup', methods=["POST"])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    who = request.form.get('who')
    username = request.form.get('username')

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Пользователь с этим адресом email уже существует')
        return render_template('signup.html', name=name, username=username)

    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username уже занят')
        return render_template('signup.html', name=name, email=email)

    possible_chars = 'qwertyuiopasdfghjklzxcvbnm1234567890_.'
    for char in username:
        if char.lower() not in possible_chars:
            flash('Username может состоять только из латинских букв, цифр, знаков точки и нижнего подчеркивания')
            return render_template('signup.html', name=name, email=email)

    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'),
                    who=('performer' if who == '0' else 'fund'), username=username)

    if who == '1':
        with open(FUNDS_DIR, encoding=ENCODING) as file:
            for line in file:
                if line.strip().split('|')[0] == name:
                    flash('Данный фонд уже есть в базе')
                    return redirect('/signup')

        with open(FUNDS_DIR, 'a+', encoding=ENCODING) as file:
            file.write(name + '|0|0\n')

    db.session.add(new_user)
    db.session.commit()

    login_user(new_user, remember=False)

    return redirect('/profile')


@app.route('/login', methods=["POST"])
def login_post():
    user_data = request.form.get('user')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=user_data).first()
    if not user or not check_password_hash(user.password, password):
        flash('Неверный логин или пароль. Попробуйте еще раз')
        return redirect('/login')

    """user = User.query.filter_by(username=user_data).first()
    if not user or not check_password_hash(user.password, password):
        flash('Неверный логин или пароль. Попробуйте еще раз')
        return redirect('/login')"""

    login_user(user, remember=remember)
    return redirect('/profile')


@app.route('/check-login/<login>')
def check_login(login):
    password = request.args.get('password')

    if isinstance(password, str):
        password = bytes(password, 'utf-8')

    else:
        return 'declined'

    if hashlib.sha224(password).hexdigest() == 'fe08e2dca23b362b24bb43566576c36c97810c5d8ce4a5dc86afc21c':
        if User.query.filter_by(username=login).first():
            return 'username'

        elif User.query.filter_by(email=login).first():
            return 'email'

        return 'none'

    return 'declined'


@app.route('/check-password/<login>/<password>')
def check_password(login, password):
    keyword = request.args.get('password')
    mode = request.args.get('mode')

    if isinstance(keyword, str):
        keyword = bytes(keyword, 'utf-8')

    else:
        return 'declined'

    if hashlib.sha224(keyword).hexdigest() == 'fe08e2dca23b362b24bb43566576c36c97810c5d8ce4a5dc86afc21c':
        user = None

        if mode == 'username':
            user = User.query.filter_by(username=login).first()
        elif mode == 'email':
            user = User.query.filter_by(email=login).first()

        if user:
            return 'yep ' + user.username if check_password_hash(user.password, password) else 'nope'

        return 'error'

    return 'declined'
