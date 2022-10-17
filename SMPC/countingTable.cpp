#include "countingTable.h"

using namespace std;

void CountingTable::setFileName(string fname) {
    this->fname = fname;

    ifstream ifile;
    ifile.open(fname);
    if(!ifile) {
        fstream newFile;

        newFile.open(fname,ios::out); // create new file
        for(int i=0; i<NUM_PARTIES; ++i){ 
            string count = "";
            for(int j=0; j<NUM_BITS; ++j) {
                char c = '0' + rand()%2;
                count.push_back(char(c));
            }
            newFile << count <<endl;
        }

        newFile.close();
    }
}

// This function's input is the party number we want to retrieve.
// This function's output is the fragmented binary number of the input party number votes in the text file.
bitset<NUM_BITS> CountingTable::getCurrentPartyCount(int partyNum){
    string text;
    fstream newFile;
    newFile.open(fname,ios::in); // Open text file in server A that holds all its fragmanted party counts.
    if(newFile.is_open()){
        // This for loop gets the wanted line by ignoring the previous lines.
        for(int i=0;i<=partyNum;++i){
            getline(newFile,text);
        }
    }
    newFile.close();
    bitset<NUM_BITS> b3(text); // converts the binary count from string to bitset
    return b3;
}

// This function's inputs are the party number we want to save and the fragmented binary number of that party votes.
// This function updates the fragmented binary number of the input party number votes in the text file.
void CountingTable::setCurrentPartyCount(int partyNum, bitset<NUM_BITS> partyCount){
    string text = partyCount.to_string(); // converts the bitset to string in order to save it into the text file.
    fstream newFile;
    fstream oldFile;
    oldFile.open(fname,ios::in); // open the original file.
    newFile.open("AfterChanges.txt",ios::out); //open a new file that will hold the old data with the changes.
    if(newFile.is_open()&&oldFile.is_open()){
        // For each party that is chronologicly placed before the current party, copy its fragmanted vote as is.   
        for(int i=0;i<partyNum;++i){ 
            getline(oldFile,text);
            newFile << text <<endl;
        }
        // For the current party, write to the new file the updated fargmented vote.
        newFile << partyCount.to_string() << endl;
        getline(oldFile,text); // Ignore the current party line in the old file.
        // For each party that is chronologicly placed after the current party, copy its fragmanted vote as is.
        if (partyNum<NUM_PARTIES){
            for(int i=partyNum + 1;i<NUM_PARTIES;++i){
                getline(oldFile,text);
                newFile << text <<endl;
            }
        }   
    }
    newFile.close();
    oldFile.close();
    // Replace the old file with the new file by deletion and renaming.
    if (remove(fname.c_str()) == 0)
        rename("AfterChanges.txt", fname.c_str());
    else
        printf("Unable to delete the file");
}