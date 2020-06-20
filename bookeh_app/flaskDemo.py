from flask import Flask, render_template

from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from tornado.ioloop import IOLoop
import sqlite3;
import threading
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bookeh_app.bookehApp import bookehApp;
app = Flask(__name__)
ba = None;
#https://github.com/bokeh/bokeh/blob/1.1.0/examples/howto/server_embed/standalone_embed.py
#https://medium.com/@n.j.marey/my-experience-with-flask-and-bokeh-plus-a-small-tutorial-7b49b2e38c76
def modify_doc(doc):
    tabs = ba.generateTabs();
    doc.add_root(tabs)
    doc.theme = Theme(filename="theme.yaml")


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    global  ba;
    print("in bk_ worker : 35 : ", threading.current_thread());
    ba = bookehApp(); #inititating the sql connection in the server thread
    server = Server({'/bkapp': modify_doc}, io_loop=IOLoop(), allow_websocket_origin=["*"])
    server.start()
    server.io_loop.start()

from threading import Thread
Thread(target=bk_worker).start()

print("main server in :", threading.current_thread())
if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(host='0.0.0.0',port=8000)