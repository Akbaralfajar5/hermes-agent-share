/*
 * eqm_leaves.cu — CUDA BLAKE2b leaf generator for Equium (EQM) mining
 *
 * Single-nonce version. Outputs hex to stdout.
 * Usage: ./eqm-leaves <input_hex_81b> <nonce_hex_32b> <n_leaves> [gpu_id]
 *
 * Compile: nvcc -O3 -arch=sm_120 -o eqm-leaves eqm_leaves.cu
 * (sm_120=RTX5060Ti/5090, sm_89=RTX4090, sm_86=RTX3090, sm_75=RTX2060)
 *
 * VERIFIED: Output matches Python hashlib.blake2b byte-for-byte (May 2026)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <cuda_runtime.h>

#define N_LEAVES 131072
#define LEAF_BYTES 12
#define LEAVES_PER_CALL 5
#define DIGEST_LEN 60
#define I_LEN 81
#define NONCE_LEN 32

__device__ __constant__ uint64_t BLAKE2B_IV[8] = {
    0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL,
    0x3c6ef372fe94f82bULL, 0xa54ff53a5f1d36f1ULL,
    0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL,
    0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL,
};

__device__ __constant__ uint8_t SIGMA[12][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15},
    {14,10, 4, 8, 9,15,13, 6, 1,12, 0, 2,11, 7, 5, 3},
    {11, 8,12, 0, 5, 2,15,13,10,14, 3, 6, 7, 1, 9, 4},
    { 7, 9, 3, 1,13,12,11,14, 2, 6, 5,10, 4, 0,15, 8},
    { 9, 0, 5, 7, 2, 4,10,15,14, 1,11,12, 6, 8, 3,13},
    { 2,12, 6,10, 0,11, 8, 3, 4,13, 7, 5,15,14, 1, 9},
    {12, 5, 1,15,14,13, 4,10, 0, 7, 6, 3, 9, 2, 8,11},
    {13,11, 7,14,12, 1, 3, 9, 5, 0,15, 4, 8, 6, 2,10},
    { 6,15,14, 9,11, 3, 0, 8,12, 2,13, 7, 1, 4,10, 5},
    {10, 2, 8, 4, 7, 6, 1, 5,15,11, 9,14, 3,12,13, 0},
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15},
    {14,10, 4, 8, 9,15,13, 6, 1,12, 0, 2,11, 7, 5, 3},
};

#define ROTR64(x, n) (((x) >> (n)) | ((x) << (64 - (n))))

__device__ void blake2b_compress(uint64_t h[8], const uint64_t m[16], uint64_t t, int is_final) {
    uint64_t v[16];
    for (int i = 0; i < 8; i++) v[i] = h[i];
    for (int i = 0; i < 8; i++) v[8+i] = BLAKE2B_IV[i];
    v[12] ^= t;
    if (is_final) v[14] ^= 0xFFFFFFFFFFFFFFFFULL;

    for (int r = 0; r < 12; r++) {
        const uint8_t *s = SIGMA[r];
        #define G(a,b,c,d,x,y) \
            v[a] += v[b] + (x); v[d] = ROTR64(v[d]^v[a],32); \
            v[c] += v[d];       v[b] = ROTR64(v[b]^v[c],24); \
            v[a] += v[b] + (y); v[d] = ROTR64(v[d]^v[a],16); \
            v[c] += v[d];       v[b] = ROTR64(v[b]^v[c],63);
        G(0,4, 8,12, m[s[ 0]], m[s[ 1]]);
        G(1,5, 9,13, m[s[ 2]], m[s[ 3]]);
        G(2,6,10,14, m[s[ 4]], m[s[ 5]]);
        G(3,7,11,15, m[s[ 6]], m[s[ 7]]);
        G(0,5,10,15, m[s[ 8]], m[s[ 9]]);
        G(1,6,11,12, m[s[10]], m[s[11]]);
        G(2,7, 8,13, m[s[12]], m[s[13]]);
        G(3,4, 9,14, m[s[14]], m[s[15]]);
        #undef G
    }
    for (int i = 0; i < 8; i++) h[i] ^= v[i] ^ v[i+8];
}

__global__ void gen_leaves_kernel(
    const uint8_t* __restrict__ input_d,
    const uint8_t* __restrict__ nonce_d,
    uint8_t* __restrict__ out_d,
    uint32_t n_leaves
) {
    uint32_t call_idx = blockIdx.x * blockDim.x + threadIdx.x;
    uint32_t n_calls = (n_leaves + LEAVES_PER_CALL - 1) / LEAVES_PER_CALL;
    if (call_idx >= n_calls) return;

    uint64_t h[8];
    for (int i = 0; i < 8; i++) h[i] = BLAKE2B_IV[i];
    // CRITICAL: digest_len=60=0x3c, NOT 0x60=96
    h[0] ^= (uint64_t)0x000000000101003cULL;  // digest_len=60(0x3c), fanout=1, depth=1
    h[6] ^= 0x576f50687361635aULL;  // "ZcashPoW" LE
    h[7] ^= 0x0000000500000060ULL;  // n=96, k=5

    uint8_t msg[128];
    memset(msg, 0, 128);
    for (int i = 0; i < I_LEN; i++) msg[i] = input_d[i];
    for (int i = 0; i < NONCE_LEN; i++) msg[81 + i] = nonce_d[i];
    msg[113] = (call_idx      ) & 0xFF;
    msg[114] = (call_idx >>  8) & 0xFF;
    msg[115] = (call_idx >> 16) & 0xFF;
    msg[116] = (call_idx >> 24) & 0xFF;

    uint64_t m[16];
    for (int i = 0; i < 16; i++) {
        m[i] = 0;
        for (int j = 0; j < 8; j++)
            m[i] |= ((uint64_t)msg[i*8+j]) << (j*8);
    }

    blake2b_compress(h, m, 117, 1);

    uint8_t digest[64];
    for (int i = 0; i < 8; i++)
        for (int j = 0; j < 8; j++)
            digest[i*8+j] = (h[i] >> (j*8)) & 0xFF;

    for (int k = 0; k < LEAVES_PER_CALL; k++) {
        uint32_t leaf_idx = call_idx * LEAVES_PER_CALL + k;
        if (leaf_idx >= n_leaves) break;
        uint8_t* dst = out_d + leaf_idx * LEAF_BYTES;
        const uint8_t* src = digest + k * LEAF_BYTES;
        for (int b = 0; b < LEAF_BYTES; b++) dst[b] = src[b];
    }
}

static int hex_decode(const char* hex, uint8_t* out, int expected_len) {
    int len = strlen(hex);
    if (len != expected_len * 2) return -1;
    for (int i = 0; i < expected_len; i++) {
        unsigned int byte;
        if (sscanf(hex + i*2, "%02x", &byte) != 1) return -1;
        out[i] = (uint8_t)byte;
    }
    return 0;
}

int main(int argc, char** argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <input_hex_81b> <nonce_hex_32b> <n_leaves> [gpu_id]\n", argv[0]);
        return 1;
    }

    uint8_t input[I_LEN];
    uint8_t nonce[NONCE_LEN];
    uint32_t n_leaves = (uint32_t)atoi(argv[3]);
    int gpu_id = (argc >= 5) ? atoi(argv[4]) : 0;

    if (hex_decode(argv[1], input, I_LEN) != 0) {
        fprintf(stderr, "Error: input must be %d hex bytes (%d chars)\n", I_LEN, I_LEN*2);
        return 1;
    }
    if (hex_decode(argv[2], nonce, NONCE_LEN) != 0) {
        fprintf(stderr, "Error: nonce must be %d hex bytes (%d chars)\n", NONCE_LEN, NONCE_LEN*2);
        return 1;
    }
    if (n_leaves == 0 || n_leaves > N_LEAVES) {
        fprintf(stderr, "Error: n_leaves must be 1..%d\n", N_LEAVES);
        return 1;
    }

    cudaSetDevice(gpu_id);

    uint8_t *d_input, *d_nonce, *d_out;
    size_t out_size = (size_t)n_leaves * LEAF_BYTES;

    cudaMalloc(&d_input, I_LEN);
    cudaMalloc(&d_nonce, NONCE_LEN);
    cudaMalloc(&d_out, out_size);

    cudaMemcpy(d_input, input, I_LEN, cudaMemcpyHostToDevice);
    cudaMemcpy(d_nonce, nonce, NONCE_LEN, cudaMemcpyHostToDevice);

    uint32_t n_calls = (n_leaves + LEAVES_PER_CALL - 1) / LEAVES_PER_CALL;
    int threads_per_block = 256;
    int blocks = (n_calls + threads_per_block - 1) / threads_per_block;

    gen_leaves_kernel<<<blocks, threads_per_block>>>(d_input, d_nonce, d_out, n_leaves);
    cudaDeviceSynchronize();

    uint8_t* h_out = (uint8_t*)malloc(out_size);
    cudaMemcpy(h_out, d_out, out_size, cudaMemcpyDeviceToHost);

    for (size_t i = 0; i < out_size; i++) printf("%02x", h_out[i]);
    printf("\n");

    free(h_out);
    cudaFree(d_input);
    cudaFree(d_nonce);
    cudaFree(d_out);

    return 0;
}
