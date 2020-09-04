from flask import Flask,request           # import flask
from flask import render_template
import datetime
import json
import pprint

import opentimelineio as otio
from opentimelineio.adapters import cmx_3600

app = Flask(__name__)             # create an app instance

def getDateTime(second):
    minute = (second % 3600) /60
    hour = second /3600
    second= second % 60
    return datetime.datetime(1970,1,1,int(hour),int(minute),int(second)) 


@app.route("/")
def index():                      # call method hello
    plugin_types = otio.plugins.manifest.OTIO_PLUGIN_TYPES
    # load all the otio plugins
    active_plugin_manifest = otio.plugins.ActiveManifest()

    plugins = {}
    for pt in plugin_types:
        plugin_by_type = getattr(active_plugin_manifest, pt)
        plugins[pt] = [
                p for p in plugin_by_type
        ]
    return render_template('upload.html',
                        plugin_types=plugin_types,
                        plugins= plugins,
                        active_plugin_manifest=active_plugin_manifest)

def generatorDoc(mod):
    result= {}
    for m in dir(eval(mod)):
        if m[:2] != "__":
            result[m]={}
            for d in dir(eval("%s.%s" %(mod,m))):
                if d[:2] != "__":
                    result[m][d]={}
                    for d2 in dir(eval("%s.%s.%s" % (mod,m,d))):
                        if d2[:2] != "__":
                            try:
                                result[m][d][d2]=eval("%s.%s.%s.%s.__doc__" % (mod,m,d,d2))
                            except Exception as  e:
                                print(e)
    return result


@app.route("/doc")           
def doc():
    return render_template('doc.html',doc=generatorDoc("otio"))
    
@app.route("/submitfile",methods=["POST"])  
def submitfile():                      # call method hello
    uploaded_file = request.files['file']
    timeline = otio.adapters.read_from_file(uploaded_file.filename)

    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
    with open(uploaded_file.filename) as f:
        data = json.load(f)
        dataForVisjs = {}
        dataForHtml = {}

    currentIndex = 1 # it's for the id in visjs
    indexSeq = 1 # it's for the group in visjs ( 1 is for loop.index jinja )
    #alldata = {}

    print("timeline.global_start_time " , timeline.global_start_time)
    totalduration =  timeline.duration().value
    for vt in timeline.video_tracks():
        sequenceName = vt.name
        dataForVisjs[sequenceName] = []
        sequenceName = vt.name
        dataForHtml[sequenceName] = []
        for clip in vt.each_clip():
            dataForHtml[sequenceName].append(
			{
                         "name": clip.name,
                         "startTime": (clip.range_in_parent().start_time.value/totalduration)*100,
                         "duration" : (clip.duration().value/totalduration)*100
            })

            dataForVisjs[sequenceName].append(
                      {
                         "id": currentIndex,
                         "idseq": indexSeq,
                         "name": clip.name,
                         #"className" :s["OTIO_SCHEMA"].replace(".",""), # CSS doesn't like dot.
                         "startTime": getDateTime(clip.range_in_parent().start_time.to_seconds()),
                         "endTime" : getDateTime(clip.range_in_parent().start_time.to_seconds() + clip.range_in_parent().duration.to_seconds())
                      }
                )
            currentIndex = currentIndex + 1
        indexSeq = indexSeq + 1

            
 
    return render_template('index.html',
                            totalduration=totalduration,
                            data=dataForVisjs,
                            dataH=dataForHtml,
                            #alldata=alldata,
                            name=data["name"])

if __name__ == "__main__":        # on running python app.py
    app.run(debug=True)                     # run the flask app
