import random
import time
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def dist2(p1,p2):
    return (p1[0]-p2[0])**2+(p1[1]-p2[1])**2

def brute_force(points):
    n=len(points)
    if(n<2):
        return None
    best_d2=float("inf")
    best_pair=None
    for i in range(n):
        for j in range(i+1,n):
            d2=dist2(points[i],points[j])
            pair=tuple(sorted((points[i],points[j])))
            if(d2<best_d2 or (d2==best_d2 and (best_pair is None or pair<best_pair))):
                best_d2=d2
                best_pair=pair
    return math.sqrt(best_d2),best_pair

def div_n_conq(points):
    if(len(points)<2):
        return None,None

    ordered=sorted(points)

    for i in range(1,len(ordered)):
        if ordered[i]==ordered[i-1]:
            return (0.0,(ordered[i-1],ordered[i])),None

    px=sorted(points,key=lambda p:(p[0],p[1]))
    py=sorted(points,key=lambda p:(p[1],p[0]))
    mid=len(px)//2
    split_x=(px[mid-1][0]+px[mid][0])/2

    def solve(x_points,y_points):
        n=len(x_points)

        if(n<=3):
            best_d2=float("inf")
            best_pair=None

            for i in range(n):
                for j in range(i+1,n):
                    d2=dist2(x_points[i],x_points[j])
                    pair=tuple(sorted((x_points[i],x_points[j])))

                    if(d2<best_d2 or (d2==best_d2 and (best_pair is None or pair<best_pair))):
                        best_d2=d2
                        best_pair=pair

            return best_d2,best_pair

        mid=len(x_points)//2
        left_x=x_points[:mid]
        right_x=x_points[mid:]

        left_set=set(left_x)
        left_y=[p for p in y_points if p in left_set]
        right_y=[p for p in y_points if p not in left_set]

        left_best=solve(left_x,left_y)
        right_best=solve(right_x,right_y)

        if(left_best[0]<right_best[0] or (left_best[0]==right_best[0] and left_best[1]<=right_best[1])):
            best=left_best
        else:
            best=right_best

        d2=best[0]
        center=(left_x[-1][0]+right_x[0][0])/2
        strip=[p for p in y_points if (p[0]-center)**2<d2]

        for i in range(len(strip)):
            for j in range(i+1,min(i+8,len(strip))):
                if((strip[j][1]-strip[i][1])**2>=best[0]):
                    break

                pair=tuple(sorted((strip[i],strip[j])))
                candidate=(dist2(*pair),pair)

                if(candidate[0]<best[0] or (candidate[0]==best[0] and candidate[1]<best[1])):
                    best=candidate

        return best

    result=solve(px,py)
    distance=math.sqrt(result[0])

    left_result=solve(px[:mid],sorted(px[:mid],key=lambda p:(p[1],p[0])))
    right_result=solve(px[mid:],sorted(px[mid:],key=lambda p:(p[1],p[0])))

    strip_d=math.sqrt(min(left_result[0],right_result[0]))

    return (distance,result[1]),(split_x,strip_d)
def timed_call(function,*args):
    start=time.perf_counter()
    result=function(*args)
    elapsed=(time.perf_counter()-start)*1000
    return result,elapsed


def print_result(name,result):
    if(result is None):
        print(f"{name}: No pair exists because N<2")
        return

    distance,(p1,p2)=result
    print(f"{name}: {distance:.6f} ({p1[0]:.3f},{p1[1]:.3f}) ({p2[0]:.3f},{p2[1]:.3f})")


def visualize(points,brute,dc,metadata,sizes,brute_times,dc_times):
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(14,6))

    ax1.scatter([p[0] for p in points],[p[1] for p in points],color="gray",s=25,label="Input points")

    if(brute is not None):
        _,(p1,p2)=brute
        ax1.plot([p1[0],p2[0]],[p1[1],p2[1]],"r-o",label="Brute-force pair")

    if(dc is not None):
        _,(p1,p2)=dc
        ax1.plot([p1[0],p2[0]],[p1[1],p2[1]],"b--x",label="Divide-and-conquer pair")

    if(metadata is not None):
        split_x,d=metadata
        ax1.axvline(split_x,color="green",linestyle="-.",label="Dividing line")
        ax1.axvspan(split_x-d,split_x+d,color="green",alpha=0.15,label="Strip width 2d")

    ax1.set_title("Closest Pair of Points")
    ax1.set_xlabel("X coordinate")
    ax1.set_ylabel("Y coordinate")
    ax1.legend()
    ax1.grid(alpha=0.25)

    ax2.plot(sizes,brute_times,"r-o",label="Brute Force O(N^2)")
    ax2.plot(sizes,dc_times,"b-s",label="Divide and Conquer O(N log N)")
    ax2.set_title("Running Time vs Input Size")
    ax2.set_xlabel("Number of points (N)")
    ax2.set_ylabel("Execution time (ms)")
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

