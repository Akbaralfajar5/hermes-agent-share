/*
 * $HASH CUDA Miner v4 — full 256-bit nonce, verified keccak256
 * Verified: CUDA output matches ethers.js keccak256 exactly (May 2026)
 * Usage: ./hash-miner-v4 <challenge_hex> <difficulty_hex> <gpu_id> [nonce_base_hex_64chars]
 *
 * Compile:
 *   RTX 5090 (Blackwell):  nvcc -O3 -arch=sm_120 -o hash-miner-v4 hash256-cuda-miner-v4.cu
 *   RTX 4090 (Ada):        nvcc -O3 -arch=sm_89  -o hash-miner-v4 hash256-cuda-miner-v4.cu
 *   RTX 3090 (Ampere):     nvcc -O3 -arch=sm_86  -o hash-miner-v4 hash256-cuda-miner-v4.cu
 *   Generic (sm_90):       nvcc -O3 -arch=sm_90  -o hash-miner-v4 hash256-cuda-miner-v4.cu
 *
 * Output: FOUND nonce=0x<64-hex-chars> gpu=<id>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <cuda_runtime.h>
#include <time.h>

#define ROTL64(x, y) (((x) << (y)) | ((x) >> (64 - (y))))

__device__ static const uint64_t RC[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL,
    0x800000000000808aULL, 0x8000000080008000ULL,
    0x000000000000808bULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL,
    0x000000000000008aULL, 0x0000000000000088ULL,
    0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL,
    0x8000000000008089ULL, 0x8000000000008003ULL,
    0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800aULL, 0x800000008000000aULL,
    0x8000000080008081ULL, 0x8000000000008080ULL,
    0x0000000080000001ULL, 0x8000000080008008ULL
};

__device__ void keccakf(uint64_t st[25]) {
    uint64_t t, bc[5];
    for (int r = 0; r < 24; r++) {
        // Theta
        bc[0]=st[0]^st[5]^st[10]^st[15]^st[20];
        bc[1]=st[1]^st[6]^st[11]^st[16]^st[21];
        bc[2]=st[2]^st[7]^st[12]^st[17]^st[22];
        bc[3]=st[3]^st[8]^st[13]^st[18]^st[23];
        bc[4]=st[4]^st[9]^st[14]^st[19]^st[24];
        t=bc[4]^ROTL64(bc[1],1); st[0]^=t;st[5]^=t;st[10]^=t;st[15]^=t;st[20]^=t;
        t=bc[0]^ROTL64(bc[2],1); st[1]^=t;st[6]^=t;st[11]^=t;st[16]^=t;st[21]^=t;
        t=bc[1]^ROTL64(bc[3],1); st[2]^=t;st[7]^=t;st[12]^=t;st[17]^=t;st[22]^=t;
        t=bc[2]^ROTL64(bc[4],1); st[3]^=t;st[8]^=t;st[13]^=t;st[18]^=t;st[23]^=t;
        t=bc[3]^ROTL64(bc[0],1); st[4]^=t;st[9]^=t;st[14]^=t;st[19]^=t;st[24]^=t;
        // Rho-Pi (chained — critical for correctness)
        t=st[1];
        t=st[1];st[1]=ROTL64(st[6],44);st[6]=ROTL64(st[9],20);st[9]=ROTL64(st[22],61);
        st[22]=ROTL64(st[14],39);st[14]=ROTL64(st[20],18);st[20]=ROTL64(st[2],62);
        st[2]=ROTL64(st[12],43);st[12]=ROTL64(st[13],25);st[13]=ROTL64(st[19],8);
        st[19]=ROTL64(st[23],56);st[23]=ROTL64(st[15],41);st[15]=ROTL64(st[4],27);
        st[4]=ROTL64(st[24],14);st[24]=ROTL64(st[21],2);st[21]=ROTL64(st[8],55);
        st[8]=ROTL64(st[16],45);st[16]=ROTL64(st[5],36);st[5]=ROTL64(st[3],28);
        st[3]=ROTL64(st[18],21);st[18]=ROTL64(st[17],15);st[17]=ROTL64(st[11],10);
        st[11]=ROTL64(st[7],6);st[7]=ROTL64(st[10],3);st[10]=ROTL64(t,1);
        // Chi
        bc[0]=st[0];bc[1]=st[1];bc[2]=st[2];bc[3]=st[3];bc[4]=st[4];
        st[0]^=(~bc[1])&bc[2];st[1]^=(~bc[2])&bc[3];st[2]^=(~bc[3])&bc[4];st[3]^=(~bc[4])&bc[0];st[4]^=(~bc[0])&bc[1];
        bc[0]=st[5];bc[1]=st[6];bc[2]=st[7];bc[3]=st[8];bc[4]=st[9];
        st[5]^=(~bc[1])&bc[2];st[6]^=(~bc[2])&bc[3];st[7]^=(~bc[3])&bc[4];st[8]^=(~bc[4])&bc[0];st[9]^=(~bc[0])&bc[1];
        bc[0]=st[10];bc[1]=st[11];bc[2]=st[12];bc[3]=st[13];bc[4]=st[14];
        st[10]^=(~bc[1])&bc[2];st[11]^=(~bc[2])&bc[3];st[12]^=(~bc[3])&bc[4];st[13]^=(~bc[4])&bc[0];st[14]^=(~bc[0])&bc[1];
        bc[0]=st[15];bc[1]=st[16];bc[2]=st[17];bc[3]=st[18];bc[4]=st[19];
        st[15]^=(~bc[1])&bc[2];st[16]^=(~bc[2])&bc[3];st[17]^=(~bc[3])&bc[4];st[18]^=(~bc[4])&bc[0];st[19]^=(~bc[0])&bc[1];
        bc[0]=st[20];bc[1]=st[21];bc[2]=st[22];bc[3]=st[23];bc[4]=st[24];
        st[20]^=(~bc[1])&bc[2];st[21]^=(~bc[2])&bc[3];st[22]^=(~bc[3])&bc[4];st[23]^=(~bc[4])&bc[0];st[24]^=(~bc[0])&bc[1];
        // Iota
        st[0]^=RC[r];
    }
}

/* keccak256 of exactly 64 bytes (challenge 32 + nonce 32) */
__device__ void keccak256_64(const uint8_t* in, uint8_t* out) {
    uint64_t st[25];
    for (int i=0;i<25;i++) st[i]=0;
    uint8_t block[136];
    for (int i=0;i<136;i++) block[i]=0;
    for (int i=0;i<64;i++) block[i]=in[i];
    block[64]=0x01;   // Keccak padding (NOT 0x06 = SHA3)
    block[135]=0x80;
    for (int i=0;i<17;i++) {
        uint64_t w=0;
        for (int j=0;j<8;j++) w|=((uint64_t)block[i*8+j])<<(j*8);
        st[i]^=w;
    }
    keccakf(st);
    for (int i=0;i<4;i++) for (int j=0;j<8;j++) out[i*8+j]=(st[i]>>(j*8))&0xFF;
}

