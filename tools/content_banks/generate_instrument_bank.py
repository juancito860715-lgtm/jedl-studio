#!/usr/bin/env python3
"""Create original CC0 2D instrument illustrations for JEDL Studio."""
import hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path("app/src/main/assets/content/instruments/jedl_original_instruments_v1")
S=3
INK=(35,48,64,255); GOLD=(226,166,65,255); WOOD=(163,91,55,255)
LIGHT=(211,145,91,255); BLUE=(76,132,177,255); RED=(183,83,76,255)
CREAM=(247,239,218,255); METAL=(190,199,204,255); GREEN=(88,139,111,255)
def c(): 
    im=Image.new("RGBA",(384,384),(0,0,0,0)); return im,ImageDraw.Draw(im)
def q(v): return int(v*S)
def ln(d,pts,col=INK,w=4): d.line([(q(x),q(y)) for x,y in pts],fill=col,width=q(w),joint="curve")
def el(d,b,fill,outline=INK,w=3): d.ellipse(tuple(q(x) for x in b),fill=fill,outline=outline,width=q(w))
def rr(d,b,r,fill,outline=INK,w=3): d.rounded_rectangle(tuple(q(x) for x in b),radius=q(r),fill=fill,outline=outline,width=q(w))
def pg(d,pts,fill,outline=INK,w=3):
    p=[(q(x),q(y)) for x,y in pts]; d.polygon(p,fill=fill)
    if outline: d.line(p+[p[0]],fill=outline,width=q(w),joint="curve")
def timbales():
    im,d=c()
    for x,col in [(24,BLUE),(70,RED)]:
        rr(d,(x,43,x+35,84),7,col); el(d,(x,35,x+35,52),CREAM)
        ln(d,[(x+5,82),(x+2,106)],METAL,3); ln(d,[(x+30,82),(x+33,106)],METAL,3)
    ln(d,[(18,106),(112,106)],INK,3); ln(d,[(39,24),(56,39)],WOOD,3); ln(d,[(90,24),(73,39)],WOOD,3)
    return im
def conga():
    im,d=c(); pg(d,[(39,30),(88,30),(81,99),(46,99)],LIGHT); el(d,(39,23,88,40),CREAM)
    el(d,(46,90,81,105),WOOD); ln(d,[(47,45),(80,45)],WOOD,2); ln(d,[(46,62),(78,62)],WOOD,2)
    ln(d,[(50,99),(47,113)],METAL,3); ln(d,[(77,99),(81,113)],METAL,3); return im
def snare():
    im,d=c(); rr(d,(22,45,106,82),8,BLUE); el(d,(22,37,106,55),CREAM); el(d,(26,73,102,89),METAL)
    for x in (35,55,75,95): ln(d,[(x,85),(x,105)],METAL,2)
    ln(d,[(29,105),(99,105)],INK,3); return im
def kit():
    im,d=c(); rr(d,(43,59,91,98),9,RED); el(d,(43,52,91,68),CREAM)
    rr(d,(15,45,47,74),6,BLUE); el(d,(15,39,47,52),CREAM)
    rr(d,(83,43,113,71),6,GREEN); el(d,(83,37,113,50),CREAM)
    ln(d,[(25,22),(25,39)],METAL,3); el(d,(8,14,42,25),GOLD)
    ln(d,[(100,22),(100,36)],METAL,3); el(d,(84,14,116,25),GOLD)
    ln(d,[(54,97),(49,114)],METAL,3); ln(d,[(80,97),(85,114)],METAL,3); return im
def trumpet():
    im,d=c(); ln(d,[(17,64),(76,64),(88,54)],GOLD,8); pg(d,[(77,48),(111,32),(111,88),(77,75)],GOLD)
    el(d,(99,31,116,89),METAL); ln(d,[(15,56),(25,56)],METAL,3); ln(d,[(15,72),(25,72)],METAL,3)
    for x in (42,55,68): ln(d,[(x,56),(x,39)],METAL,3); rr(d,(x-5,32,x+5,42),3,RED)
    return im
def sax():
    im,d=c(); ln(d,[(47,22),(47,53),(58,68),(73,72),(83,62),(83,48)],GOLD,9)
    ln(d,[(47,22),(56,14)],METAL,4); pg(d,[(75,61),(100,58),(108,76),(86,91),(72,78)],GOLD)
    for x,y in [(45,35),(47,48),(55,59),(67,68),(78,65)]: el(d,(x-4,y-4,x+4,y+4),CREAM,w=2)
    ln(d,[(83,48),(94,39)],METAL,3); return im
