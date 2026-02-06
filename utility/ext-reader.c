#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

struct pingdata_s
{
    uint32_t prb_id;
    uint8_t ip1, ip2, ip3, ip4;
    float rtt1, rtt2, rtt3;
};

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    FILE* fp;
    struct pingdata_s buf[10];
    
    fp = fopen(argv[1], "rb");
    fread(buf, sizeof(struct pingdata_s), 10, fp);

    struct pingdata_s pingdata;

    for (int i = 0; i < 10; i++) {
        pingdata = buf[i];
        printf("%d.%d.%d.%d|%d|%f|%f|%f\n", pingdata.ip1, pingdata.ip2, pingdata.ip3, pingdata.ip4, pingdata.prb_id, pingdata.rtt1, pingdata.rtt2, pingdata.rtt3);
    }
}