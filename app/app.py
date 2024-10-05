
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect
)

from sqlalchemy import (
    create_engine,
    text,
    exc
)

import datetime as dt

import os
from dotenv import load_dotenv
import uuid

import pandas as pd

load_dotenv(".env",override=True)

CONN_STR = os.environ.get("CONN_STR")

server = Flask(__name__)

@server.route('/')
def index():
    
    # Home page, that lists projects in projects table
    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    projects=pd.read_sql("select * from projects",con=conn)
    members=pd.read_sql("select * from members",con=conn)
    conn.close()
    engine.dispose()

    projects['link'] = projects['pid'].apply(lambda x: f'<a href="{url_for("project", pid=x)}">link</a>')
    members['link'] = members['mid'].apply(lambda x: f'<a href="{url_for("member", mid=x)}">link</a>')

    html_tbl = projects[['name','text','link']].to_html(escape=False,classes='table table-striped', index=False)
    team_tbl = members[['name','role','link']].to_html(escape=False,classes='table table-striped', index=False)

    return render_template('index.html',username='Jason',projects=html_tbl,team_tbl=team_tbl)

@server.route('/create_project',methods=['GET', 'POST'])
def create_project():

    # Create a new project with this form. A unique ID is created along with the project name and text.
    result = ''
    if request.method == 'POST':
        name = request.form['input_name']
        text = request.form['input_text']
        result = f'Processed: {name}: {text}'  

        pid = uuid.uuid4().__str__()

        store_df = pd.DataFrame(
            {'pid':[pid],
             'name':[name],
             'text':[text]}
        )

        try:  
            engine = create_engine(url = CONN_STR)
            conn = engine.connect()
            store_df.to_sql('projects',index=False,if_exists='append',con=conn)
            conn.close()
            engine.dispose()

            return redirect(url_for('index'))
        except exc.IntegrityError:
            return render_template('create_project.html',result='The app name probably exists. Try another name.')

    return render_template('create_project.html',result=result)

@server.route('/project/<pid>')
def project(pid):

    # Look up everything about a project. By pid. If it doesn't exist, app will say so.
    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    projects=pd.read_sql(
        f"select * from projects where pid = '{pid}'",
        con=conn)
    tasks=pd.read_sql(
        f"select * from tasks where pid = '{pid}'",
        con=conn)
    members=pd.read_sql(
        f"select * from members",
        con=conn)
    conn.close()
    engine.dispose()

    if len(projects)<1:
        text = ''
        return render_template('project.html',pid='Project not found',
                            name='404',text='No project was found with that ID. Go to home and follow a project link.')

    name = projects['name'].values[0]
    text = projects['text'].values[0]

    tasks['link'] = tasks['tid'].apply(lambda x: f'<a href="{url_for("task", tid=x)}">link</a>')

    html_tbl = tasks[['task_name','text','start_dt','end_dt','link']].to_html(escape=False,classes='table table-striped', index=False)

    return render_template('project.html',pid=pid,
                           name=name,text=text,tasks_tbl=html_tbl)

@server.route('/delete_project/<pid>', methods=['POST'])
def delete_project(pid):

    with open("sql/dml/delete.sql",'r') as file:
        query = file.read()
    
    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    conn.execute(text(query.format(id_val=pid,tbl='projects',id_col='pid')))
    conn.commit()
    conn.execute(text(query.format(id_val=pid,tbl='tasks',id_col='pid')))
    conn.commit()
    conn.close()
    engine.dispose()

    return redirect(url_for('index'))

@server.route('/create_member',methods=['GET', 'POST'])
def create_member():

    # Create a new project with this form. A unique ID is created along with the project name and text.
    result = ''
    if request.method == 'POST':
        name = request.form['member_name']
        text = request.form['member_text']
        result = f'Processed: {name}: {text}'  

        mid = uuid.uuid4().__str__()

        store_df = pd.DataFrame(
            {'mid':[mid],
             'name':[name],
             'role':[text]}
        )

        try:  
            engine = create_engine(url = CONN_STR)
            conn = engine.connect()
            store_df.to_sql('members',index=False,if_exists='append',con=conn)
            conn.close()
            engine.dispose()

            return redirect(url_for('index'))
        except exc.IntegrityError:
            return render_template('create_member.html',msg='The member already exists')

    return render_template('create_member.html', msg=result)

@server.route('/member/<mid>')
def member(mid):

    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    members=pd.read_sql(
        f"select * from members where mid = '{mid}'",
        con=conn)
    conn.close()
    engine.dispose()

    
    if len(members)<1:
        text = ''
        return render_template('member.html',pid='Member not found',
                            name='404',text='That member was\'nt found.')

    name = members['name'].values[0]
    role = members['role'].values[0]
    
    return render_template('member.html',mid=mid,
                           name=name,role=role) 


@server.route('/delete_member/<mid>', methods=['POST'])
def delete_member(mid):

    with open("sql/dml/delete.sql",'r') as file:
        query = file.read()
    
    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    conn.execute(text(query.format(id_col='mid',tbl='members',id_val=mid)))
    conn.commit()
    conn.close()
    engine.dispose()

    return redirect(url_for('index'))


@server.route('/create_task/<pid>',methods=['POST'])
def create_task(pid):

    name = request.form['task_name']
    text = request.form['task_text']
    start = request.form['dt1']
    close = request.form['dt2']
    
    
    tid = uuid.uuid4().__str__()

    load_data = pd.DataFrame(
        {
            'pid':[pid],
            'tid':[tid],
            'task_name':[name],
            'text':[text],
            'start_dt':[start],
            'end_dt':[close]
        }
    )

    try:  
        engine = create_engine(url = CONN_STR)
        conn = engine.connect()
        load_data.to_sql('tasks',index=False,if_exists='append',con=conn)
        conn.close()
        engine.dispose()

        return redirect(url_for('project',pid=pid))
    except exc.IntegrityError:
        return render_template(url_for('project',pid=pid),result='The app name probably exists. Try another name.')

@server.route('/task/<tid>')

def task(tid):
    # Look up everything about a project. By pid. If it doesn't exist, app will say so.
    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    tasks=pd.read_sql(
        f"select * from tasks where tid = '{tid}'",
        con=conn)
    conn.close()
    engine.dispose()

    if len(tasks)<1:
        return render_template('task.html',tid='Task not found',
                            name='404',text='That task was\'nt found.')
    
    html_tbl = tasks[['task_name','text','start_dt','end_dt','tid']].to_html(escape=False,classes='table table-striped', index=False)

    return render_template('task.html',tid=tid,
                            name=tasks['task_name'].values[0],
                            tasks_tbl=html_tbl)