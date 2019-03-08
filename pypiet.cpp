import <vector.h>


vector<int> d;

void psh(int x) {
    d.push_back(x);
}
int pop(int &x) {
    if (d.size()) {
        x = d.pop_back();
        return 1;
    }
    return 0;
}
int pop(int &x, int &y) {
    if (d.size() > 1) {
        x = d.pop_back();
        y = d.pop_back();
        return 1;
    }
    return 0;
}
void rll(int n, int k) {
    if (n > d.size() || n == 0 || k<1) {
        return;
    } else if ( n > 0 ){
        n = n%k;
        vector<int> z(d.begin(), d.begin+k);
        fill... d->d
        fill... z->d
    } else {
        n = n%k;
        vector<int> z(...);
        fill... d->d
        fill... z->d
    }
}





int main() {
    int t=0,i=0,a,b;
    char A;

    goto c_0_0_NOP;
%%%DEFN%%%
}

