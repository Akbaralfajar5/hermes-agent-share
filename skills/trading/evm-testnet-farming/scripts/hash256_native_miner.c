/*
 * $HASH Native CPU Miner - keccak256 brute force
 * Compile: gcc -O3 -march=native -o hash-miner-native hash256_native_miner.c -lpthread
 * Usage: ./hash-miner-native <challenge_hex> <difficulty_hex> <num_workers>
 * Output: prints RESULT_NONCE=0x... when found (parse this from Node.js wrapper)
 *
 * Hashrate: ~10 MH/s on 64 cores (vs ~1.7 MH/s Node.js, ~95 MH/s browser WASM)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>

// ─── Keccak-256 (NOT SHA3-256 - different padding 0x01 vs 0x06) ──────────────
#define KECCAK_ROUNDS 24
static const uint64_t keccak_rc[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL, 0x800000000000808aULL,
    0x8000000080008000ULL, 0x000000000000808bULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL, 0x000000000000008aULL,
    0x0000000000000088ULL, 0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL, 0x8000000000008089ULL,
    0x8000000000008003ULL, 0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800aULL, 0x800000008000000aULL, 0x8000000080008081ULL,
    0x8000000000008080ULL, 0x0000000080000001ULL, 0x8000000080008008ULL
};
static const int rho[24] = {
    1,  3,  6, 10, 15, 21, 28, 36, 45, 55,  2, 14,
    27, 41, 56,  8, 25, 43, 62, 18, 39, 61, 20, 44
};
static const int pi[24] = {
    10,  7, 11, 17, 18,  3,  5, 16,  8, 21, 24,  4,
    15, 23, 19, 13, 12,  2, 20, 14, 22,  9,  6,  1
};

static inline uint64_t rotl64(uint64_t x, int n) {
    return (x << n) | (x >> (64 - n));
}

static void keccakf(uint64_t st[25]) {
    uint64_t t, bc[5];
    for (int r = 0; r < KECCAK_ROUNDS; r++) {
        for (int i = 0; i < 5; i++)
            bc[i] = st[i] ^ st[i+5] ^ st[i+10] ^ st[i+15] ^ st[i+20];
        for (int i = 0; i < 5; i++) {
            t = bc[(i+4)%5] ^ rotl64(bc[(i+1)%5], 1);
            for (int j = 0; j < 25; j += 5) st[j+i] ^= t;
        }
        t = st[1];
        for (int i = 0; i < 24; i++) {
            int j = pi[i];
            bc[0] = st[j];
            st[j] = rotl64(t, rho[i]);
            t = bc[0];
        }
        for (int j = 0; j < 25; j += 5) {
            for (int i = 0; i < 5; i++) bc[i] = st[j+i];
            for (int i = 0; i < 5; i++) st[j+i] ^= (~bc[(i+1)%5]) & bc[(i+2)%5];
        }
        st[0] ^= keccak_rc[r];
    }
}

static void keccak256(const uint8_t *in, size_t inlen, uint8_t *out) {
    uint64_t st[25] = {0};
    uint8_t temp[136];
    size_t rsiz = 136;
    while (inlen >= rsiz) {
        for (size_t i = 0; i < rsiz/8; i++)
            st[i] ^= ((uint64_t*)in)[i];
        keccakf(st);
        in += rsiz; inlen -= rsiz;
    }
    memcpy(temp, in, inlen);
    temp[inlen++] = 0x01; // Keccak padding (NOT SHA3's 0x06)
    memset(temp + inlen, 0, rsiz - inlen);
    temp[rsiz-1] |= 0x80;
    for (size_t i = 0; i < rsiz/8; i++)
        st[i] ^= ((uint64_t*)temp)[i];
    keccakf(st);
    memcpy(out, st, 32);
}

// ─── Worker ──────────────────────────────────────────────────────────────────
#define MAX_WORKERS 128

typedef struct {
    uint8_t  challenge[32];
    uint8_t  difficulty[32];
    uint64_t nonce_start;
    uint64_t nonce_step;
    int      worker_id;
    int      found;
    uint64_t nonce_found;
    uint64_t hashes;
} WorkerArgs;

static volatile int global_found = 0;
static uint64_t global_nonce = 0;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

static inline int bytes32_lt(const uint8_t *a, const uint8_t *b) {
    for (int i = 0; i < 32; i++) {
        if (a[i] < b[i]) return 1;
        if (a[i] > b[i]) return 0;
    }
    return 0;
}

static void *worker_thread(void *arg) {
    WorkerArgs *w = (WorkerArgs*)arg;
    uint8_t input[64];
    uint8_t hash[32];
    memcpy(input, w->challenge, 32);
    uint64_t nonce = w->nonce_start;
    uint64_t count = 0;
    while (!global_found) {
        memset(input + 32, 0, 24);
        input[56] = (nonce >> 56) & 0xff;
        input[57] = (nonce >> 48) & 0xff;
        input[58] = (nonce >> 40) & 0xff;
        input[59] = (nonce >> 32) & 0xff;
        input[60] = (nonce >> 24) & 0xff;
        input[61] = (nonce >> 16) & 0xff;
        input[62] = (nonce >>  8) & 0xff;
        input[63] = (nonce      ) & 0xff;
        keccak256(input, 64, hash);
        count++;
        if (bytes32_lt(hash, w->difficulty)) {
            pthread_mutex_lock(&mutex);
            if (!global_found) {
                global_found = 1;
                global_nonce = nonce;
                printf("\n[FOUND] nonce=0x%016llx hashes=%llu\n",
                       (unsigned long long)nonce, (unsigned long long)count);
                fflush(stdout);
            }
            pthread_mutex_unlock(&mutex);
            break;
        }
        nonce += w->nonce_step;
        if (count % 1000000 == 0 && w->worker_id == 0) {
            pthread_mutex_lock(&mutex);
            printf("\r  [W0] %llu MH searched...", (unsigned long long)(count/1000000));
            fflush(stdout);
            pthread_mutex_unlock(&mutex);
        }
    }
    w->hashes = count;
    w->found = global_found;
    w->nonce_found = global_nonce;
    return NULL;
}

static void hex2bytes(const char *hex, uint8_t *out, int len) {
    if (hex[0] == '0' && (hex[1] == 'x' || hex[1] == 'X')) hex += 2;
    for (int i = 0; i < len; i++)
        sscanf(hex + 2*i, "%2hhx", &out[i]);
}

static void bytes2hex(const uint8_t *in, int len, char *out) {
    for (int i = 0; i < len; i++)
        sprintf(out + 2*i, "%02x", in[i]);
    out[2*len] = 0;
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <challenge_hex> <difficulty_hex> <num_workers>\n", argv[0]);
        return 1;
    }
    uint8_t challenge[32], difficulty[32];
    hex2bytes(argv[1], challenge, 32);
    hex2bytes(argv[2], difficulty, 32);
    int num_workers = atoi(argv[3]);
    if (num_workers < 1) num_workers = 1;
    if (num_workers > MAX_WORKERS) num_workers = MAX_WORKERS;

    char chex[65], dhex[65];
    bytes2hex(challenge, 32, chex);
    bytes2hex(difficulty, 32, dhex);
    printf("Challenge : 0x%.16s...\n", chex);
    printf("Difficulty: 0x%.16s...\n", dhex);
    printf("Workers   : %d\n\n", num_workers);

    pthread_t threads[MAX_WORKERS];
    WorkerArgs args[MAX_WORKERS];
    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (int i = 0; i < num_workers; i++) {
        memcpy(args[i].challenge, challenge, 32);
        memcpy(args[i].difficulty, difficulty, 32);
        args[i].nonce_start = (uint64_t)i;
        args[i].nonce_step  = (uint64_t)num_workers;
        args[i].worker_id   = i;
        args[i].found = 0; args[i].nonce_found = 0; args[i].hashes = 0;
        pthread_create(&threads[i], NULL, worker_thread, &args[i]);
    }
    for (int i = 0; i < num_workers; i++)
        pthread_join(threads[i], NULL);

    struct timespec t1;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    uint64_t total_hashes = 0;
    for (int i = 0; i < num_workers; i++) total_hashes += args[i].hashes;

    printf("Elapsed   : %.2f s\n", elapsed);
    printf("Total hash: %llu M\n", (unsigned long long)(total_hashes / 1000000));
    printf("Hashrate  : %.2f MH/s\n", total_hashes / elapsed / 1e6);
    printf("Nonce     : 0x%016llx\n", (unsigned long long)global_nonce);
    printf("RESULT_NONCE=0x%016llx\n", (unsigned long long)global_nonce);
    return 0;
}
