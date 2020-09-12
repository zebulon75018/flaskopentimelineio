#
# charles vidal. 
# opentimelineio integration with flask for visualisation.
#
#

from flask import Flask,request  
from flask import render_template
import datetime
import json
import pprint

import opentimelineio as otio
from opentimelineio.adapters import cmx_3600

app = Flask(__name__)             # create an app instance

def getDateTime(second):
    #
    # return a datetime from a number of seconds.
    # usefull for jinja and visjs.
    # @param: second float ( result of clip.range_in_parent().start_time.to_seconds() )
    # @return a datetime.
    #
    minute = (second % 3600) /60
    hour = second /3600
    second= second % 60
    return datetime.datetime(1970,1,1,int(hour),int(minute),int(second)) 



def generatorDoc(mod):
    # make for the jinja templating a 3 level array to display documentation
    # from the package api __doc__.
    # I'm sure there this better ( but I don't find it to generate or 
    # link to html file doc of package)
    #
    # @param : pakage ( opentimelineio)
    # @return : array of namespace [key][key][key] = doc ...
    #
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

def getNameSequence(track,prefix,index):
    # return a name of track :
    # if name is empty (appears with xml) , the return prefix index
    # else track.name 
    #
    # @return string 

    if track.name is "":
        return "%s%d" % (prefix,index)
    return track.name

def addClip(track,sequenceName,currentIndex,indexSeq,dataForVisjs,dataMarker,classname):
    # factorisation for a track ( video track , audio track )
    # fill the dataForVisjs,dataMarker with information of track. 
    # I should thinking how may be make the method in an object ...
    # each element of visjs should have an unique id.
    #  
    # @param track
    # @param sequenceName : string 
    # @param currentIndex : integer ( usefull for visjs )
    # @param indexSeq : integer ( userfull for visjs group index )
    # @param dataForVisjs array 
    # @param dataMarker   array 
    # @param classname string 
    # @return integer ( new currentIndex )

    for clip in track.each_clip():
        dataForVisjs[sequenceName].append(
                    {
                        "id": currentIndex,
                        "idseq": indexSeq,
                        "name": clip.name,
                        "className" : classname,
                        "startTime": getDateTime(clip.range_in_parent().start_time.to_seconds()),
                        "endTime" : getDateTime(clip.range_in_parent().start_time.to_seconds() + clip.range_in_parent().duration.to_seconds())
                    }
            )
        for m in clip.markers:
                currentIndex = currentIndex + 1
                dataMarker.append(
                    {
                        "id": currentIndex,
                        "idseq": indexSeq,
                        "startTime": getDateTime(clip.range_in_parent().start_time.to_seconds()+m.marked_range.start_time.to_seconds()),
                        "name" : "marker" #m.name
                    }
                )

        currentIndex = currentIndex + 1
    return currentIndex
    
#
# Route , binding url and python method
#
@app.route("/")
def index():
    # show opentimelineio plugin could be interesting in the home page.

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


@app.route("/doc")           
def doc():
    return render_template('doc.html',doc=generatorDoc("otio"))
    
@app.route("/submitfile",methods=["POST"])  
def submitfile():
    uploaded_file = request.files['file']
    timeline = otio.adapters.read_from_file(uploaded_file.filename)

    # Data for jinja templating.
    dataForVisjs = {}
    dataMarker = []
    currentIndex = 1 # it's for the id in visjs
    indexSeq = 1 # it's for the group in visjs ( 1 is for loop.index jinja )
    #alldata = {}

    #print("timeline.global_start_time " , timeline.global_start_time)
    totalduration =  timeline.duration().value
    for vt in timeline.video_tracks():
        sequenceName = getNameSequence(vt,"Vid",indexSeq)
        dataForVisjs[sequenceName] = []
        currentIndex = addClip(vt,sequenceName,currentIndex,indexSeq,dataForVisjs,dataMarker,"video")
        indexSeq = indexSeq + 1

    indexAudioTrack = 1
    
    for at in timeline.audio_tracks():
        sequenceName = getNameSequence(at,"Audio",indexSeq)
        dataForVisjs[sequenceName] = []
        currentIndex = addClip(at,sequenceName,currentIndex,indexSeq,dataForVisjs,dataMarker,"audio")
        indexSeq = indexSeq + 1
        indexAudioTrack = indexAudioTrack + 1
 
    return render_template('index.html',
                            totalduration=totalduration,
                            data=dataForVisjs,
                            dataMarker = dataMarker,
                            name=timeline.name)

if __name__ == "__main__":        # on running python app.py
    app.run(debug=True)                     # run the flask app
