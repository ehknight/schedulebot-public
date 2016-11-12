import os
import flask
from flask import render_template, request, redirect, g
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from celery import Celery

app = flask.Flask(__name__)

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_BACKEND='redis://localhost:6379'
)

celery = Celery('app', broker="redis://localhost:6379", backend='redis://localhost:6379')


# def make_celery(app):
#     celery = Celery(app.import_name, backend=app.config['CELERY_BACKEND'],
#                     broker=app.config['CELERY_BROKER_URL'])
#     celery.conf.update(app.config)
#     TaskBase = celery.Task
#     class ContextTask(TaskBase):
#         abstract = True
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return TaskBase.__call__(self, *args, **kwargs)
#     celery.Task = ContextTask
#     return celery
# celery = make_celery(app)

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('service_key.json', scope)

gc = gspread.authorize(credentials)

def grouped(iterable, n):
    return list(zip(*[iter(iterable)]*n))

@app.route('/')
def home():
    print("test")
    return render_template("index.html")

@app.route("/index.html")
def index_html():
    return home()

@app.route('/classUpload', methods=['POST'])
def classupload():
    print("i've received the classupload")
    blocks = grouped([x[1] for b in grouped(sorted(list(request.form.to_dict().items()),
                                                  key=lambda x: x[0]),3) for x in b], 3)
    classes = []
    for item in blocks:
        classes.append(item[0]+" ("+item[1]+")\n"+item[2])
    spreadsheetURL = request.form['spreadsheeturl']
    # print(classes)
    schedule.delay(spreadsheetURL, classes)
    return redirect(spreadsheetURL)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown-now', methods=['POST', 'GET'])
def shutdown():
  shutdown_server()
  return "Server is shutting down..."
  # return "Nice try- schedulebot is immortal"

@celery.task
def schedule(spreadsheetURL, classes):
    sh = gc.open_by_url(spreadsheetURL)
    print("received")
    print("GOING")
    for wk in sh.worksheets():
        for cell in wk._fetch_cells():
            for ind in range(8):
                if classes[ind].startswith(" ("):
                    continue
                val=cell.value
                if "Block "+str(ind+1)+"\n" in val:
                    wk.update_cell(int(str(cell.row)),int(str(cell.col)),val.replace("Block " + str(ind + 1),
                                                                                            str(ind+1)+". "+classes[ind]))
    return True

if __name__=="__main__":
    app.secret_key = 'wow this is so secret'
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, debug=True)
