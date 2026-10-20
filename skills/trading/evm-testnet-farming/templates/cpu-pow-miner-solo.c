/*
 * CPU PoW Miner — single-threaded, no mutex, pure parallel
 * Usage: ./miner-solo <challenge_hex> <difficulty_hex> <nonce_start_hex> <nonce_step_hex>
 * Output: FOUND nonce=0x... hashes=N elapsed=X hashrate=Y (on stdout)
 *         Progress: NM @ X.XXMH/s (on stderr every 5M hashes)
 * Compile: gcc -O3 -march=native -o miner-solo miner-solo.c
 *
 * Design: spawn N of these processes from an orchestrator (Node.js/Python).
 * Each gets nonce_start=i, nonce_step=N_WORKERS.
 * First to find kills all others. No shared memory needed.
 * Achieves ~99% CPU vs ~50% for pthreads with mutex.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

/* ── Keccak-256 (Ethereum keccak, NOT SHA3 — padding byte 0x01 not 0x06) ── */
#define KECCAK_ROUNDS 24
static const uint64_t keccak_rc[24] = {
    0x0000000000000001ULL,0x0000000000008082ULL,0x800000000000808aULL,
    0x8000000080008000ULL,0x000000000000808bULL,0x0000000080000001ULL,
    0x8000000080008081ULL,0x8000000000008009ULL,0x000000000000008aULL,
    0x0000000000000088ULL,0x0000000080008009ULL,0x000000008000000aULL,
    0x000000008000808bULL,0x800000000000008bULL,0x8000000000008089ULL,
    0x8000000000008003ULL,0x8000000000008002ULL,0x8000000000000080ULL,
    0x000000000000800aULL,0x800000008000000aULL,0x8000000080008081ULL,
    0x8000000000008080ULL,0x0000000080000001ULL,0x8000000080008008ULL
};
static const int rho[24]={1,3,6,10,15,21,28,36,45,55,2,14,27,41,56,8,25,43,62,18,39,61,20,44};
static const int pi[24]={10,7,11,17,18,3,5,16,8,21,24,4,15,23,19,13,12,2,20,14,22,9,6,1};

static inline uint64_t rotl64(uint64_t x,int n){return(x<<n)|(x>>(64-n));}

static void keccakf(uint64_t st[25]){
    uint64_t t,bc[5];
    for(int r=0;r<KECCAK_ROUNDS;r++){
        for(int i=0;i<5;i++)bc[i]=st[i]^st[i+5]^st[i+10]^st[i+15]^st[i+20];
        for(int i=0;i<5;i++){t=bc[(i+4)%5]^rotl64(bc[(i+1)%5],1);for(int j=0;j<25;j+=5)st[j+i]^=t;}
        t=st[1];for(int i=0;i<24;i++){int j=pi[i];bc[0]=st[j];st[j]=rotl64(t,rho[i]);t=bc[0];}
        for(int j=0;j<25;j+=5){for(int i=0;i<5;i++)bc[i]=st[j+i];for(int i=0;i<5;i++)st[j+i]^=(~bc[(i+1)%5])&bc[(i+2)%5];}
        st[0]^=keccak_rc[r];
    }
}

static void keccak256(const uint8_t*in,size_t inlen,uint8_t*out){
    uint64_t st[25]={0};uint8_t temp[136];size_t rsiz=136;
    while(inlen>=rsiz){for(size_t i=0;i<rsiz/8;i++)st[i]^=((uint64_t*)in)[i];keccakf(st);in+=rsiz;inlen-=rsiz;}
    memcpy(temp,in,inlen);temp[inlen++]=0x01;memset(temp+inlen,0,rsiz-inlen);temp[rsiz-1]|=0x80;
    for(size_t i=0;i<rsiz/8;i++)st[i]^=((uint64_t*)temp)[i];keccakf(st);memcpy(out,st,32);
}

static void hex2bytes(const char*hex,uint8_t*out,int len){
    if(hex[0]=='0'&&(hex[1]=='x'||hex[1]=='X'))hex+=2;
    for(int i=0;i<len;i++)sscanf(hex+2*i,"%2hhx",&out[i]);
}

/* Compare 32-byte big-endian: return 1 if a < b */
static inline int bytes32_lt(const uint8_t*a,const uint8_t*b){
    for(int i=0;i<32;i++){if(a[i]<b[i])return 1;if(a[i]>b[i])return 0;}return 0;
}

int main(int argc,char*argv[]){
    if(argc<5){
        fprintf(stderr,"Usage: %s <challenge_hex> <difficulty_hex> <nonce_start_hex> <nonce_step_hex>\n",argv[0]);
        return 1;
    }
    uint8_t challenge[32],difficulty[32];
    hex2bytes(argv[1],challenge,32);
    hex2bytes(argv[2],difficulty,32);
    uint64_t nonce=strtoull(argv[3],NULL,0);
    uint64_t step=strtoull(argv[4],NULL,0);

    uint8_t input[64],hash[32];
    memcpy(input,challenge,32);
    uint64_t count=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);

    while(1){
        /* Pack nonce as big-endian uint256 (32 bytes, nonce in last 8 bytes) */
        memset(input+32,0,24);
        input[56]=(nonce>>56)&0xff;input[57]=(nonce>>48)&0xff;
        input[58]=(nonce>>40)&0xff;input[59]=(nonce>>32)&0xff;
        input[60]=(nonce>>24)&0xff;input[61]=(nonce>>16)&0xff;
        input[62]=(nonce>>8)&0xff;input[63]=(nonce)&0xff;
        keccak256(input,64,hash);
        count++;
        if(bytes32_lt(hash,difficulty)){
            clock_gettime(CLOCK_MONOTONIC,&t1);
            double elapsed=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
            fprintf(stdout,"FOUND nonce=0x%016llx hashes=%llu elapsed=%.2f hashrate=%.2f\n",
                (unsigned long long)nonce,(unsigned long long)count,elapsed,count/elapsed/1e6);
            fflush(stdout);
            return 0;
        }
        nonce+=step;
        if(count%5000000==0){
            clock_gettime(CLOCK_MONOTONIC,&t1);
            double elapsed=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
            fprintf(stderr,"%.0fM @ %.2fMH/s\n",count/1e6,count/elapsed/1e6);
            fflush(stderr);
        }
    }
}
