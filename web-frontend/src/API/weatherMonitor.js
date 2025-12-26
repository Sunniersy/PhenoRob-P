import request from '@/utils/request'
// 养分监测
export function getWeaData(){
    return request({
      url: '/greenhouse/data/all',
      method: 'get',
       
      timeout: 1000*600000
    })
  }