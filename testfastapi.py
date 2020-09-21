from typing import Optional

from fastapi import FastAPI, File, UploadFile
from fastapi.openapi.utils import get_openapi
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

import datetime
import json
import pprint
import opentimelineio as otio
from opentimelineio.adapters import fcp_xml
from opentimelineio.adapters import cmx_3600
app = FastAPI()

app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")


# Hum global var, should be global to the route /clip/ should be in session ...
allClip = {}

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

def readfile(filename):
    with open(filename) as file:  
        data = file.read()
    return data 

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
    
    # use for route /clip.
    global allClip
    for clip in track.each_clip():
        allClip[currentIndex] = clip
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
                
                allClip[currentIndex] = clip

                dataMarker.append(
                    {
                        "id": currentIndex,
                        "idseq": indexSeq,
                        "startTime": getDateTime(clip.range_in_parent().start_time.to_seconds()+m.marked_range.start_time.to_seconds()),
                        "name" : "marker", #m.name
                        "color" : m.Color,
                    }
                )

        currentIndex = currentIndex + 1
    return currentIndex




# REST API...


@app.get("/openapi/")
async def getopenapi():
    return  get_openapi(
        title="OpentimelineIo OpenApi",
        version="0.0.1",
        description="This is OpenTimelineIO OpenAPI schema",
        routes=app.routes,
    )


@app.post("/convert_to_edl/")
async def create_fcpxml_from_otio(file: UploadFile = File(..., description="The file otio")):
    timeline = otio.adapters.read_from_file(file.filename)
    return  cmx_3600.write_to_string(timeline,rate=25,ignore_timecode_mismatch=True)


@app.post("/convert_to_fcp_xml/")
async def create_fcpxml_from_otio(file: UploadFile = File(..., description="The file otio")):
    timeline = otio.adapters.read_from_file(file.filename)
    return fcp_xml.write_to_string(timeline)

@app.post("/convert_to_otio/")
async def create_otio_from_file(file: UploadFile = File(..., description="The file to be converted otio")):
    timeline = otio.adapters.read_from_file(file.filename)
    # I Don't find the timeline to_json() ... ?
    return json.loads(timeline.to_json_string())

@app.get("/plugins")
async def getplugins(request: Request):
    plugin_types = otio.plugins.manifest.OTIO_PLUGIN_TYPES
    # load all the otio plugins
    active_plugin_manifest = otio.plugins.ActiveManifest()

    plugins = {}
    for pt in plugin_types:
        plugin_by_type = getattr(active_plugin_manifest, pt)
        plugins[pt] = []
        for p in plugin_by_type:
            # p is not json serialiable .... but can be convert in string 
             plugins[pt].append("%s" % (p)) 
        
    return plugins


# HTML INTERACTION.


@app.get("/clip/{clip_id}")
async def getclipinfo(request: Request,clip_id: int):
    global allClip

    if clip_id in allClip.keys():
        return allClip[clip_id].to_json_string()
    
    return "not found" 

@app.post("/submitfile")
async def submitfile(request: Request,file: UploadFile = File(..., description="For GUI visjs")):    
    jsonschema = readfile("static/otio.schema.json")
    
    timeline = otio.adapters.read_from_file(file.filename)

    jsonvalue =  timeline.to_json_string()
    
    # Data for jinja templating.
    dataForVisjs = {}
    dataMarker = []
    currentIndex = 1 # it's for the id in visjs
    indexSeq = 1 # it's for the group in visjs ( 1 is for loop.index jinja )
    #alldata = {}

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

    # Find markers in Track.
    for t in timeline.tracks:
        for mt in t.markers:
            indexSeq = indexSeq + 1
            dataMarker.append(
                    {
                        "id": currentIndex,
                        "startTime": getDateTime(mt.marked_range.start_time.to_seconds()),
                        "name" :  mt.name,
                        "color" : mt.Color(),
                    }
                )          
    pprint.pprint(dataMarker)
    return templates.TemplateResponse('index.html',{
                            "request":request,
                            "totalduration":totalduration,
                            "data":dataForVisjs,
                            "dataMarker": dataMarker,
                            "jsonschema":jsonschema,
                            "jsonvalue":jsonvalue,
                            "name":timeline.name
        })



@app.get("/")
async def home(request: Request):
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


    return templates.TemplateResponse('upload.html',{
                        "request":request,
                        "plugins":plugins,
                        "active_plugin_manifest":active_plugin_manifest,
            })

if __name__ == "__main__":
    uvicorn.run("testfastapi:app", host="127.0.0.1", port=5000, debug=True,log_level="info")