def guitar():
    im,d=c(); pg(d,[(72,19),(85,23),(81,49),(75,59),(92,70),(94,87),(84,104),(65,108),(54,98),(52,84),(61,72),(65,59),(58,48),(61,25)],LIGHT)
    rr(d,(67,7,78,63),3,WOOD); rr(d,(64,5,81,17),3,METAL)
    el(d,(61,67,86,92),GOLD); el(d,(69,75,78,84),INK,w=1)
    for x in (68,71,74,77): ln(d,[(x,13),(x-2,101)],CREAM,1)
    ln(d,[(59,95),(88,95)],METAL,3); return im
def piano():
    im,d=c(); rr(d,(12,38,116,91),7,WOOD); rr(d,(18,46,110,82),2,CREAM,w=2)
    for x in range(22,109,11): ln(d,[(x,47),(x,81)],INK,1)
    for x in (29,40,62,73,84,95): rr(d,(x,46,x+6,66),1,INK,w=1)
    ln(d,[(22,96),(106,96)],METAL,3); ln(d,[(29,91),(29,105)],WOOD,4); ln(d,[(99,91),(99,105)],WOOD,4); return im
def marimba():
    im,d=c()
    for i,(x,col) in enumerate([(16,RED),(35,GOLD),(54,GREEN),(73,BLUE),(92,RED)]):
        rr(d,(x,34+(i%2)*5,x+17,50+(i%2)*5),4,col,w=2)
        pg(d,[(x+2,83),(x+15,83),(x+13,106),(x+4,106)],LIGHT,w=2)
    ln(d,[(12,111),(116,111)],INK,4); ln(d,[(21,22),(106,22)],GOLD,3); return im
def violin():
    im,d=c(); pg(d,[(60,18),(70,24),(67,39),(80,51),(88,65),(83,80),(70,87),(66,103),(57,110),(48,103),(45,87),(32,80),(27,65),(35,51),(48,39),(45,24)],LIGHT)
    rr(d,(56,6,72,50),3,WOOD); rr(d,(55,4,73,14),3,METAL)
    el(d,(53,56,62,65),GOLD,w=2); el(d,(67,56,76,65),GOLD,w=2)
    for x in (59,62,65,68): ln(d,[(x,11),(x+1,104)],CREAM,1)
    ln(d,[(20,105),(105,23)],METAL,3); return im
def flute():
    im,d=c(); ln(d,[(18,75),(111,35)],METAL,9); ln(d,[(18,75),(111,35)],CREAM,4)
    for x,y in [(39,65),(55,58),(71,51),(87,44)]: el(d,(x-3,y-3,x+3,y+3),GOLD,w=1)
    ln(d,[(16,80),(24,86)],INK,3); return im

def generate():
    ROOT.mkdir(parents=True,exist_ok=True); folder=ROOT/"png"/"Instruments"; folder.mkdir(parents=True,exist_ok=True)
    items=[("timbales","Timbales",timbales),("conga","Conga",conga),("snare-drum","Redoblante",snare),
      ("drum-kit","Batería",kit),("trumpet","Trompeta",trumpet),("saxophone","Saxofón",sax),
      ("guitar","Guitarra",guitar),("piano","Piano",piano),("marimba","Marimba",marimba),
      ("violin","Violín",violin),("flute","Flauta",flute)]
    entries=[]
    for ident,title,draw in items:
        path=folder/(ident+".png"); draw().resize((128,128),Image.Resampling.LANCZOS).save(path,optimize=True)
        raw=path.read_bytes(); entries.append({"id":ident,"title":title,"file":"png/Instruments/"+path.name,
          "sourceFile":"PNG/Instruments/"+path.name,"width":128,"height":128,
          "sha256":hashlib.sha256(raw).hexdigest(),"kind":"instrument-object","category":"Instruments"})
    source="https://github.com/juancito860715-lgtm/jedl-studio"
    manifest={"schemaVersion":1,"id":"jedl_original_instruments_v1","title":"Instrumentos JEDL originales",
      "publisher":"JEDL Studio","source":source,"license":"CC0-1.0",
      "licenseTerms":"https://creativecommons.org/publicdomain/zero/1.0/","commercialUse":True,
      "modificationAllowed":True,"apkRedistributionAllowed":True,"attributionRequired":False,
      "attributionNote":"Ilustraciones originales generadas para JEDL Studio.",
      "assetCount":len(entries),"assets":entries}
    (ROOT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (ROOT/"LICENSE.txt").write_text("CC0 1.0 Universal. Original JEDL Studio instrument illustrations.\nhttps://creativecommons.org/publicdomain/zero/1.0/\n",encoding="utf-8")
    (ROOT/"SOURCE.json").write_text(json.dumps({"publisher":"JEDL Studio","source":source,"license":"CC0-1.0"},indent=2)+"\n",encoding="utf-8")
    print("INSTRUMENT_BANK_OK assets=11 license=CC0-1.0")
    return entries
if __name__=="__main__": generate()
