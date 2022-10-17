#include "countingTable.cpp"
#include <vector>

using namespace std;

// Class that simulates the intermediate server which will initate the process of vote counting
class IntermediateServer
{
public:
    CountingTable serverA; // A variable that represent actions taken at server A
    CountingTable serverB; // A variable that represent actions taken at server B

    // Constructor
    IntermediateServer()
    {
        serverA.setFileName("countA.txt");
        serverB.setFileName("countB.txt");
    }

    // This function's input is a bit: 1 if the current party was voted and 0 otherwise
    // This function's output is a pair of bits, where the XOR product of the pair is always the input. 
    // The pair will be randomly splitted between servers A and B
    pair<int,int> splitVote(int vote)
    {
        int fragmentA = rand()%2; // Fragmant A will be sent to server A, The randomized result affect FragmentB
        int fragmentB = vote ^ fragmentA; // Fragment B will be sent to server B. This line also ensures that
                                          // both fragments will give the original vote via their XOR product

        return pair<int,int>{fragmentA,fragmentB};
    }

    void addVote(int vote) 
    {
        vote = vote-1; //make sure that party 1 is treated as party 0, party 2 is treated as party 1 and so on...
        //For each party 
        for(int i = 0; i<NUM_PARTIES; ++i){
            if(i == vote){
                // The party was voted. Add 1 to the XOR product between server A and server B and mix their count bits.
                addPartyVote(1,i); 
            }else{
                // The party was not voted. Just mix the bits in of the current party in both server A and B,
                // but don't change the count
                addPartyVote(0,i); 
            }
        }
    }
    // This function's input is the current party to calculate (partyNum),
    // and a bit that states if that party was voted for by the voter: 0 if not voted, 1 if voted.
    // This function initiates the Oblivious Transfer protocol and at the end of the process, 
    // adds a vote to the XOR product between Server A's and server's B current party.
    void addPartyVote(int vote, int partyNum){
        pair<int,int> splittedVote = splitVote(vote); // Calculate which bit should be sent to each server.
        int fragmentedVoteA = splittedVote.first; // The bit that will be sent to server A
        int fragmentedVoteB = splittedVote.second; // The bit that will be sent to server B
        // TODO: Intemidiate server sends the splitted vote to servers A and B with the partyNumber.
        // SERVER A AND B:
        serverA.partyCount = serverA.getCurrentPartyCount(partyNum); // Simulate server A getting his own current party's count 
        serverB.partyCount = serverB.getCurrentPartyCount(partyNum); // Simulate server B getting his own current party's count
        int prevBitA = serverA.partyCount[0]; // The first bit in Server's A count 
        int prevBitB = serverB.partyCount[0]; // The first bit in Server's B count 

        serverA.partyCount[0] = serverA.partyCount[0] ^ fragmentedVoteA;  // Server A's 1st step of Oblivious Transfer Protocol.
        serverB.partyCount[0] = serverB.partyCount[0] ^ fragmentedVoteB; // Server B's 1st step of Oblivious Transfer Protocol.

        pair<int, int> carry{fragmentedVoteA, fragmentedVoteB}; // Declaration of the carry variable that each server holds
        pair<int,int> prevBit{prevBitA, prevBitB}; // Decleration of the previous bit variable that each server holds.

        // This For loop starting the Oblivious Transfer protocol for each bit in the party count, creating a secured and 
        // obscured addition that splits between servers A and B.
        for(int i=1; i < NUM_BITS; ++i){
            // SERVER A
            obliviousTransfer(i, prevBit, carry); //Start Oblivious Transfer protocol
            prevBit.first = serverA.partyCount[i]; // Updates server A previous bit variable to hold the calculated result
            serverA.partyCount[i] = serverA.partyCount[i] ^ carry.first;
        }
        serverA.setCurrentPartyCount(partyNum,serverA.partyCount); // Simulates server A saving the product of the last calculations
        serverB.setCurrentPartyCount(partyNum,serverB.partyCount); // Simulates server B saving the product of the last calculations
    }

