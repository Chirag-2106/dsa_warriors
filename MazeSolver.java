import java.io.*;
import java.nio.file.*;
import java.util.*;


public class MazeSolver {
    static final int MAX_KEYS = 6;
    static final int[] DR = {-1, 1, 0, 0};
    static final int[] DC = {0, 0, -1, 1};
    static final String[] DIR = {"UP", "DOWN", "LEFT", "RIGHT"};

    static class State {
        int r, c, mask, dist;
        State prev;
        State(int r, int c, int mask, int dist, State prev) {
            this.r=r; this.c=c; this.mask=mask; this.dist=dist; this.prev=prev;
        }
    }
    static class Result {
        int distance;
        List<int[]> path;
        int finalMask;
        Result(int d, List<int[]> p, int m) { distance=d; path=p; finalMask=m; }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 0 || args[0].equalsIgnoreCase("help")) {
            usage(); return;
        }
        String mode = args[0].toLowerCase(Locale.ROOT);
        char[][] grid;
        if (mode.equals("solve")) {
            if (args.length < 2) { usage(); return; }
            grid = readCsv(Paths.get(args[1]));
        } else if (mode.equals("generate")) {
            if (args.length < 4) { usage(); return; }
            int n = Integer.parseInt(args[1]), t = Integer.parseInt(args[2]);
            long seed = args.length >= 5 ? Long.parseLong(args[4]) : System.nanoTime();
            grid = generateSolvable(n, t, seed);
            writeCsv(grid, Paths.get(args[3]));
            System.out.println("Generated maze: " + args[3] + " (seed=" + seed + ")");
        } else { usage(); return; }

