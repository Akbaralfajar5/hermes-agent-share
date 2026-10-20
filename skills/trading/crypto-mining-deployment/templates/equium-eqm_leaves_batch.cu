/*
 * eqm_leaves_batch.cu — CUDA BLAKE2b batch leaf generator for EQM mining
 *
 * Processes N nonces in parallel on GPU in one kernel launch.
 * Each nonce → 131072 leaves of 12 bytes.
 *
 * Usage:
 *   ./eqm-leaves-batch <input_hex_81b> <nonces_hex_Nx64> <n_nonces> [gpu_id]
 *   - nonces_hex: concatenated hex of N nonces (N * 64 hex chars)
 * Output: binary to stdout — N * 131072 * 12 bytes
 *
 * Compile:
 *   nvcc -O3 -arch=sm_120 -o eqm-leaves-batch eqm_leaves_batch.cu  # RTX 5060 Ti / 5090
 *   nvcc -O3 -arch=sm_89  -o eqm-leaves-batch eqm_leaves_batch.cu  # RTX 4090
 *   nvcc -O3 -arch=sm_86  -o eqm-leaves-batch eqm_leaves_batch.cu  # RTX 3090
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <cuda_runtime.h>

#define N_LEAVES 131072
#define LEAF_BYTES 12
#define LEAVES_PER_CALL 5
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

/*
 * Kernel: each thread = one BLAKE2b call (5 leaves) for one nonce.
 * global_id = nonce_idx * n_calls + call_idx
 */
__global__ void gen_leaves_batch_kernel(
    const uint8_t* __restrict__ input_d,
    const uint8_t* __restrict__ nonces_d,
    uint8_t* __restrict__ out_d,
    uint32_t n_nonces,
    uint32_t n_leaves
) {
    uint32_t n_calls = (n_leaves + LEAVES_PER_CALL - 1) / LEAVES_PER_CALL;
    uint32_t global_id = blockIdx.x * blockDim.x + threadIdx.x;
    if (global_id >= n_nonces * n_calls) return;

    uint32_t nonce_idx = global_id / n_calls;
    uint32_t call_idx  = global_id % n_calls;
    const uint8_t* nonce = nonces_d + nonce_idx * NONCE_LEN;

    // Init BLAKE2b state with ZcashPoW personalization
    uint64_t h[8];
    for (int i = 0; i < 8; i++) h[i] = BLAKE2B_IV[i];
    h[0] ^= 0x000000000101003cULL;  // digest_len=60(0x3c), fanout=1, depth=1
    h[6] ^= 0x576f50687361635aULL;  // "ZcashPoW" LE
    h[7] ^= 0x0000000500000060ULL;  // n=96, k=5

    // Build message: input(81) || nonce(32) || call_idx_le(4) || pad(11) = 128 bytes
    uint8_t msg[128];
    #pragma unroll
    for (int i = 0; i < 128; i++) msg[i] = 0;
    for (int i = 0; i < I_LEN; i++) msg[i] = input_d[i];
    for (int i = 0; i < NONCE_LEN; i++) msg[81 + i] = nonce[i];
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

    uint8_t* nonce_out = out_d + (size_t)nonce_idx * n_leaves * LEAF_BYTES;
    for (int k = 0; k < LEAVES_PER_CALL; k++) {
        uint32_t leaf_idx = call_idx * LEAVES_PER_CALL + k;
        if (leaf_idx >= n_leaves) break;
        uint8_t* dst = nonce_out + leaf_idx * LEAF_BYTES;
        const uint8_t* src = digest + k * LEAF_BYTES;
        for (int b = 0; b < LEAF_BYTES; b++) dst[b] = src[b];
    }
}

int main(int argc, char** argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <input_hex_81b> <nonces_hex_Nx64> <n_nonces> [gpu_id]\n", argv[0]);
        fprintf(stderr, "Output: binary leaves to stdout (n_nonces * 131072 * 12 bytes)\n");
        return 1;
    }

    uint8_t input[I_LEN];
    int n_nonces = atoi(argv[3]);
    int gpu_id = (argc >= 5) ? atoi(argv[4]) : 0;

    // Decode input hex
    if ((int)strlen(argv[1]) != I_LEN * 2) {
        fprintf(stderr, "Error: input must be %d hex bytes\n", I_LEN);
        return 1;
    }
    for (int i = 0; i < I_LEN; i++) {
        unsigned int byte;
        sscanf(argv[1] + i*2, "%02x", &byte);
        input[i] = (uint8_t)byte;
    }

    if (n_nonces <= 0 || n_nonces > 1024) {
        fprintf(stderr, "Error: n_nonces must be 1..1024\n");
        return 1;
    }

    // Decode nonces — use per-byte sscanf to avoid length check issues
    uint8_t* nonces = (uint8_t*)malloc(n_nonces * NONCE_LEN);
    const char* nonces_hex = argv[2];
    size_t expected_len = (size_t)n_nonces * NONCE_LEN * 2;
    if (strlen(nonces_hex) < expected_len) {
        fprintf(stderr, "Error: nonces_hex too short: got %zu chars, need %zu\n",
                strlen(nonces_hex), expected_len);
        free(nonces);
        return 1;
    }
    for (int i = 0; i < n_nonces; i++) {
        for (int j = 0; j < NONCE_LEN; j++) {
            unsigned int byte;
            if (sscanf(nonces_hex + i * NONCE_LEN * 2 + j * 2, "%02x", &byte) != 1) {
                fprintf(stderr, "Error: bad nonce hex at nonce %d byte %d\n", i, j);
                free(nonces);
                return 1;
            }
            nonces[i * NONCE_LEN + j] = (uint8_t)byte;
        }
    }

    cudaSetDevice(gpu_id);

    uint32_t n_leaves = N_LEAVES;
    size_t out_size = (size_t)n_nonces * n_leaves * LEAF_BYTES;

    uint8_t *d_input, *d_nonces, *d_out;
    cudaMalloc(&d_input, I_LEN);
    cudaMalloc(&d_nonces, n_nonces * NONCE_LEN);
    cudaMalloc(&d_out, out_size);

    cudaMemcpy(d_input, input, I_LEN, cudaMemcpyHostToDevice);
    cudaMemcpy(d_nonces, nonces, n_nonces * NONCE_LEN, cudaMemcpyHostToDevice);

    uint32_t n_calls = (n_leaves + LEAVES_PER_CALL - 1) / LEAVES_PER_CALL;
    uint32_t total_threads = n_nonces * n_calls;
    int threads_per_block = 256;
    int blocks = (total_threads + threads_per_block - 1) / threads_per_block;

    gen_leaves_batch_kernel<<<blocks, threads_per_block>>>(d_input, d_nonces, d_out, n_nonces, n_leaves);
    cudaDeviceSynchronize();

    uint8_t* h_out = (uint8_t*)malloc(out_size);
    cudaMemcpy(h_out, d_out, out_size, cudaMemcpyDeviceToHost);
    fwrite(h_out, 1, out_size, stdout);
    fflush(stdout);

    free(h_out);
    free(nonces);
    cudaFree(d_input);
    cudaFree(d_nonces);
    cudaFree(d_out);

    return 0;
}