/* Add uint256 (32 bytes big-endian) + uint64 scalar */
__device__ void add256_64(const uint8_t* base, uint64_t delta, uint8_t* result) {
    for (int i=0;i<32;i++) result[i]=base[i];
    uint64_t carry = delta;
    for (int i=31; i>=0 && carry>0; i--) {
        uint64_t sum = (uint64_t)result[i] + (carry & 0xFF);
        result[i] = (uint8_t)(sum & 0xFF);
        carry = (carry >> 8) + (sum >> 8);
    }
}

__global__ void mine_kernel(
    const uint8_t* challenge,
    const uint8_t* difficulty,
    const uint8_t* nonce_base,  // 32-byte base nonce (big-endian)
    uint64_t nonce_range,
    uint8_t* found_nonce,       // 32 bytes output
    int* found_flag
) {
    uint64_t tid = (uint64_t)blockIdx.x * blockDim.x + threadIdx.x;
    uint64_t stride = (uint64_t)gridDim.x * blockDim.x;

    uint8_t input[64];
    uint8_t hash[32];
    uint8_t nonce[32];

    for (int i = 0; i < 32; i++) input[i] = challenge[i];

    for (uint64_t i = tid; i < nonce_range; i += stride) {
        if (*found_flag) return;

        add256_64(nonce_base, i, nonce);
        for (int j=0;j<32;j++) input[32+j]=nonce[j];
        keccak256_64(input, hash);

        // hash < difficulty (big-endian comparison)
        bool valid = true;
        for (int j = 0; j < 32; j++) {
            if (hash[j] < difficulty[j]) { valid = true; break; }
            if (hash[j] > difficulty[j]) { valid = false; break; }
        }

        if (valid) {
            if (atomicCAS(found_flag, 0, 1) == 0) {
                for (int j=0;j<32;j++) found_nonce[j]=nonce[j];
            }
            return;
        }
    }
}

