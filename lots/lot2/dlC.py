import subprocess,json,sys,os
from concurrent.futures import ThreadPoolExecutor
SRC='/Users/luca.grousset/Movies/highkey-gauchiste/lot2/sources'
PAD=0.5
# (fichier, id video, debut, fin)  temps source en secondes
J=[
 # C1 Guette
 ("C1-guette-bezons-citation","9Cgr6La_XaE",1017.0,1033.0),
 ("C1-guette-meaux-01","Cse3O99mlR0",36.6,41.4),
 ("C1-guette-meaux-02","Cse3O99mlR0",895.0,901.0),
 ("C1-guette-meaux-03","Cse3O99mlR0",43.0,48.0),
 ("C1-guette-meaux-04","Cse3O99mlR0",193.4,197.9),
 ("C1-guette-meaux-05","Cse3O99mlR0",369.0,375.0),
 ("C1-guette-meaux-06","Cse3O99mlR0",427.0,432.5),
 ("C1-guette-meaux-07","Cse3O99mlR0",1232.0,1238.0),
 ("C1-guette-meaux-08","Cse3O99mlR0",1132.0,1135.5),
 ("C1-guette-meaux-09","Cse3O99mlR0",697.0,702.5),
 ("C1-guette-meaux-10","Cse3O99mlR0",617.5,623.0),
 ("C1-guette-bezons-01","9Cgr6La_XaE",969.8,974.2),
 ("C1-guette-bezons-02","9Cgr6La_XaE",1066.5,1072.5),
 ("C1-guette-amfis-01","HW03wZDi6Tk",1528.0,1534.0),
 ("C1-guette-amfis-02","HW03wZDi6Tk",1693.0,1699.0),
 ("C1-guette-amfis-03","HW03wZDi6Tk",1683.0,1690.0),
 # C2 Coquerel
 ("C2-coquerel-stdenis-citation","JqMnuzxTXGI",179.0,195.0),
 ("C2-coquerel-stdenis-01","JqMnuzxTXGI",103.0,108.0),
 ("C2-coquerel-stdenis-02","JqMnuzxTXGI",62.8,67.8),
 ("C2-coquerel-stdenis-03","JqMnuzxTXGI",144.0,150.0),
 ("C2-coquerel-stdenis-04","JqMnuzxTXGI",72.0,76.0),
 ("C2-coquerel-stdenis-05","JqMnuzxTXGI",124.0,128.0),
 ("C2-coquerel-stdenis-06","JqMnuzxTXGI",36.0,41.0),
 ("C2-coquerel-stdenis-07","JqMnuzxTXGI",151.5,157.0),
 ("C2-coquerel-hemicycle-01","v6HH2QrtogU",140.0,145.0),
 ("C2-coquerel-hemicycle-02","v6HH2QrtogU",270.0,274.0),
 ("C2-coquerel-hemicycle-03","v6HH2QrtogU",514.0,519.2),
 ("C2-coquerel-hemicycle-04","v6HH2QrtogU",220.0,224.0),
 ("C2-coquerel-stouen-01","q5zM4ghkEqs",457.0,461.0),
 ("C2-coquerel-stouen-02","q5zM4ghkEqs",671.0,675.0),
 ("C2-coquerel-stouen-03","q5zM4ghkEqs",1042.0,1046.0),
 # C3 Melenchon
 ("C3-melenchon-convention-citation","Yc46p2zQZxY",1633.0,1653.5),
 ("C3-melenchon-convention-01","Yc46p2zQZxY",25.0,30.0),
 ("C3-melenchon-convention-02","Yc46p2zQZxY",118.0,124.0),
 ("C3-melenchon-convention-03","Yc46p2zQZxY",490.0,496.0),
 ("C3-melenchon-convention-04","Yc46p2zQZxY",181.0,187.0),
 ("C3-melenchon-convention-05","Yc46p2zQZxY",1009.0,1014.0),
 ("C3-melenchon-convention-06","Yc46p2zQZxY",1687.0,1691.0),
 ("C3-melenchon-convention-07","Yc46p2zQZxY",1697.0,1702.0),
 ("C3-melenchon-clermont-01","sBvVfHxcJp4",554.0,560.0),
 ("C3-melenchon-clermont-02","sBvVfHxcJp4",310.0,314.0),
 ("C3-melenchon-clermont-03","sBvVfHxcJp4",2219.0,2225.0),
 ("C3-melenchon-clermont-04","sBvVfHxcJp4",3188.0,3195.0),
 ("C3-melenchon-clermont-05","sBvVfHxcJp4",4304.0,4308.0),
 ("C3-melenchon-clermont-06","sBvVfHxcJp4",542.5,548.5),
 ("C3-melenchon-clermont-07","sBvVfHxcJp4",2607.0,2611.0),
]
def run(j):
    n,v,a,b=j
    out=f"{SRC}/{n}.mp4"
    if os.path.exists(out) and os.path.getsize(out)>10000: return n,0
    a2=max(0,a-PAD); b2=b+PAD
    r=subprocess.run(["yt-dlp","-f","bv*[height=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[height=1080]+ba/b[height=1080]","--merge-output-format","mp4",
      "--download-sections",f"*{a2}-{b2}","--force-keyframes-at-cuts","-o",out,f"https://www.youtube.com/watch?v={v}"],capture_output=True,text=True)
    return n,r.returncode
if __name__=="__main__":
    with ThreadPoolExecutor(4) as ex:
        for n,rc in ex.map(run,J): print(n,rc,flush=True)
