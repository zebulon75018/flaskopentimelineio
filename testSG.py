import click
import json
import os
import shotgun_api3 
import pprint
import opentimelineio as otio
from opentimelineio.adapters import cmx_3600



SERVER_PATH ="https://xxxxxx.shotgunstudio.com"
SCRIPT_NAME = 'XXXX'
SCRIPT_KEY = "XXXX"

PROJECT_ID =  85
sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)

filterscut =[ ['project', 'is', {'type': 'Project', 'id': PROJECT_ID}],['id','is',3] ]

cut = sg.find_one("Cut",filterscut,["code","sg_cut_type","fps","duration","id"])

filters =[ ['project', 'is', {'type': 'Project', 'id': PROJECT_ID}],['cut', 'is', {'type': 'Cut', 'id':3}]]
fields=["code","entity","id","edit_in","edit_out","cut_item_duration"]

result = sg.find("CutItem",filters,fields,order= [{'field_name':'cut_order', 'direction':'asc'}])

tl = otio.schema.Timeline(metadata = { "id" : cut["id"] })
tl.name=cut["code"]
t = otio.schema.Track()
t.name = "track"
tl.tracks.append( t )

for c in result:

    mr = otio.schema.ExternalReference(
        available_range=otio.opentime.range_from_start_end_time(
        otio.opentime.RationalTime(c["edit_in"], cut["fps"]),
        otio.opentime.RationalTime(c["edit_out"],  cut["fps"])
        ),
        target_url="/var/tmp/test.mov"
    )
    rt = otio.opentime.RationalTime(c["cut_item_duration"],  cut["fps"])

    cl = otio.schema.Clip(
            name=c["code"],
            #media_reference=mr,
            source_range=otio.opentime.TimeRange(duration=rt),
            metadata = { "id" : c["id"] }
        )
    tl.tracks[0].append(cl)

print(tl.to_json_string())
#pprint.pprint(tl)