def animate_divide_conquer(points):
    if(len(points)<2):
        print("Animation requires at least 2 points.")
        return

    px=sorted(points,key=lambda p:(p[0],p[1]))
    frames=[]

    def record(x_points,stage,depth=0):
        frames.append((list(x_points),stage,depth))

    def solve(x_points):
        n=len(x_points)
        record(x_points,"Splitting",len(points)-n)

        if(n<=3):
            best=(float("inf"),None)

            for i in range(n):
                for j in range(i+1,n):
                    d2=dist2(x_points[i],x_points[j])
                    pair=tuple(sorted((x_points[i],x_points[j])))

                    if(d2<best[0]):
                        best=(d2,pair)

            record(x_points,"Base case",len(points)-n)
            return best

        mid=n//2
        left=x_points[:mid]
        right=x_points[mid:]

        left_best=solve(left)
        right_best=solve(right)

        best=min(left_best,right_best,key=lambda z:z[0])
        center=(left[-1][0]+right[0][0])/2
        d2=best[0]

        strip=[p for p in x_points if (p[0]-center)**2<d2]
        record(strip,"Checking middle strip",len(points)-n)

        strip=sorted(strip,key=lambda p:(p[1],p[0]))

        for i in range(len(strip)):
            for j in range(i+1,min(i+8,len(strip))):
                if((strip[j][1]-strip[i][1])**2>=best[0]):
                    break

                candidate=(dist2(strip[i],strip[j]),
                           tuple(sorted((strip[i],strip[j]))))

                if(candidate[0]<best[0]):
                    best=candidate

        record(list(best[1]),"Merging results",len(points)-n)
        return best

    duplicate=any(px[i]==px[i-1] for i in range(1,len(px)))

    if(duplicate):
        pair=next((px[i-1],px[i]) for i in range(1,len(px))
                  if px[i]==px[i-1])
        record(px,"Duplicate points: distance 0",0)
    else:
        solve(px)

    fig,ax=plt.subplots(figsize=(8,6))
    xs=[p[0] for p in points]
    ys=[p[1] for p in points]

    ax.scatter(xs,ys,color="gray",s=35)
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    ax.set_title("Divide-and-Conquer Animation")
    ax.grid(alpha=0.25)

    padding=10
    ax.set_xlim(min(xs)-padding,max(xs)+padding if max(xs)>min(xs) else max(xs)+padding)
    ax.set_ylim(min(ys)-padding,max(ys)+padding if max(ys)>min(ys) else max(ys)+padding)

    line,=ax.plot([],[],color="red",marker="o",linewidth=2)
    strip_scatter=ax.scatter([],[],color="orange",s=65)
    status=ax.text(0.02,0.98,"",transform=ax.transAxes,va="top")

    def update(frame_index):
        current,stage,depth=frames[frame_index]
        strip_scatter.set_offsets(current if current else [[float("nan"),float("nan")]])
        line.set_data([],[])

        if(stage=="Merging results" and len(current)==2):
            line.set_data([current[0][0],current[1][0]],
                          [current[0][1],current[1][1]])

        status.set_text(
            f"Step {frame_index+1}/{len(frames)}\n"
            f"Stage: {stage}\n"
            f"Recursive depth: {depth}"
        )
        return line,strip_scatter,status

    ani=animation.FuncAnimation(
        fig,update,frames=len(frames),interval=900,
        repeat=True,blit=False
    )

    plt.tight_layout()
    plt.show()

def main():
    try:
        n=int(input("Enter number of points N: "))
        if(n<0):
            print("N cannot be negative")
            return
    except ValueError:
        print("Enter a valid integer")
        return

    random.seed(42)
    points=[(random.randint(0,1000),random.randint(0,1000)) for _ in range(n)]

    brute_result,brute_ms=timed_call(brute_force,points)
    dc_output,dc_ms=timed_call(div_n_conq,points)

    dc_result,metadata=dc_output

    print_result("Brute Force",brute_result)
    print_result("Divide and Conquer",dc_result)

    print(f"Execution time (ms): Brute Force={brute_ms:.3f}, Divide and Conquer={dc_ms:.3f}")

    if(brute_result is not None and dc_result is not None):
        agrees=math.isclose(brute_result[0],dc_result[0],rel_tol=1e-9,abs_tol=1e-9)
        print("Minimum distances agree:",agrees)

        if(not agrees):
            print("WARNING: Results do not agree!")

    if(n>=2):
        sizes=[100,250,500,1000,1500]
        brute_times=[]
        dc_times=[]

        for size in sizes:
            sample=[(random.uniform(0,1000),random.uniform(0,1000)) for _ in range(size)]

            _,t1=timed_call(brute_force,sample)
            _,t2=timed_call(div_n_conq,sample)

            brute_times.append(t1)
            dc_times.append(t2)

        visualize(points,brute_result,dc_result,metadata,sizes,brute_times,dc_times)
        animate_divide_conquer(points)
    else:
        print("Plots skipped because N<2")
if __name__=="__main__":
    main() 