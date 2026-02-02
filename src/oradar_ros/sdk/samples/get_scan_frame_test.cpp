#include <iostream>
#include "ord/ord_driver.h"
#include "ord/lidar_address.h"
#include "ord/ord_types.h"
#include <string.h>
#ifdef __linux__
#include <arpa/inet.h>
#include <unistd.h>
#endif

int main()
{
    printf("this is oradar lidar sdk test demo \n");
    //The default IP of the Lidar is 192.168.1.100, net port is 2007
    in_addr_t ip_addr = inet_addr("192.168.1.100");
    in_port_t port = htons(2007);
    ord_sdk::LidarAddress sensor(ip_addr, port);
    ord_sdk::OrdDriver drv(sensor);
    ord_sdk::ScanFrameData scan_frame_data;
	
	//open device
    if (drv.open() != ord_sdk::no_error){
        std::cerr << "unable to open device" << std::endl;
        return -1;
    }
	//connect device
    if(drv.trackConnect() != ord_sdk::no_error){
        std::cerr << "unable to connect ms500 lidar" << std::endl;
        return -1;
    }
	//enable data stream
	drv.enabelDataStream();

	while (true) {
		//get a circle of point cloud data
        if (drv.GrabFullScanBlocking(scan_frame_data) == ord_sdk::no_error){
            int count =  scan_frame_data.layers[0].ranges.size();
            std::cout << "scan_frame_data count size is " << \
            scan_frame_data.layers[0].ranges.size()  << std::endl;
            std::cout << "scan_frame_data.layers.szie = " << \
            scan_frame_data.layers.size() << std::endl;
            std::cout << "scan_frame_data.layers[0].ranges.szie = " << \
            scan_frame_data.layers[0].ranges.size() << std::endl;
            std::cout << "scan_frame_data.layers[0].intensities.szie = " << \
            scan_frame_data.layers[0].intensities.size() << std::endl;
            std::cout << "timestamp is " << scan_frame_data.timestamp << std::endl;
        }else{
            std::cerr << "unable to get point cloud data\n";
        }
    }
	//close device
    drv.close();
    return 0;
}
