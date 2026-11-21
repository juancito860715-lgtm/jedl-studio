#!/usr/bin/env python3
"""Generate original transparent CC0 wardrobe sprites for JEDL Studio scenes."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

SIZE=128
S=3
INK=(35,48,60,255)
CREAM=(247,239,218,255)
BLUE=(65,125,174,255)
RED=(193,75,74,255)
GOLD=(231,178,73,255)
PURPLE=(119,92,166,255)
WOOD=(156,91,55,255)

def make(name):
    im=Image.new("RGBA",(SIZE*S,SIZE*S),(0,0,0,0))
    d=ImageDraw.Draw(im)
    def q(v): return int(v*S)
    def rr(b,fill,r=5,outline=INK,w=3):
        d.rounded_rectangle(tuple(q(v) for v in b),radius=q(r),fill=fill,outline=outline,width=q(w))
    def el(b,fill,outline=INK,w=3):
        d.ellipse(tuple(q(v) for v in b),fill=fill,outline=outline,width=q(w))
    def pg(points,fill,outline=INK,w=3):
        p=[(q(x),q(y)) for x,y in points]; d.polygon(p,fill=fill)
        if outline: d.line(p+[p[0]],fill=outline,width=q(w),joint="curve")
    def ln(points,fill=INK,w=2):
        d.line([(q(x),q(y)) for x,y in points],fill=fill,width=q(w),joint="curve")
    d.ellipse(tuple(q(v) for v in (15,105,113,119)),fill=(25,35,45,22))
    if name=="cap":
        el((25,24,102,91),BLUE)
        pg([(27,67),(103,67),(117,83),(61,91)],RED)
        ln([(44,39),(81,39)],CREAM,2)
    elif name=="tshirt":
        pg([(40,22),(53,16),(76,16),(89,22),(116,47),(99,63),(88,53),(88,103),(40,103),(40,53),(29,63),(12,47)],BLUE)
        ln([(53,18),(58,32),(71,32),(76,18)],CREAM,2)
    elif name=="hoodie":
        pg([(40,32),(51,23),(77,23),(88,32),(112,49),(97,69),(88,60),(88,104),(40,104),(40,60),(31,69),(16,49)],PURPLE)
        el((48,12,80,51),(145,122,184,255))
        ln([(64,48),(64,96)],CREAM,2)
        rr((48,74,59,84),GOLD,2,w=1); rr((69,74,80,84),GOLD,2,w=1)
    elif name=="jacket":
        pg([(40,22),(53,16),(76,16),(89,22),(112,48),(96,65),(88,55),(88,104),(40,104),(40,55),(32,65),(16,48)],RED)
        pg([(53,18),(64,43),(76,18),(80,32),(64,49),(48,32)],CREAM,w=2)
        ln([(64,48),(64,101)],GOLD,2)
        el((50,60,56,66),GOLD,w=1); el((72,60,78,66),GOLD,w=1)
    elif name=="jeans":
        pg([(36,18),(92,18),(87,61),(101,105),(70,105),(64,63),(58,105),(27,105),(41,61)],BLUE)
        ln([(64,22),(64,60)],CREAM,2)
        ln([(45,64),(58,64)],CREAM,1); ln([(70,64),(83,64)],CREAM,1)
    elif name=="sneakers":
        pg([(17,67),(45,67),(59,82),(91,85),(112,97),(110,108),(16,108),(10,96)],CREAM)
        pg([(12,96),(111,96),(111,108),(14,108)],RED,w=2)
        ln([(49,74),(65,87),(88,87)],BLUE,3)
        for x in (52,60,68): ln([(x,77),(x+8,84)],INK,1)
    else:
        raise ValueError(name)
    return im.resize((SIZE,SIZE),Image.Resampling.LANCZOS)

ITEMS=[
    ("cap","Gorra"),("tshirt","Camiseta"),("hoodie","Sudadera"),
    ("jacket","Chaqueta"),("jeans","Pantalones"),("sneakers","Zapatillas")
]

def build(output:Path):
    output=Path(output); folder=output/"png"/"Clothing"; folder.mkdir(parents=True,exist_ok=True)
    assets=[]
    for slug,title in ITEMS:
        path=folder/(slug+".png"); make(slug).save(path,format="PNG",optimize=True)
        raw=path.read_bytes()
        assets.append({"id":slug,"title":title,"file":"png/Clothing/"+path.name,
          "sourceFile":"PNG/Clothing/"+path.name,"category":"Clothing",
          "width":SIZE,"height":SIZE,"sha256":hashlib.sha256(raw).hexdigest(),"kind":"clothing-object"})
    source="https://github.com/juancito860715-lgtm/jedl-studio"
    manifest={"schemaVersion":1,"id":"jedl_original_clothing_v1","title":"Vestuario JEDL original",
      "publisher":"JEDL Studio","source":source,"license":"CC0-1.0",
      "licenseTerms":"https://creativecommons.org/publicdomain/zero/1.0/",
      "commercialUse":True,"modificationAllowed":True,"apkRedistributionAllowed":True,
      "attributionRequired":False,"assetCount":len(assets),"assets":assets}
    output.mkdir(parents=True,exist_ok=True)
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (output/"LICENSE.txt").write_text("Original JEDL Studio wardrobe illustrations. CC0-1.0.\nhttps://creativecommons.org/publicdomain/zero/1.0/\n",encoding="utf-8")
    (output/"SOURCE.json").write_text(json.dumps({"source":source,"license":"CC0-1.0","generator":"tools/content_banks/generate_clothing_bank.py"},indent=2)+"\n",encoding="utf-8")
    print("CLOTHING_BANK_OK assets=" + str(len(assets)) + " license=CC0-1.0")
    return manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="app/src/main/assets/content/clothing/jedl_original_clothing_v1")
    args=parser.parse_args()
    build(Path(args.out))

if __name__=="__main__": main()
