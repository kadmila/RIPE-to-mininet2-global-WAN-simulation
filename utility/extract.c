#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define BUFFER_SIZE (16 * 1024 * 1024)
#define MAX_LINE_SIZE (4 * 1024)

// "dst_addr":"
static const char str_dst_addr[] = "\"dst_addr\":\"";
static const size_t len_dst_addr = sizeof(str_dst_addr) - 1;

// "result":[
static const char str_result[] = "\"result\":[";
static const size_t len_result = sizeof(str_result) - 1;

// {"rtt":
static const char str_rtt[] = "{\"rtt\":";
static const size_t len_rtt = sizeof(str_rtt) - 1;

// "prb_id":
static const char str_prb_id[] = "\"prb_id\":";
static const size_t len_prb_id = sizeof(str_prb_id) - 1;

static inline int iter_search(char* line, const char* target, int target_len, char stop, char** next_out) {
    char* p = line;
    while (1) {
        if (*p == 0 || *p == stop) return -1;
        if (strncmp(p, target, target_len) == 0) {
            *next_out = p + target_len;
            return 0;
        }
        p++;
    }
}

static inline int iter_search_single(char* line, char target, char stop, char** next_out) {
    char* p = line;
    while (1) {
        if (*p == 0 || *p == stop) return -1;
        if (*p == target) {
            *next_out = p + 1;
            return 0;
        }
        p++;
    }
}

static inline int extract_all(char* line, char** dst_addr_1, char** dst_addr_2, char** dst_addr_3, char** dst_addr_4, char **rtt1, char **rtt2, char **rtt3, char** prb_id) {
    char* p = line;

    if (iter_search(p, str_dst_addr, len_dst_addr, 0, &p)) return -1;
    *dst_addr_1 = p;
    if (iter_search_single(p, '.', '"', &p)) return -1;
    p[-1] = 0;
    *dst_addr_2 = p;
    if (iter_search_single(p, '.', '"', &p)) return -1;
    p[-1] = 0;
    *dst_addr_3 = p;
    if (iter_search_single(p, '.', '"', &p)) return -1;
    p[-1] = 0;
    *dst_addr_4 = p;
    if (iter_search_single(p, '"', 0, &p)) return -1;
    p[-1] = 0;

    if (iter_search(p, str_result, len_result, 0, &p)) return -1;
    if (iter_search(p, str_rtt, len_rtt, ']', &p)) return -1;
    *rtt1 = p;
    if (iter_search_single(p, '}', ',', &p)) return -1;
    p[-1] = 0;
    if (iter_search(p, str_rtt, len_rtt, ']', &p)) return -1;
    *rtt2 = p;
    if (iter_search_single(p, '}', ',', &p)) return -1;
    p[-1] = 0;
    if (iter_search(p, str_rtt, len_rtt, ']', &p)) return -1;
    *rtt3 = p;
    if (iter_search_single(p, '}', ',', &p)) return -1;
    p[-1] = 0;

    if (iter_search(p, str_prb_id, len_prb_id, 0, &p)) return -1;
    *prb_id = p;
    if (iter_search_single(p, ',', '"', &p)) return -1;
    p[-1] = 0;

    return 0;
}

struct pingdata_s
{
    uint32_t prb_id;
    uint8_t ip1, ip2, ip3, ip4;
    float rtt1, rtt2, rtt3;
};

static inline int parse_pingdata(struct pingdata_s *dst, const char *dst_addr_1, const char *dst_addr_2, const char *dst_addr_3, const char *dst_addr_4, const char *rtt1, const char *rtt2, const char *rtt3, const char *prb_id) {
    char *endptr;
    long v_l;
    float v_f;
    
    v_l = strtol(dst_addr_1, &endptr, 10);
    if (endptr == dst_addr_1 || *endptr != 0 || v_l < 0 || v_l > 255) return -1;
    dst->ip1 = (uint8_t)v_l;
    
    v_l = strtol(dst_addr_2, &endptr, 10);
    if (endptr == dst_addr_2 || *endptr != 0 || v_l < 0 || v_l > 255) return -1;
    dst->ip2 = (uint8_t)v_l;
    
    v_l = strtol(dst_addr_3, &endptr, 10);
    if (endptr == dst_addr_3 || *endptr != 0 || v_l < 0 || v_l > 255) return -1;
    dst->ip3 = (uint8_t)v_l;
    
    v_l = strtol(dst_addr_4, &endptr, 10);
    if (endptr == dst_addr_4 || *endptr != 0 || v_l < 0 || v_l > 255) return -1;
    dst->ip4 = (uint8_t)v_l;

    v_f = strtof(rtt1, &endptr);
    if (endptr == rtt1 || *endptr != 0 || v_f < 0.0f) return -1;
    dst->rtt1 = v_f;

    v_f = strtof(rtt2, &endptr);
    if (endptr == rtt2 || *endptr != 0 || v_f < 0.0f) return -1;
    dst->rtt2 = v_f;

    v_f = strtof(rtt3, &endptr);
    if (endptr == rtt3 || *endptr != 0 || v_f < 0.0f) return -1;
    dst->rtt3 = v_f;

    v_l = strtol(prb_id, &endptr, 10);
    if (endptr == prb_id || *endptr != 0 || v_l < 0) return -1;
    dst->prb_id = v_l;

    return 0;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }
    
    FILE* wfp;
    char* file_buffer;

    wfp = fopen(argv[1], "wb");
    if (!wfp) {
        perror("Failed to open file");
        goto FAIL;
    }

    file_buffer = malloc(BUFFER_SIZE);
    if (!file_buffer) {
        perror("failed to allocate buffer");
        goto FAIL;
    }
    
    char line[MAX_LINE_SIZE+1];
    line[MAX_LINE_SIZE] = 0;
    char *dst_addr_1, *dst_addr_2, *dst_addr_3, *dst_addr_4, *rtt1, *rtt2, *rtt3, *prb_id;
    struct pingdata_s pingdata;
    
    char *dump; //strtoul ignore

    while (fgets(line, MAX_LINE_SIZE, stdin)) {
        //printf("%s", line);

        if (extract_all(line, &dst_addr_1, &dst_addr_2, &dst_addr_3, &dst_addr_4, &rtt1, &rtt2, &rtt3, &prb_id)) continue;
        if (parse_pingdata(&pingdata, dst_addr_1, dst_addr_2, dst_addr_3, dst_addr_4, rtt1, rtt2, rtt3, prb_id)) continue;

        //printf(">>>>>%d.%d.%d.%d|%d|%f|%f|%f\n\n", pingdata.ip1, pingdata.ip2, pingdata.ip3, pingdata.ip4, pingdata.prb_id, pingdata.rtt1, pingdata.rtt2, pingdata.rtt3);
        fwrite(&pingdata, sizeof(struct pingdata_s), 1, wfp);
    }
    
    fclose(wfp);
    free(file_buffer);
    
    return 0;

FAIL:
    if(wfp) fclose(wfp);
    if(file_buffer) free(file_buffer);
    
    return 1;
}