from flask import Flask,request           # import flask
from flask import render_template
import datetime
import json


app = Flask(__name__)             # create an app instance

def getDateTime(frame,start=True):
    second = frame /24
    minute = (second % 3600) /60
    hour = second /3600
    second= second % 60
    if start:
    	return datetime.datetime(1970,1,1,int(hour),int(minute),int(second),100) 
    else:
    	return datetime.datetime(1970,1,1,int(hour),int(minute),int(second)) 


@app.route("/")                   # at the end point /
def index():                      # call method hello
    return render_template('upload.html')

@app.route("/submitfile",methods=["POST"])  
def submitfile():                      # call method hello
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
    with open(uploaded_file.filename) as f:
        data = json.load(f)
        dataForVisjs = {}
    currentIndex = 1 # it's for the id in visjs
    indexSeq = 1 # it's for the group in visjs ( 1 is for loop.index jinja )
    alldata = {}

    for c in data["tracks"]["children"]:
        sequenceName = c["name"]
        dataForVisjs[sequenceName] = []
        delta = 0
        for s in c["children"]:
            alldata[currentIndex] = s
            startTime = delta
            delta = delta+s["source_range"]["duration"]["value"]
            dataForVisjs[sequenceName].append(
                      {
                         "id": currentIndex,
                         "idseq": indexSeq,
                         "name": s["name"],
                         "className" :s["OTIO_SCHEMA"].replace(".",""), # CSS doesn't like dot.
                         "startTime": getDateTime(startTime),
                         "endTime" : getDateTime(delta,False)
                      }
                )
            currentIndex = currentIndex + 1
        indexSeq = indexSeq + 1
    return render_template('index.html',data=dataForVisjs,alldata=alldata,name=data["name"])

if __name__ == "__main__":        # on running python app.py
    app.run(debug=True)                     # run the flask app
