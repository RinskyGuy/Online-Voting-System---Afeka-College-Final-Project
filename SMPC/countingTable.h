
#include <bitset>
#include <fstream>
#include <string>
#include "rsa.cpp"

using namespace std;

const int NUM_PARTIES = 5; //The amount of parties participating in the election
const int NUM_BITS = 24; // The binary amount of maximum votes that a single party can be voted in an election

class CountingTable{ 
private:
    string fname;

public:
    bitset<NUM_BITS> partyCount; // Holds the 1st fragmented binary number of the current party's votes
    RsaCrypto rsa; // Holds our simple implementation of RSA

    // Constructor
    CountingTable(string fname): fname(fname) {}
    CountingTable() {};

    void setFileName(string fname);
    bitset<NUM_BITS> getCurrentPartyCount(int partyNum);
    void setCurrentPartyCount(int partyNum, bitset<NUM_BITS> partyCount);
};