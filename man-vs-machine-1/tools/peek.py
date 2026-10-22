"""Debug helper: crop rows of a sheet to a scaled preview PNG."""
import sys, zlib, struct, json
from png import Image
def load(path):
    data=open(path,'rb').read(); pos=8; idat=b''; w=h=0
    while pos<len(data):
        ln=struct.unpack('>I',data[pos:pos+4])[0]; tag=data[pos+4:pos+8]; body=data[pos+8:pos+8+ln]
        if tag==b'IHDR': w,h=struct.unpack('>II',body[:8])
        if tag==b'IDAT': idat+=body
        pos+=12+ln
    raw=zlib.decompress(idat); img=Image(w,h); st=w*4+1
    prev=bytearray(w*4)
    for y in range(h):
        f=raw[y*st]; line=bytearray(raw[y*st+1:(y+1)*st])
        for i in range(len(line)):
            a=line[i-4] if i>=4 else 0; b=prev[i]; c=prev[i-4] if i>=4 else 0
            if f==1: line[i]=(line[i]+a)&255
            elif f==2: line[i]=(line[i]+b)&255
            elif f==3: line[i]=(line[i]+((a+b)>>1))&255
            elif f==4:
                p=a+b-c; pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
                pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c)
                line[i]=(line[i]+pr)&255
        prev=line
        for x in range(w):
            r,g,b_,a_=line[x*4:x*4+4]
            if a_: img.px[y*w+x]=(r,g,b_,a_)
    return img
if __name__=='__main__':
    cid=sys.argv[1]; r0=int(sys.argv[2]); r1=int(sys.argv[3]); s=int(sys.argv[4]) if len(sys.argv)>4 else 2
    meta=json.load(open(f'../assets/characters/{cid}/{cid}_anims.json'))
    img=load(f'../assets/characters/{cid}/{cid}_sheet.png')
    fh=meta['frame_h']
    c=img.crop(0,r0*fh,img.w,(r1-r0)*fh)
    bg=Image(c.w,c.h,(70,74,92,255)); bg.paste(c,0,0)
    for r in range(r1-r0):
        for x in range(0,c.w,3): bg.set(x,r*fh+meta['origin_y'],(90,200,90,255))
        for y in range(r*fh,(r+1)*fh): bg.set(0,y,(0,0,0,255))
    bg.scaled(s).save(f'preview/{cid}_{r0}_{r1}.png')
