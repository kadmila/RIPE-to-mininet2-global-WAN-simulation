#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define BUFFER_SIZE (16 * 1024 * 1024)
#define MAX_LINE_SIZE (4 * 1024)

static inline int extract_all(char* line, char** val1, char** val2, char** val3) {
    char* p = line;

    while (1) {
        if (p[0] == 't' && p[1] == '_' && p[2] == 'a') {
            p = *val1 = p + 9;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    while (1) {
        if (p[0] == ',') {
            p[-1] = 0;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    while (1) {
        if (p[0] == 'u' && p[1] == 'l' && p[2] == 't') {
            p = *val2 = p + 5;
            break;
        }
        
        p++;
        if (*p == 0) {
            return -1;
        }
    }
    
    while (1) {
        if (p[-2] == ']' && p[-1] == ',') {
            p[-1] = 0;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    while (1) {
        if (p[0] == 'b' && p[1] == '_' && p[2] == 'i') {
            p = *val3 = p + 6;
            break;
        }
        
        p++;
        if (*p == 0) {
            return -1;
        }
    }
    
    while (1) {
        if (p[0] == ',') {
            p[0] = 0;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    return 0;
}

static inline int extract_three_rtt(char *line, char **rtt1, char **rtt2, char **rtt3) {
    char *p = line;

    while (1) {
        if (p[0] == 'r' && p[1] == 't' && p[2] == 't' && p[3] == '"' && p[4] == ':') {
            p = *rtt1 = p + 5;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }
    while (1) {
        if (p[-1] == '}' || p[-1] == ',') {
            p[-1] = 0;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    while (1) {
        if (p[0] == 'r' && p[1] == 't' && p[2] == 't' && p[3] == '"' && p[4] == ':') {
            p = *rtt2 = p + 5;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }
    while (1) {
        if (p[-1] == '}' || p[-1] == ',') {
            p[-1] = 0;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    while (1) {
        if (p[0] == 'r' && p[1] == 't' && p[2] == 't' && p[3] == '"' && p[4] == ':') {
            p = *rtt3 = p + 5;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }
    while (1) {
        if (p[-1] == '}' || p[-1] == ',') {
            p[-1] = 0;
            break;
        }

        p++;
        if (*p == 0) {
            return -1;
        }
    }

    return 0;
}

static inline int check_ipv6(const char* val1) {
    char* p = (char*)val1;
    while (*p) {
        if (*p == ':') {
            return -1;
        }
        p++;
    }
    return 0;
}

static inline int check_unexpected_string(const char* rtt) {
    return *rtt == '"';
}

struct pingdata_s
{
    uint32_t prb_id;
    uint8_t ip1, ip2, ip3, ip4;
    float rtt1, rtt2, rtt3;
};

static inline int parse_ipv4(const char *ip_str, struct pingdata_s *dest) {
    char *endptr;
    long val;

    // Parse first octet
    val = strtol(ip_str, &endptr, 10);
    if (endptr == ip_str || val < 0 || val > 255) return -1;
    dest->ip1 = (uint8_t)val;
    
    // Parse second octet
    val = strtol(endptr + 1, &endptr, 10);
    if (*endptr != '.' || val < 0 || val > 255) return -1;
    dest->ip2 = (uint8_t)val;
    
    // Parse third octet
    val = strtol(endptr + 1, &endptr, 10);
    if (*endptr != '.' || val < 0 || val > 255) return -1;
    dest->ip3 = (uint8_t)val;
    
    // Parse fourth octet
    val = strtol(endptr + 1, &endptr, 10);
    if (*endptr != '\0' || val < 0 || val > 255) return -1;
    dest->ip4 = (uint8_t)val;
    
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
    char *val1, *val2, *val3;
    char *rtt1, *rtt2, *rtt3;
    struct pingdata_s pingdata;
    
    char *dump; //strtoul ignore

    while (fgets(line, MAX_LINE_SIZE, stdin)) {
        //printf("%s", line);
        if(extract_all(line, &val1, &val2, &val3)) continue;
        if(extract_three_rtt(val2, &rtt1, &rtt2, &rtt3)) continue;
        if(check_ipv6(val1)) continue;
        if(check_unexpected_string(rtt1) || check_unexpected_string(rtt2) || check_unexpected_string(rtt3)) continue;
        if(parse_ipv4(val1, &pingdata)) continue;
        pingdata.prb_id = strtoul(val3, &dump, 10);
        pingdata.rtt1 = strtof(rtt1, &dump);
        pingdata.rtt2 = strtof(rtt2, &dump);
        pingdata.rtt3 = strtof(rtt3, &dump);

        //fprintf(wfp, "%s|%s|%s|%s|%s\n", val1, val3, rtt1, rtt2, rtt3);
        //printf(">>%d.%d.%d.%d|%d|%f|%f|%f\n\n", pingdata.ip1, pingdata.ip2, pingdata.ip3, pingdata.ip4, pingdata.prb_id, pingdata.rtt1, pingdata.rtt2, pingdata.rtt3);
        fwrite(&pingdata, sizeof(struct pingdata_s), 1, wfp);
        //fprintf(wfp, "%s|%s|%s|%s|%s\n", val1, val3, rtt1, rtt2, rtt3);
    }
    
    fclose(wfp);
    free(file_buffer);
    
    return 0;

FAIL:
    if(wfp) fclose(wfp);
    if(file_buffer) free(file_buffer);
    
    return 1;
}