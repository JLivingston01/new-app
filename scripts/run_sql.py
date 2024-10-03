
from sqlalchemy import (
    create_engine,
    text
)

import click

import logging

#logger = logging.Logger(__name__,level=logging.INFO)

CONN_STR = "sqlite:///.data/sqlite.db"

@click.command()
@click.option('-q',type=str,help='query to run')
@click.option('-t',type=str,help='table name',required=False)
def main(q,t=None):

    with open(q,'r') as file:
        query = file.read()
        file.close()

    engine = create_engine(CONN_STR,echo=True)
    conn = engine.connect()

    if t:
        conn.execute(text(query.format(tbl=t)))
    else:
        conn.execute(text(query))
    conn.commit()
    conn.close()
    engine.dispose()

    return

if __name__=='__main__':
    main()