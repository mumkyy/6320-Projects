#include <stdio.h>
#include <time.h>
#include <stdlib.h>

void finit(int g, float *h){

    for(int i = 0; i<g; i++){
        h[i] = (float) (i  % 10 + 1);
    }
}

void cinit(int g, int *next){
    int *p = malloc(g * sizeof(int));

    for (int i = 0; i < g; i++)          // p = 0, 1, 2, ..., g-1
        p[i] = i;
                       // shuffle p
    for (int i = g - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int tmp = p[i];
        p[i] = p[j];
        p[j] = tmp;
    }

    for (int i = 0; i < g; i++)          // link p[0] -> p[1] -> ... -> p[0]
        next[p[i]] = p[(i + 1) % g];
    free(p);
}

float axpy_32(int n, int stride, float *fin1, float *fin2, float *fin3){
    const float a = 665643;
    float *x = fin1;
    float *y = fin2;
    float *z = fin3;

    for (int i = 0; i < n / stride; i++)
         y[i] = (a * x[i*stride]) + y[i];

    return y[0];
}

float chase(int n, int stride, float *fin1, float *fin2, float *fin3){
    int *next = (int *) fin1;
    int k = 0;
    for (int i = 0; i < n; i++)
         k = next[k];
    return k;
}


int main(int argc, char *argv[]) {
    int n;
    float fout;
    clock_t start;
    float duration;
    int mode;
    int off;
    int stride;
    int trials;
    float *fin1;
    float *fin2;
    float *fin3;
    float (*ffunc)(int, int, float *, float *, float *) = NULL;

    n = atoi(argv[1]);
    mode = atoi(argv[2]);
    off = atoi(argv[3]);
    stride = atoi(argv[4]);
    trials = atoi(argv[5]);

    fout = 0;

    fin1 = aligned_alloc(64, (n + 64) * sizeof(float));
    fin2 = aligned_alloc(64, (n + 64) * sizeof(float));
    fin3 = aligned_alloc(64, (n + 64) * sizeof(float));

    finit(n+64,fin1);
    finit(n+64,fin2);
    finit(n+64,fin3);


    switch (mode) {
        case 0:
            ffunc = axpy_32;
            break;
        case 1:
            cinit(n, (int *) fin1);   // random chain
            ffunc = chase;
            break;
        default:
            return 0;
    }

    start = clock();
    for (int j = 0; j < trials; j++){    
        fout = ffunc(n, stride, fin1 + off, fin2 + off, fin3 + off);
    }
    duration = ((float)(clock() - start) / CLOCKS_PER_SEC) / trials;
    printf("%.9f\n", duration);

    free(fin1); 
    free(fin2); 
    free(fin3);
    return (int) (fout);
}
