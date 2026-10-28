import sys, subprocess, numpy as np, cv2
sys.path.insert(0, "/Users/luca.grousset/Movies/highkey-gauchiste/_claude/outils")
from decoupe import masques
S="/Users/luca.grousset/Movies/highkey-gauchiste/lot3/sources/C4-melenchon-stdenis-%s.mp4"
box=(200,0,1920,820); tiles=[]
for f_, t in [("05",2.0),("01",3.5),("06",8.0),("02",7.4),("03",26.6),("06",12.4),("01",6.8)]:
    p=subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",S%f_,"-frames:v","1","-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True)
    fr=np.frombuffer(p.stdout,np.uint8).reshape(1080,1920,3).copy()
    m=masques([fr],box,(0.45,0.75),"cache/dec/inp_%s_%.1f"%(f_,t))[0]
    b=(m>0.5).astype(np.uint8)
    cl=cv2.morphologyEx(b,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(91,91)))
    inv=(1-cl).copy(); h,w=cl.shape; ff=np.zeros((h+2,w+2),np.uint8)
    for sx in range(0,w,20): cv2.floodFill(inv,ff,(sx,0),2)
    R=((inv!=2)|(cl>0)).astype(np.uint8)
    # bas : le buste continue jusqu'au bas du box sous le pupitre
    mic=(R>0)&(b==0)
    ys=np.where(b.any(1))[0]; head=ys[0]
    mic[:head+150]=False
    mic=cv2.dilate(mic.astype(np.uint8),np.ones((9,9),np.uint8))
    crop=fr[box[1]:box[3],box[0]:box[2]].copy()
    inp=cv2.inpaint(crop,mic,15,cv2.INPAINT_TELEA)
    mm=np.maximum(m,mic.astype(np.float32)*(R>0))
    mag=np.array([200,30,200],np.float32)
    out=(inp*mm[...,None]+mag*(1-mm[...,None])).astype(np.uint8)
    orig=(crop*m[...,None]+mag*(1-m[...,None])).astype(np.uint8)
    tiles.append(np.vstack([cv2.resize(orig,(430,205)),cv2.resize(out,(430,205))]))
cv2.imwrite("cache/inp2.jpg",np.hstack(tiles))
