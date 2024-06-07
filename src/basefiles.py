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
* input: input, user output, and expected output (optional)
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

int main() {
    ios::sync_with_stdio(0);
    cin.tie(0);
    
    return 0;
}
"""
