import request from "@/utils/robotRequest";

export function control_robot(data) {
    return request({
        url: '/api/argi_robot/control_robot',
        method: 'post',
        data
    })
}
export function map_robot(data) {
    return request({
        url: '/api/argi_robot/map_robot',
        method: 'post',
        responseType: 'blob',
        data
    })
}
export function state_robot(data) {
    return request({
        url: '/api/argi_robot/information_robot',
        method: 'post',
        data
    })
}
