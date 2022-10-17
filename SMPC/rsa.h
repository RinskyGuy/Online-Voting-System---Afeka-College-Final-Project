#ifndef __RSA_CRYPTO_H
#define __RSA_CRYPTO_H

const int NUM_KEY_BITS = 1024;

class RsaCrypto
{
private:
   static int gcd(int a, int b);

public:
    int n;
    int e;
    int d;

    RsaCrypto();

    double encrypt(int message);
    double decrypt(double c);
    int nBitRandom();

};

#endif