        validate(grid);
        Result result = bfs(grid);
        if (result == null) {
            System.out.println("Shortest path length: -1 (no path)");
            return;
        }
        System.out.println("Shortest path length: " + result.distance);
        System.out.println("Path coordinates (row,column; zero-based):");
        for (int[] p : result.path) System.out.printf("(%d,%d)%n", p[0], p[1]);
        char[][] marked = copy(grid);
        for (int i=1; i<result.path.size()-1; i++) {
            int r=result.path.get(i)[0], c=result.path.get(i)[1];
            if (marked[r][c]=='.') marked[r][c]='x';
        }
        Path out = Paths.get("solution.csv");
        writeCsv(marked, out);
        System.out.println("Path exported to " + out.toAbsolutePath());
        System.out.println("Original key/door symbols are preserved in solution.csv.");
    }

    static void usage() {
        System.out.println("Usage:\n  java MazeSolver solve maze.csv\n  java MazeSolver generate <size>=5+ <T>=1..6 <output.csv> [seed]");
    }

    static char[][] readCsv(Path file) throws IOException {
        List<char[]> rows = new ArrayList<>();
        for (String line : Files.readAllLines(file)) {
            if (line.trim().isEmpty()) continue;
            String[] cells = line.split(",", -1);
            char[] row = new char[cells.length];
            for (int i=0; i<cells.length; i++) {
                String s=cells[i].trim();
                if (s.length()!=1) throw new IllegalArgumentException("Each CSV cell must contain exactly one character: " + s);
                row[i]=s.charAt(0);
            }
            rows.add(row);
        }
        if (rows.isEmpty()) throw new IllegalArgumentException("CSV maze is empty.");
        int n=rows.get(0).length;
        if (rows.size()!=n) throw new IllegalArgumentException("Maze must be square (N x N).");
        for (char[] row: rows) if (row.length!=n) throw new IllegalArgumentException("All CSV rows must have N cells.");
        return rows.toArray(new char[0][]);
    }

    static void writeCsv(char[][] grid, Path file) throws IOException {
        List<String> lines = new ArrayList<>();
        for (char[] row: grid) {
            StringJoiner sj = new StringJoiner(",");
            for (char ch: row) sj.add(String.valueOf(ch));
            lines.add(sj.toString());
        }
        Files.write(file, lines);
    }

    static void validate(char[][] g) {
        int n=g.length; if (n==0) throw new IllegalArgumentException("Empty maze.");
        int starts=0, exits=0; boolean[] keys=new boolean[MAX_KEYS], doors=new boolean[MAX_KEYS];
        for (char[] row:g) if (row.length!=n) throw new IllegalArgumentException("Maze must be square.");
        for (char[] row:g) for (char ch:row) {
            if (ch=='S') starts++;
            else if (ch=='E') exits++;
            else if (ch=='.' || ch=='#' || ch=='x') { }
            else if (ch>='a' && ch<='f') keys[ch-'a']=true;
            else if (ch>='A' && ch<='F') doors[ch-'A']=true;
            else throw new IllegalArgumentException("Invalid cell symbol: " + ch);
        }
        if (starts!=1 || exits!=1) throw new IllegalArgumentException("Maze must contain exactly one S and one E.");
        for(int i=0;i<MAX_KEYS;i++) if(keys[i]!=doors[i]) throw new IllegalArgumentException("Key/door type mismatch for " + (char)('a'+i) + ".");
    }

    static Result bfs(char[][] g) {
        int n=g.length, allMasks=1<<MAX_KEYS;
        boolean[][][] seen=new boolean[n][n][allMasks];
        State[][][] states=new State[n][n][allMasks];
        int sr=-1,sc=-1;
        for(int r=0;r<n;r++) for(int c=0;c<n;c++) if(g[r][c]=='S'){sr=r;sc=c;}
        State start=new State(sr,sc,0,0,null);
        ArrayDeque<State> q=new ArrayDeque<>(); q.add(start); seen[sr][sc][0]=true; states[sr][sc][0]=start;
        State goal=null;
        while(!q.isEmpty()) {
            State cur=q.remove();
            if(g[cur.r][cur.c]=='E'){goal=cur;break;}
            for(int k=0;k<4;k++) {
                int nr=cur.r+DR[k], nc=cur.c+DC[k];
                if(nr<0||nr>=n||nc<0||nc>=n||g[nr][nc]=='#') continue;
                char cell=g[nr][nc]; int mask=cur.mask;
                if(cell>='A'&&cell<='F'&&cell!='E'&&(mask&(1<<(cell-'A')))==0) continue;
                if(cell>='a'&&cell<='f') mask|=1<<(cell-'a');
                if(!seen[nr][nc][mask]) {
                    State next=new State(nr,nc,mask,cur.dist+1,cur);
                    seen[nr][nc][mask]=true; states[nr][nc][mask]=next; q.add(next);
                }
            }
        }
        if(goal==null) return null;
        List<int[]> path=new ArrayList<>();
        for(State s=goal;s!=null;s=s.prev) path.add(new int[]{s.r,s.c});
        Collections.reverse(path);
        return new Result(goal.dist,path,goal.mask);
    }

    static char[][] generateSolvable(int n, int t, long seed) {
        if(n<5) throw new IllegalArgumentException("Maze size must be at least 5.");
        if(t<1||t>6||2*t+2>n*n) throw new IllegalArgumentException("T must be 1..6 and fit in the maze.");
        Random random=new Random(seed); char[][] g=new char[n][n];
        for(char[] row:g) Arrays.fill(row,'.');
        // Add walls randomly while preserving a guaranteed route along the top and right edges.
        for(int r=1;r<n-1;r++) for(int c=0;c<n;c++) if(random.nextDouble()<0.23) g[r][c]='#';
        for(int c=0;c<n;c++) g[0][c]='.';
        for(int r=0;r<n;r++) g[r][n-1]='.';
        g[0][0]='S'; g[n-1][n-1]='E';
        // Put each key and matching door on the guaranteed route in key-before-door order.
        List<int[]> route=new ArrayList<>();
        for(int c=0;c<n;c++) route.add(new int[]{0,c});
        for(int r=1;r<n;r++) route.add(new int[]{r,n-1});
        int slots=route.size()-2;
        if(2*t>slots) throw new IllegalArgumentException("Maze too small for this many key/door pairs on guaranteed route.");
        List<Integer> positions=new ArrayList<>(); for(int i=1;i<route.size()-1;i++) positions.add(i);
        // Place ordered key/door pairs at increasing positions, ensuring every key precedes its door.
        int previous=0;
        for(int i=0;i<t;i++) {
            int remainingPairs=t-i;
            int maxKeyPos=route.size()-2-(2*remainingPairs-1);
            int keyPos=previous+1+random.nextInt(Math.max(1,maxKeyPos-previous));
            int doorPos=keyPos+1;
            int[] kp=route.get(keyPos), dp=route.get(doorPos);
            g[kp[0]][kp[1]]=(char)('a'+i); g[dp[0]][dp[1]]=(char)('A'+i);
            previous=doorPos;
        }
        return g;
    }
    static char[][] copy(char[][] g) { char[][] x=new char[g.length][]; for(int i=0;i<g.length;i++) x[i]=g[i].clone(); return x; }
}