# Python port of scenery.lsl findShot() run against simple test worlds
# (flat ground + boxes). Checks: camera inside the region, above the top surface at
# its spot (never inside a box), view ray unblocked, pitch in range, owner indoors ->
# camera above the roof.
import math, random
def ray(world, a, b):
    # world: ground z, list of boxes (xmin,ymin,zmin,xmax,ymax,zmax). returns (st, dist)
    ground, boxes = world
    dx,dy,dz=[b[i]-a[i] for i in range(3)]; L=math.sqrt(dx*dx+dy*dy+dz*dz)
    best=None
    if dz<0 and a[2]>ground:
        t=(ground-a[2])/dz
        if 0<=t<=1: best=t
    for bx in boxes:
        tmin,tmax=0.0,1.0; ok=True
        for i,(lo,hi) in enumerate([(bx[0],bx[3]),(bx[1],bx[4]),(bx[2],bx[5])]):
            d=[dx,dy,dz][i]; o=a[i]
            if abs(d)<1e-9:
                if o<lo or o>hi: ok=False;break
            else:
                t1,t2=(lo-o)/d,(hi-o)/d
                if t1>t2: t1,t2=t2,t1
                tmin=max(tmin,t1); tmax=min(tmax,t2)
                if tmin>tmax: ok=False;break
        if ok and tmin>0 and (best is None or tmin<best): best=tmin
    return (0,L) if best is None else (1,best*L)
def inside(world,p):
    return any(b[0]<p[0]<b[3] and b[1]<p[1]<b[4] and b[2]<p[2]<b[5] for b in world[1]) or p[2]<world[0]
def surface(world,x,y,ztop,zbot):
    st,d=ray(world,(x,y,ztop),(x,y,zbot)); return ztop-d if st==1 else zbot
def clampf(v,lo,hi): return max(lo,min(hi,v))
def novelty(az,last):
    if not last: return 1.0
    m=math.pi
    for l in last:
        d=(az-l+math.pi)%(2*math.pi)-math.pi; m=min(m,abs(d))
    return clampf(m/(math.pi/2),0,1)
def findShot(world,OP,reach,last,lasttype,minD,clearMin,water=0.0):
    covered = ray(world,(OP[0],OP[1],OP[2]+1),(OP[0],OP[1],OP[2]+41))[0]==1
    topZ = surface(world,OP[0],OP[1],OP[2]+80,OP[2]-5)
    best=None;bs=-1e9;base=random.uniform(0,2*math.pi)
    for i in range(10):
        az=base+i*0.628319; nov=novelty(az,last)
        if nov<0.44: continue
        d=minD+random.uniform(0,max(0,reach-minD))
        c=[OP[0]+math.cos(az)*d, OP[1]+math.sin(az)*d, 0]
        c[0]=clampf(c[0],3,253); c[1]=clampf(c[1],3,253)
        fl=math.hypot(c[0]-OP[0],c[1]-OP[1])
        if fl<minD*0.75: continue
        sZ=surface(world,c[0],c[1],max(OP[2],topZ)+80,OP[2]-40)
        if sZ<=OP[2]-39.9: sZ=OP[2]-1
        sZ=max(sZ,water)
        if random.random()<0.6: typ=5;h=random.uniform(10,30)
        else: typ=6;h=random.uniform(2.5,4)
        c[2]=sZ+h
        if covered and c[2]<topZ+5: c[2]=topZ+5
        pitch=0.0349; need=clearMin
        if typ==5:
            T=(OP[0]+random.uniform(-15,15),OP[1]+random.uniform(-15,15),OP[2]-1)
            hv=(T[0]-c[0],T[1]-c[1]); hl=math.hypot(*hv)
            if hl<1: hv=(OP[0]-c[0],OP[1]-c[1]); hl=math.hypot(*hv)
            pitch=clampf(math.atan2(c[2]-T[2],hl),0.1745,0.6981)
            u=(hv[0]/hl,hv[1]/hl); foc=(c[0]+u[0]*30,c[1]+u[1]*30,c[2]-30*math.tan(pitch))
            need=clampf(0.8*math.dist(c,T),8,clearMin)
        else:
            va=az+math.pi+random.uniform(-1,1)*1.047198
            foc=(c[0]+math.cos(va)*30,c[1]+math.sin(va)*30,c[2]-30*math.tan(pitch))
        v=[foc[k]-c[k] for k in range(3)]; vl=math.sqrt(sum(x*x for x in v)); v=[x/vl for x in v]
        st,clear=ray(world,tuple(c),tuple(c[k]+v[k]*60 for k in range(3)))
        if clear>=need:
            s=3*clear/60+2*nov+random.uniform(0,0.5)+(1 if typ!=lasttype else 0)+(0.5 if pitch<=0.4363 else 0)
            if s>bs: bs=s; best=(tuple(c),foc,typ,az,pitch,clear,need,covered,topZ)
    return best
random.seed(7)
worlds={
 'open field':        ((20.0,[]), (128,128,21.0)),
 'near region edge':  ((20.0,[]), (8,10,21.0)),
 'inside a house':    ((20.0,[(120,120,20,136,136,20.3),(120,120,20,136,120.3,28),(120,135.7,20,136,136,28),(120,120,20,120.3,136,28),(135.7,120,20,136,136,28),(120,120,27.7,136,136,28)]), (128,128,21.0)),
 'town of tall blocks':((20.0,[(100+i*20,100+j*20,20,110+i*20,110+j*20,20+random.uniform(8,40)) for i in range(4) for j in range(4) if not (i==1 and j==1)]), (128,128,21.0)),
 'skybox at 3000 m':  ((20.0,[(110,110,2999,146,146,3000)]), (128,128,3001.0)),
}
allok=True
for name,(world,OP) in [(n+(' @150' if R==150 else ''),v) for R in (100,150) for n,v in worlds.items()]:
    REACH=150 if name.endswith(' @150') else 100
    last=[];lt=-1;cuts=0;fails=0
    for k in range(40):
        s=findShot(world,OP,REACH,last,lt,20,25)
        if s is None: s=findShot(world,OP,REACH,last,lt,15,12)
        if s is None: fails+=1; last=[]; continue
        c,foc,typ,az,pitch,clear,need,covered,topZ=s; cuts+=1
        problems=[]
        if not (3<=c[0]<=253 and 3<=c[1]<=253): problems.append('outside region')
        if inside(world,c): problems.append('camera inside geometry')
        if clear<need: problems.append('view blocked')
        if not (0.03<=pitch<=0.70): problems.append('pitch')
        if covered and c[2]<topZ+5-1e-6: problems.append('not above roof')
        if problems: allok=False; print(name,problems,c)
        last=[az]+last[:1]; lt=typ
    print(f'{name:22s} shots {cuts:2d}/40, no-shot {fails:2d}')
print('scenery checks:', 'ALL PASS' if allok else 'FAILURES')
