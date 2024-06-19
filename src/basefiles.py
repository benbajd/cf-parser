'''Creates the base .cpp files.'''

MAIN_CPP: str = """\
#include <bits/stdc++.h>

using namespace std;
typedef long long ll;

int main() {
    ios::sync_with_stdio(0);
    cin.tie(0);
    
    return 0;
}
"""

CHECKER_CPP: str = """\
#include <bits/stdc++.h>

using namespace std;
typedef long long ll;

/*
CHECKER:
* input: input, user output, and expected output (optional), joined with "---"
* verdict: call checker_ac() if the user output is accepted
           or checker_wa() with the wrong answer reason otherwise
* output: do not output anything else
*/

void checker_ac() {
    exit(0);
}

void checker_wa(string message) {
    cout << (message != "" ? message : "checker returned wa");
    exit(0);
}

void assert_io_delim() {
    string delim;
    cin >> delim;
    assert(delim == "---");
}

int main() {
    ios::sync_with_stdio(0);
    cin.tie(0);
    // read input
    
    assert_io_delim();
    // read user output
    
    assert_io_delim();
    // read expected output (optional)
    
    return 1;  // checker_ac() should be called before this line
}
"""

BRUTEFORCE_CPP: str = """\
#include <bits/stdc++.h>

using namespace std;
typedef long long ll;

/*
BRUTEFORCE:
* input: random input
* output: the correct output
*/

int main() {
    ios::sync_with_stdio(0);
    cin.tie(0);
    
    return 0;
}
"""

GENERATOR_CPP: str = """\
#include <bits/stdc++.h>

using namespace std;
typedef long long ll;

/*
GENERATOR:
* output: a random input
*/

mt19937 gen(chrono::steady_clock::now().time_since_epoch().count());

int randint(int l, int r) {
    // get a random int in [l, r]
    return uniform_int_distribution<int>(l, r)(gen);
}

void randshuffle(auto &a) {
    // randomly shuffles a
    shuffle(a.begin(), a.end(), gen);
}

int main() {
    ios::sync_with_stdio(0);
    cin.tie(0);
    
    return 0;
}
"""