    /*
    This function's inputs are: 
    i = the current bit that is calculated in the bitset.
    (?) prevbit = the last bit that was calculated in the bitset.
    (?) carry =  the carry product that was calculated.

    This function is responsible for the core calculation in the elections.
    If the party was voted, it adds a vote for the current party XOR product between servers A and B while 
    "randomly" mixing both servers bits positions.
    If the party was NOT voted, servers A and B both are "randomly" mixing bits positions for the corrent 
    party, while keeping. the XOR product the same as before.

    Example 1: Party 2 was voted by the voter. 
    Before the vote, Setver A had bx10011 count and server B had bx10111 count (Before the calculation party 2
    had bx100 votes - 4 votes). After this function executes and the vote is calculated, Party 2 will have 5 votes, 
    but it is unknown which bits will be in server's A count and which bits will be at server's B count.
    A possible outcome will be such that server A has bx01001 count and server b has a bx01100 count (A XOR B= bx00101)
    
    Example 2: Party 1 was not voted by the voter. 
    Before the vote, Setver A had bx10011 count and server B had bx00111 count (Before the calculation party 1
    had bx10100 votes - 20 votes). After this function executes and calculated, Party 1 will still have 20 votes, 
    but it is unknown which bits will be in server's A count and which bits will be at server's B count.
    A possible outcome will be such that server A has bx01001 count and server b has a bx11101 count (A XOR B= bx10100)
    */
    void obliviousTransfer(int i, pair<int,int>& prevBit, pair<int,int>& carry){
        // SERVER A
        int prevCarry = carry.first;
        carry.first = rand() %2;
        vector<int> tt = computeTruthTable(carry.first, prevCarry, prevBit.first);
        // END SERVER A

        // SERVER B
        int rowNum = (int)(bitset<2>(to_string(prevBit.second)+to_string(carry.second))).to_ulong(); // Generate which row to select from the truth table
        //Server B generates 4 random numbers and encypts only 1 of them using server A's public key
        vector<unsigned int> x = {(unsigned int)(rand()%(int)serverA.rsa.n), (unsigned int)(rand()%(int)serverA.rsa.n), (unsigned int)(rand()%(int)serverA.rsa.n), (unsigned int)(rand()%(int)serverA.rsa.n)};
        vector<unsigned int> y(x);
        for(int k = 0; k<x.size(); ++k){
            if(k == rowNum)
            {
                y[k] = serverA.rsa.encrypt(x[k]); 
            }

        }
        // END SERVER B

        // SERVER A
        vector<unsigned int> res;
        unsigned int z;

        for(int j = 0; j < 4; ++j) {
            z = serverA.rsa.decrypt(y[j]);
            res.push_back((z % 2) ^ tt[j]);
        }

        // END SERVER A

        // SERVER B
        carry.second = (res[rowNum] % 2) ^ (x[rowNum] % 2);
        prevBit.second = serverB.partyCount[i];
        serverB.partyCount[i] = serverB.partyCount[i] ^ carry.second;
        // END SERVER B
    }

    // This function calculates the truth table that server A must calculate\
    to be used in the Oblivious transfer protocol.
    // TODO: Add more data
    vector<int> computeTruthTable(int carry, int prevCarry, int prevBit){
        vector<vector<int>> bVals{{0,0}, {0,1}, {1,0}, {1,1}};
        vector<int> tt(4);

        for (int i=0; i<4; ++i){
            tt[i] = ((prevBit ^ bVals[i][0])*(prevCarry^bVals[i][1])) ^ carry;
        }
        return tt;
    }

    // This function's input is the current party number
    // This function's output is the XOR product between the counts in both servers A and B\
     - the total number of votes each party got when this function was called
    bitset<NUM_BITS> getTotalCount(int partyNum)
    {
        return serverA.getCurrentPartyCount(partyNum) ^ serverB.getCurrentPartyCount(partyNum);
    }
    
    void printTotalCount() 
    {
        for(int i=0; i<NUM_PARTIES;++i){
            cout << "For party " << i+1  << ": " << getTotalCount(i) << "\n";
        }
    }
};