void hex_to_bytes(const char* hex, uint8_t* bytes, int len) {
    const char* h = hex;
    if (h[0] == '0' && (h[1] == 'x' || h[1] == 'X')) h += 2;
    for (int i = 0; i < len; i++) {
        unsigned int v;
        sscanf(h + i*2, "%02x", &v);
        bytes[i] = (uint8_t)v;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <challenge_hex> <difficulty_hex> <gpu_id> [nonce_base_hex_64chars]\n", argv[0]);
        return 1;
    }

    int gpu_id = atoi(argv[3]);
    uint8_t nonce_base[32] = {0};

    if (argc >= 5) {
        hex_to_bytes(argv[4], nonce_base, 32);
    } else {
        srand(time(NULL) ^ (gpu_id * 0x9e3779b9));
        for (int i=0;i<32;i++) nonce_base[i]=(uint8_t)(rand()&0xFF);
        nonce_base[0] &= 0x7F;
    }

    cudaSetDevice(gpu_id);

    uint8_t challenge[32], difficulty[32];
    hex_to_bytes(argv[1], challenge, 32);
    hex_to_bytes(argv[2], difficulty, 32);

    fprintf(stderr, "[GPU%d] Base: 0x", gpu_id);
    for (int i=0;i<8;i++) fprintf(stderr, "%02x", nonce_base[i]);
    fprintf(stderr, "...\n");

    uint8_t *d_challenge, *d_difficulty, *d_nonce_base, *d_found_nonce;
    int *d_found_flag;
    cudaMalloc(&d_challenge, 32); cudaMalloc(&d_difficulty, 32);
    cudaMalloc(&d_nonce_base, 32); cudaMalloc(&d_found_nonce, 32);
    cudaMalloc(&d_found_flag, sizeof(int));
    cudaMemcpy(d_challenge, challenge, 32, cudaMemcpyHostToDevice);
    cudaMemcpy(d_difficulty, difficulty, 32, cudaMemcpyHostToDevice);
    cudaMemcpy(d_nonce_base, nonce_base, 32, cudaMemcpyHostToDevice);

    int zero = 0; uint8_t zero32[32] = {0};
    cudaMemcpy(d_found_flag, &zero, sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_found_nonce, zero32, 32, cudaMemcpyHostToDevice);

    int blocks = 4096, threads = 256;
    uint64_t batch_size = (uint64_t)blocks * threads * 64;
    uint64_t total_hashes = 0;
    time_t t_start = time(NULL), t_last = t_start;

    while (1) {
        mine_kernel<<<blocks, threads>>>(d_challenge, d_difficulty, d_nonce_base,
                                         batch_size, d_found_nonce, d_found_flag);
        cudaDeviceSynchronize();

        int found = 0;
        cudaMemcpy(&found, d_found_flag, sizeof(int), cudaMemcpyDeviceToHost);
        if (found) {
            uint8_t nonce[32];
            cudaMemcpy(nonce, d_found_nonce, 32, cudaMemcpyDeviceToHost);
            printf("FOUND nonce=0x");
            for (int i=0;i<32;i++) printf("%02x", nonce[i]);
            printf(" gpu=%d\n", gpu_id);
            fflush(stdout);
            break;
        }

        // Advance base nonce
        uint8_t h_base[32];
        cudaMemcpy(h_base, d_nonce_base, 32, cudaMemcpyDeviceToHost);
        uint64_t carry = batch_size;
        for (int i=31; i>=0 && carry>0; i--) {
            uint64_t sum = (uint64_t)h_base[i] + (carry & 0xFF);
            h_base[i] = (uint8_t)(sum & 0xFF);
            carry = (carry >> 8) + (sum >> 8);
        }
        cudaMemcpy(d_nonce_base, h_base, 32, cudaMemcpyHostToDevice);
        cudaMemcpy(d_found_flag, &zero, sizeof(int), cudaMemcpyHostToDevice);

        total_hashes += batch_size;
        time_t now = time(NULL);
        if (now - t_last >= 5) {
            double elapsed = difftime(now, t_start);
            fprintf(stderr, "[GPU%d] %.1f MH/s | %.2fB hashes\n",
                gpu_id, (double)total_hashes/elapsed/1e6, (double)total_hashes/1e9);
            t_last = now;
        }
    }

    cudaFree(d_challenge); cudaFree(d_difficulty);
    cudaFree(d_nonce_base); cudaFree(d_found_nonce); cudaFree(d_found_flag);
    return 0;
}
