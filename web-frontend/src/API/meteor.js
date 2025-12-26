import request from '@/utils/request'
// 详细数据echarts展示
export function getChartData(){
    return request({
      url: '/greenhouse/data/all',
      method: 'get', 
      timeout: 1000*600000
    })
  }
  export function getHunidityData(params){
    return request({
      url: '/greenhouse/data/ambientHumidity',
      method: 'post',
      data:params, 
      timeout: 1000*600000

    })
  }
  export function getTempData(params){
    return request({
      url: '/greenhouse/data/ambientTemperature',
      method: 'post',
      data:params, 
      timeout: 1000*600000
    })
  }
  export function getCoData(params){
    return request({
      url: '/greenhouse/data/CO2',
      method: 'post',
      data:params, 
      timeout: 1000*600000
    })
  }
  export function getLightData(params){
    return request({
      url: '/greenhouse/data/lightIntensity',
      method: 'post',
      data:params, 
      timeout: 1000*600000
    })
  }
  export function getLightDataByTime(i){
    return request({
      url: '/greenhouse/data/lightIntensityTime',
      method: 'get', 
      params: {
        i
      },
      timeout: 1000*600000
    })
  }
  export function getHunidityDataByTime(i){
    return request({
      url: '/greenhouse/data/ambientHumidityTime',
      method: 'get', 
      params: {
        i
      },
      timeout: 1000*600000
    })
  }
  export function getTempDataByTime(i){
    return request({
      url: '/greenhouse/data/ambientTemperatureTime',
      method: 'get', 
      params: {
        i
      },
      timeout: 1000*600000
    })
  }
  export function getCoDataByTime(i){
    return request({
      url: '/greenhouse/data/CO2Time',
      method: 'get', 
      params: {
        i
      },
      timeout: 1000*600000
    })
  }