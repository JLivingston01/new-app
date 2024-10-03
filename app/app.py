
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
    conn.close()
    engine.dispose()

    projects['link'] = projects['pid'].apply(lambda x: f'<a href="{url_for("project", pid=x)}">link</a>')

    html_tbl = projects[['name','text','link']].to_html(escape=False,classes='table table-striped', index=False)

    return render_template('index.html',username='Jason',projects=html_tbl)

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
    conn.close()
    engine.dispose()

    if len(projects)<1:
        text = ''
        return render_template('project.html',pid='Project not found',
                            name='404',text='No project was found with that ID. Go to home and follow a project link.')

    name = projects['name'].values[0]
    text = projects['text'].values[0]

    return render_template('project.html',pid=pid,
                           name=name,text=text)


@server.route('/delete_project/<pid>', methods=['POST'])
def delete_project(pid):

    with open("sql/dml/delete.sql",'r') as file:
        query = file.read()
    
    engine = create_engine(url = CONN_STR)
    conn = engine.connect()
    conn.execute(text(query.format(pid=pid)))
    conn.commit()
    conn.close()
    engine.dispose()

    return redirect(url_for('index'))