# Python port of the director's composition maths; checks signs in hand-made scenes.
import math
def d(a): return (math.cos(a), math.sin(a))
def dot(a,b): return a[0]*b[0]+a[1]*b[1]
def rot(v,a):  # LSL: v * llEuler2Rot(<0,0,a>) = CCW rotation by a
    c,s=math.cos(a),math.sin(a); return (v[0]*c-v[1]*s, v[0]*s+v[1]*c)
def norm(v): m=math.hypot(*v); return (v[0]/m,v[1]/m)
tanV=math.tan(1.047198/2); tanH=tanV*1.778; alpha=math.atan2(tanH/3,1)
def screen_x(cam, view, p):   # +1 right edge, -1 left edge (SL: +y is left of +x)
    to=(p[0]-cam[0],p[1]-cam[1]); right=(view[1],-view[0])
    return dot(to,right)/dot(to,view)/tanH
ok=True
# 1) portrait with lead room, all angles and facings
for oy_deg in range(0,360,30):
    oy=math.radians(oy_deg); F=d(oy)
    for phi in [45,-45,135,-135,180,0]:
        az=oy+math.radians(phi); D=3.0
        cam=(D*math.cos(az),D*math.sin(az)); V=(-math.cos(az),-math.sin(az))
        fs=dot(F,(V[1],-V[0])); sd=1.0
        if fs>0.2: sd=1.0
        elif fs<-0.2: sd=-1.0
        V2=rot(V,-sd*alpha); x=screen_x(cam,V2,(0,0))
        facing_right = fs>0.2; facing_left = fs<-0.2
        if facing_right and not x<-0.2: ok=False; print('lead room wrong',oy_deg,phi,x)
        if facing_left and not x>0.2: ok=False; print('lead room wrong',oy_deg,phi,x)
        if abs(abs(x)-1/3)>0.02 : ok=False; print('not on a third',oy_deg,phi,x)
# 2) over-the-shoulder: camera behind owner (shot) / behind partner (reverse), same side of the axis
owner=(0,0); partner=(2,0); A=norm((2,0)); N=(-A[1],A[0])
for side in (1,-1):
    for rev in (0,1):
        dc=(N[0]*side*0.819152+(1 if rev else -1)*A[0]*0.573576, N[1]*side*0.819152+(1 if rev else -1)*A[1]*0.573576)
        dc=norm(dc); C=((owner[0]*1.5+partner[0])/2.5,(owner[1]*1.5+partner[1])/2.5); cam=(C[0]+dc[0]*3,C[1]+dc[1]*3)
        behind = cam[0]<owner[0] if not rev else cam[0]>partner[0]
        sameside = (cam[1]-0)*side>0
        if not (behind and sameside): ok=False; print('OTS wrong',side,rev,cam)
# 3) group: camera on the side the owner faces, square to the long axis
M=[(0,0),(3,0),(1.5,0.5)]; oyg=math.radians(80)
C=(sum(p[0] for p in M)/3,sum(p[1] for p in M)/3); A=(1,0); Nn=(0,1)
if dot(d(oyg),Nn)<0: Nn=(-Nn[0],-Nn[1])
if Nn!=(0,1): ok=False; print('group side wrong')
# 4) camera height puts eyes on the upper third with a level camera
for D in (2.5,3.0,8.0):
    camz=1.7-D*tanV/3; y=(1.7-camz)/D/tanV
    if abs(y-1/3)>1e-6: ok=False; print('thirds height wrong',D,y)
# 5) speaker shots (chat cuts): the speaker AND the other person are in frame, camera behind the right shoulder
for side in (1,-1):
    for rev,spk,oth in ((0,(2,0),(0,0)),(1,(0,0),(2,0))):   # rev=0: camera behind owner at (0,0), partner speaks; rev=1: owner speaks
        dc=(N[0]*side*0.819152+(1 if rev else -1)*A[0]*0.573576, N[1]*side*0.819152+(1 if rev else -1)*A[1]*0.573576); dc=norm(dc)
        C=((0*1.5+2)/2.5,0.0); cam=(C[0]+dc[0]*3,C[1]+dc[1]*3); view=norm((C[0]-cam[0],C[1]-cam[1]))
        for who,p in (('speaker',spk),('other',oth)):
            if abs(screen_x(cam,view,p))>1.0: ok=False; print('speaker shot: not in frame',who,side,rev)
print('geometry checks:', 'ALL PASS' if ok else 'FAILURES')
