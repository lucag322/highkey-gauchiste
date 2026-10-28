import cv2, numpy as np, subprocess, sys
src="/Users/luca.grousset/Movies/highkey-gauchiste/lot3/sources/C4-melenchon-intersyndicale.mp4"
def frame(t):
    p=subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",src,"-frames:v","1","-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True)
    return np.frombuffer(p.stdout,np.uint8).reshape(1080,1920,3).copy()
def micmask():
    m=np.zeros((1080,1920),np.uint8)
    cv2.ellipse(m,(1100,316),(31,38),0,0,360,255,-1)
    cv2.line(m,(1100,340),(1112,600),255,24); cv2.line(m,(1112,600),(1124,1080),255,28); cv2.line(m,(1112,600),(1162,1080),255,28)
    cv2.rectangle(m,(1098,522),(1164,558),255,-1)
    return m
out=[]
for t in [133,136,140,141.5]:
    f=frame(t); m=micmask(); r=cv2.inpaint(f,m,9,cv2.INPAINT_TELEA)
    out.append(np.hstack([f[150:750,850:1400],r[150:750,850:1400]]))
cv2.imwrite(sys.argv[1],np.vstack([np.hstack(out[:2]),np.hstack(out[2:])]))
