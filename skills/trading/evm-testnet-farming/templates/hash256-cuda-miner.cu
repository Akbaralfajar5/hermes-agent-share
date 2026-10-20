/*
 * $HASH CUDA Miner v2 - keccak256 GPU
 * Verified against ethers.js solidityPackedKeccak256(['bytes32','uint256'])
 *
 * Compile:
 *   RTX 5090: nvcc -O3 -arch=sm_120 -o hash-miner-cuda hash-miner-cuda.cu
 *   RTX 4090: nvcc -O3 -arch=sm_89  -o hash-miner-cuda hash-miner-cuda.cu
 *   RTX 3090: nvcc -O3 -arch=sm_86  -o hash-miner-cuda hash-miner-cuda.cu
 *
 * Usage: ./hash-miner-cuda <challenge_hex> <difficulty_hex> <gpu_id>
 * Output (stdout): FOUND nonce=0x... gpu=N
 * Progress (stderr): GPU0 mining... ~NNN MH/s
 *
 * Run 4 GPUs in parallel:
 *   for i in 0 1 2 3; do ./hash-miner-cuda $CHALLENGE $DIFF $i & done
 *   wait
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <cuda_runtime.h>

__constant__ uint64_t RC[24] = {
    0x0000000000000001ULL,0x0000000000008082ULL,0x800000000000808AULL,
    0x8000000080008000ULL,0x000000000000808BULL,0x0000000080000001ULL,
    0x8000000080008081ULL,0x8000000000008009ULL,0x000000000000008AULL,
    0x0000000000000088ULL,0x0000000080008009ULL,0x000000008000000AULL,
    0x000000008000808BULL,0x800000000000008BULL,0x8000000000008089ULL,
    0x8000000000008003ULL,0x8000000000008002ULL,0x8000000000000080ULL,
    0x000000000000800AULL,0x800000008000000AULL,0x8000000080008081ULL,
    0x8000000000008080ULL,0x0000000080000001ULL,0x8000000080008008ULL
};

#define ROTL64(x,n) (((x)<<(n))|((x)>>(64-(n))))

__device__ __forceinline__ void keccakf1600(uint64_t s[25]) {
    uint64_t bc[5], t;
    #pragma unroll
    for (int i = 0; i < 24; i++) {
        bc[0]=s[0]^s[5]^s[10]^s[15]^s[20];
        bc[1]=s[1]^s[6]^s[11]^s[16]^s[21];
        bc[2]=s[2]^s[7]^s[12]^s[17]^s[22];
        bc[3]=s[3]^s[8]^s[13]^s[18]^s[23];
        bc[4]=s[4]^s[9]^s[14]^s[19]^s[24];

        t=bc[4]^ROTL64(bc[1],1); s[0]^=t;s[5]^=t;s[10]^=t;s[15]^=t;s[20]^=t;
        t=bc[0]^ROTL64(bc[2],1); s[1]^=t;s[6]^=t;s[11]^=t;s[16]^=t;s[21]^=t;
        t=bc[1]^ROTL64(bc[3],1); s[2]^=t;s[7]^=t;s[12]^=t;s[17]^=t;s[22]^=t;
        t=bc[2]^ROTL64(bc[4],1); s[3]^=t;s[8]^=t;s[13]^=t;s[18]^=t;s[23]^=t;
        t=bc[3]^ROTL64(bc[0],1); s[4]^=t;s[9]^=t;s[14]^=t;s[19]^=t;s[24]^=t;

        t=s[1];
        s[1] =ROTL64(s[6], 44); s[6] =ROTL64(s[9], 20); s[9] =ROTL64(s[22],61);
        s[22]=ROTL64(s[14],39); s[14]=ROTL64(s[20],18); s[20]=ROTL64(s[2], 62);
        s[2] =ROTL64(s[12],43); s[12]=ROTL64(s[13],25); s[13]=ROTL64(s[19], 8);
        s[19]=ROTL64(s[23],56); s[23]=ROTL64(s[15],41); s[15]=ROTL64(s[4], 27);
        s[4] =ROTL64(s[24],14); s[24]=ROTL64(s[21], 2); s[21]=ROTL64(s[8], 55);
        s[8] =ROTL64(s[16],45); s[16]=ROTL64(s[5], 36); s[5] =ROTL64(s[3], 28);
        s[3] =ROTL64(s[18],21); s[18]=ROTL64(s[17],15); s[17]=ROTL64(s[11],10);
        s[11]=ROTL64(s[7],  6); s[7] =ROTL64(s[10], 3); s[10]=ROTL64(t,    1);

        #pragma unroll
        for(int j=0;j<25;j+=5){
            bc[0]=s[j];bc[1]=s[j+1];bc[2]=s[j+2];bc[3]=s[j+3];bc[4]=s[j+4];
            s[j]  ^=(~bc[1])&bc[2]; s[j+1]^=(~bc[2])&bc[3];
            s[j+2]^=(~bc[3])&bc[4]; s[j+3]^=(~bc[4])&bc[0];
            s[j+4]^=(~bc[0])&bc[1];
        }
        s[0]^=RC[i];
    }
}

// keccak256 of exactly 64 bytes (challenge32 + nonce32)
// Input stored as 8 little-endian uint64 (keccak state format)
__device__ __forceinline__ void keccak256_64(
    const uint64_t* __restrict__ in8,
    uint8_t* __restrict__ out32
) {
    uint64_t s[25];
    #pragma unroll
    for(int i=0;i<25;i++) s[i]=0;
    #pragma unroll
    for(int i=0;i<8;i++) s[i]^=in8[i];
    // Keccak-256 padding (NOT SHA3 — use 0x01, not 0x06)
    s[8] ^= 0x0000000000000001ULL;
    s[16]^= 0x8000000000000000ULL;
    keccakf1600(s);
    #pragma unroll
    for(int i=0;i<4;i++){
        uint64_t v=s[i];
        out32[i*8+0]=(v    )&0xff; out32[i*8+1]=(v>> 8)&0xff;
        out32[i*8+2]=(v>>16)&0xff; out32[i*8+3]=(v>>24)&0xff;
        out32[i*8+4]=(v>>32)&0xff; out32[i*8+5]=(v>>40)&0xff;
        out32[i*8+6]=(v>>48)&0xff; out32[i*8+7]=(v>>56)&0xff;
    }
}

__global__ void mine_kernel(
    const uint64_t* __restrict__ challenge8,
    const uint8_t*  __restrict__ difficulty,
    uint64_t nonce_offset,
    uint64_t nonce_stride,
    volatile uint64_t* result_nonce,
    volatile int* found_flag
) {
    uint64_t tid = (uint64_t)blockIdx.x * blockDim.x + threadIdx.x;
    uint64_t nonce = nonce_offset + tid;

    uint64_t input[8];
    #pragma unroll
    for(int i=0;i<4;i++) input[i]=challenge8[i];

    uint8_t hash[32];

    while(!(*found_flag)) {
        // Nonce as big-endian uint256 in bytes 32-63
        // Stored as LE uint64 with byte-swap for keccak input
        input[4] = 0; input[5] = 0; input[6] = 0;
        input[7] = (
            ((nonce & 0xffULL) << 56) |
            (((nonce>>8) & 0xffULL) << 48) |
            (((nonce>>16) & 0xffULL) << 40) |
            (((nonce>>24) & 0xffULL) << 32) |
            (((nonce>>32) & 0xffULL) << 24) |
            (((nonce>>40) & 0xffULL) << 16) |
            (((nonce>>48) & 0xffULL) << 8) |
            ((nonce>>56) & 0xffULL)
        );

        keccak256_64(input, hash);

        bool less = false, eq = true;
        #pragma unroll
        for(int i=0;i<32;i++){
            if(eq){
                if(hash[i]<difficulty[i]){less=true;eq=false;}
                else if(hash[i]>difficulty[i]){eq=false;}
            }
        }

        if(less){
            if(atomicCAS((int*)found_flag,0,1)==0){
                *result_nonce=nonce;
            }
            return;
        }

        nonce += nonce_stride;
    }
}

void hex2bytes(const char *hex, uint8_t *out, int len){
    if(hex[0]=='0'&&(hex[1]=='x'||hex[1]=='X'))hex+=2;
    for(int i=0;i<len;i++) sscanf(hex+2*i,"%2hhx",&out[i]);
}

int main(int argc, char *argv[]){
    if(argc<4){
        fprintf(stderr,"Usage: %s <challenge_hex> <difficulty_hex> <gpu_id>\n",argv[0]);
        return 1;
    }

    uint8_t challenge_bytes[32], difficulty[32];
    hex2bytes(argv[1], challenge_bytes, 32);
    hex2bytes(argv[2], difficulty, 32);
    int gpu_id = atoi(argv[3]);

    cudaSetDevice(gpu_id);
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, gpu_id);
    fprintf(stderr,"GPU%d: %s | %d SMs\n", gpu_id, prop.name, prop.multiProcessorCount);

    // Convert challenge bytes to LE uint64 array
    uint64_t challenge8[4];
    for(int i=0;i<4;i++){
        challenge8[i]=0;
        for(int b=0;b<8;b++)
            challenge8[i] |= ((uint64_t)challenge_bytes[i*8+b]) << (b*8);
    }

    uint64_t *d_challenge8, *d_result;
    uint8_t  *d_difficulty;
    int      *d_found;
    cudaMalloc(&d_challenge8, 32);
    cudaMalloc(&d_difficulty, 32);
    cudaMalloc(&d_result, sizeof(uint64_t));
    cudaMalloc(&d_found, sizeof(int));
    cudaMemcpy(d_challenge8, challenge8, 32, cudaMemcpyHostToDevice);
    cudaMemcpy(d_difficulty, difficulty, 32, cudaMemcpyHostToDevice);
    cudaMemset(d_found, 0, sizeof(int));
    cudaMemset(d_result, 0, sizeof(uint64_t));

    int threads = 256;
    int blocks  = prop.multiProcessorCount * 32;
    uint64_t total_threads = (uint64_t)blocks * threads;
    uint64_t nonce_offset  = (uint64_t)gpu_id * total_threads;
    uint64_t nonce_stride  = 4ULL * total_threads; // assumes 4 GPUs

    fprintf(stderr,"Blocks=%d Threads=%d TotalThreads=%llu Offset=%llu\n",
        blocks, threads,
        (unsigned long long)total_threads,
        (unsigned long long)nonce_offset);
    fflush(stderr);

    mine_kernel<<<blocks,threads>>>(
        d_challenge8, d_difficulty,
        nonce_offset, nonce_stride,
        (volatile uint64_t*)d_result,
        (volatile int*)d_found
    );

    int h_found=0;
    uint64_t h_nonce=0;
    struct timespec ts; ts.tv_sec=0; ts.tv_nsec=5000000;
    uint64_t polls=0;
    while(!h_found){
        nanosleep(&ts,NULL);
        cudaMemcpy(&h_found,d_found,sizeof(int),cudaMemcpyDeviceToHost);
        polls++;
        if(polls%200==0){
            fprintf(stderr,"\rGPU%d mining... ~%.0f MH/s",
                gpu_id, (double)total_threads*200.0/1e6/1.0);
            fflush(stderr);
        }
    }
    cudaMemcpy(&h_nonce,d_result,sizeof(uint64_t),cudaMemcpyDeviceToHost);
    cudaDeviceSynchronize();

    fprintf(stdout,"FOUND nonce=0x%016llx gpu=%d\n",(unsigned long long)h_nonce,gpu_id);
    fflush(stdout);

    cudaFree(d_challenge8); cudaFree(d_difficulty);
    cudaFree(d_result); cudaFree(d_found);
    return 0;
}
