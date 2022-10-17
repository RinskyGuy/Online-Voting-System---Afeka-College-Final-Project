#include <math.h>
#include <iostream>
#include "rsa.h"
using namespace std;

RsaCrypto::RsaCrypto()
{
    cout << "RSA initialize"<< endl;
    // 1st prime number p
    int p = 3;
    // 2nd prime number q
    int q = 11;
    n = p * q;
    cout << "the value of n = "<< n << endl;
    int phi = (p - 1) * (q - 1);
    cout << "the value of phi = " << phi << endl;

    for (e = 2; e < phi; ++e) {

        // e is for public key exponent
        if (gcd(e, phi) == 1) {
            break;
        }
    }
    cout << "the value of e = "  << e << endl;
    for (int i = 0; i <= 9; i++) {
        int x = 1 + (i * phi);

        // d is for private key exponent
        if (x % e == 0) {
            d = x / e;
            break;
        }
    }
}

int RsaCrypto::gcd(int a, int b) {
   if (a == 0 || b == 0)
        return 0;
   else if (a == b)
        return a;
   else if (a > b)
        return gcd(a - b, b);
   else return gcd(a, b - a);
}

double RsaCrypto::encrypt(int message)
{
    return fmod(pow(message, e), n);
}

double RsaCrypto::decrypt(double c)
{
    return fmod(pow(c, d), n);
}

int RsaCrypto::nBitRandom()
{
    // Returns a random number
    // between 2**(n-1)+1 and 2**n-1'''
    return fmod(rand(),(pow(2,NUM_KEY_BITS-1)+1 - pow(2,NUM_KEY_BITS-1) +1) + pow(2,NUM_KEY_BITS-1));
}