#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

struct pingdata_s
{
    float rtt1, rtt2, rtt3;
    uint8_t dst_addr_1, dst_addr_2, dst_addr_3, dst_addr_4;
    uint8_t src_addr_1, src_addr_2, src_addr_3, src_addr_4;
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
        printf("%d.%d.%d.%d|%d.%d.%d.%d|%f|%f|%f\n\n", 
            pingdata.dst_addr_1, pingdata.dst_addr_2, pingdata.dst_addr_3, pingdata.dst_addr_4, 
            pingdata.src_addr_1, pingdata.src_addr_2, pingdata.src_addr_3, pingdata.src_addr_4, 
            pingdata.rtt1, pingdata.rtt2, pingdata.rtt3);
    }
}