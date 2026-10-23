#include <stdio.h>
#include <time.h>
#include <stdlib.h>

void finit(int g, float *h){

    for(int i = 0; i<g; i++){
        h[i] = (float) (i  % 10 + 1);
    }
}

void dinit(int g, double *h){

    for(int i = 0; i<g; i++){
        h[i] = (double) (i  % 10 + 1);
    }

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

double axpy_64(int n, int stride, double *din1, double *din2, double *din3){
    const double a = 665643;
    double *x = din1;
    double *y = din2;
    double *z = din3;

    for (int i = 0; i < n / stride; i++)
         y[i] = (a * x[i*stride]) + y[i];

    return y[0];
}


float dp_32(int n, int stride, float *fin1, float *fin2, float *fin3){
    float *x = fin1;
    float *y = fin2;
    float *z = fin3;
    float s;

    s = 0;

    for (int i = 0; i < n / stride; i++)
         s += y[i*stride] * x[i*stride];

    return s;
}


double dp_64(int n, int stride, double *din1, double *din2, double *din3){
    double *x = din1;
    double *y = din2;
    double *z = din3;
    double s;

    s=0;
    for (int i = 0; i < n / stride; i++)
         s += y[i*stride] * x[i*stride];

    return s;
}


float em_32(int n, int stride, float *fin1, float *fin2, float *fin3){
    float *x = fin1;
    float *y = fin2;
    float *z = fin3;

    for (int i = 0; i < n / stride; i++)
         z[i*stride] = y[i*stride] * x[i*stride];

    return z[0]; 
}

double em_64(int n, int stride, double *din1, double *din2, double *din3){
    double *x = din1;
    double *y = din2;
    double *z = din3;

    for (int i = 0; i < n / stride; i++)
         z[i*stride] = y[i*stride] * x[i*stride];

    return z[0];
}

float peak_32(int n, int stride, float *fin1, float *fin2, float *fin3){
    float *x = fin1;
    const float a = 0.999999f, b = 0.000001f;

    for (int r = 0; r < n; r++)
        for (int i = 0; i < 64; i++)
            x[i] = x[i] * a + b;

    return x[0];
}

void verify(int n, float *fx, float *fy, float *fz, double *dx, double *dy, double *dz){
    double sum;

    axpy_32(n, 1, fx, fy, fz);
    sum = 0; for (int i = 0; i < n; i++) sum += fy[i];
    printf("axpy float  %f\n", sum);

    axpy_64(n, 1, dx, dy, dz);
    sum = 0; for (int i = 0; i < n; i++) sum += dy[i];
    printf("axpy double %f\n", sum);

    printf("dot  float  %f\n", dp_32(n, 1, fx, fy, fz));
    printf("dot  double %f\n", dp_64(n, 1, dx, dy, dz));

    em_32(n, 1, fx, fy, fz);
    sum = 0; for (int i = 0; i < n; i++) sum += fz[i];
    printf("mul  float  %f\n", sum);

    em_64(n, 1, dx, dy, dz);
    sum = 0; for (int i = 0; i < n; i++) sum += dz[i];
    printf("mul  double %f\n", sum);
}


int main(int argc, char *argv[]) {
    int n;
    float fout;
    double dout;
    clock_t start;
    float duration;
    int mode;
    int off;
    int stride;
    int trials;
    float *fin1;
    float *fin2;
    float *fin3;
    double *din1;
    double *din2;
    double *din3;
    float (*ffunc)(int, int, float *, float *, float *) = NULL;
    double (*dfunc)(int, int, double *, double *, double *) = NULL;

    n = atoi(argv[1]);
    mode = atoi(argv[2]);
    off = atoi(argv[3]);
    stride = atoi(argv[4]);
    trials = atoi(argv[5]);

    fout = 0;
    dout = 0;

    fin1 = aligned_alloc(64, (n + 64) * sizeof(float));
    fin2 = aligned_alloc(64, (n + 64) * sizeof(float));
    fin3 = aligned_alloc(64, (n + 64) * sizeof(float));

    din1 = aligned_alloc(64, (n + 64) * sizeof(double));
    din2 = aligned_alloc(64, (n + 64) * sizeof(double));
    din3 = aligned_alloc(64, (n + 64) * sizeof(double));

    finit(n+64,fin1);
    finit(n+64,fin2);
    finit(n+64,fin3);

    dinit(n+64,din1);
    dinit(n+64,din2);
    dinit(n+64,din3);

    switch (mode) {
        case 0:
            ffunc = axpy_32;
            break;
        case 1:
            dfunc = axpy_64;
            break;
        case 2:
            ffunc = dp_32;
            break;
        case 3:
            dfunc = dp_64;
            break;
        case 4:
            ffunc = em_32;
            break;
        case 5:
            dfunc = em_64;
            break;

        case 6:
            ffunc = peak_32;
            break;
        case 7:
            verify(n, fin1, fin2, fin3, din1, din2, din3);
            return 0;
        default:
            return 0;
    }

    start = clock();
    for (int j = 0; j < trials; j++){    
        if (ffunc != NULL){
            fout = ffunc(n, stride, fin1 + off, fin2 + off, fin3 + off);
        }
        else if (dfunc != NULL){
           dout = dfunc(n, stride, din1 + off, din2 + off, din3 + off);
        }
    }
    duration = ((float)(clock() - start) / CLOCKS_PER_SEC) / trials;
    printf("%.9f\n", duration);

    free(fin1); 
    free(fin2); 
    free(fin3);
    free(din1); 
    free(din2);
    free(din3);
    return (int) (((double) fout) + dout);
}
