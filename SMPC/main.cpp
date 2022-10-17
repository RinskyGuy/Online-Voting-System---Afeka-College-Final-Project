#include <iostream>
#include <math.h>
//#include <Windows.h>
//#include <ntsecapi.h>
#include "intermediateServer.h"
#include <time.h>

using namespace std;

int main(int argc, char *argv[]) {   
    srand(time(0)); // Initiate a basic random
    IntermediateServer server = IntermediateServer(); // Simulate the intermediate server.
    int vote; 

    // The Intermidiate server is also the web server, hence it handles the voter's vote.
    // In this terminal application the vote is casted via a simple cout and cin process.
    if (argc != 2) {
        cout << "Enter which party number you want to vote for (1-" << NUM_PARTIES << "): "<< endl;
        cin >> vote;
    }else{
        vote = strtol(argv[1], NULL, 10);
    }

    cout << "Befor vote:" << endl;
    server.printTotalCount();

    server.addVote(vote);

    // the next for loop is for our debugging perpuses - to find out the current count for each party after the process.
    cout << "After vote:" << endl;
    server.printTotalCount();
    return 0;
}