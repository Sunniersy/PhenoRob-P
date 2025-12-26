import request from '@/utils/request'

// 获取表格数据
export function getTableData(treeId) {
  return request({
    url: '/system/file/csvSynthesis',
    method: 'get',
    params: {
      treeId
    },
    timeout: 1000*600000
  })
}

// 生长预测
export function getPredictGrow(params) {
  return request({
    url: '/python/predictGrow',
    method: 'get',
    params,
    timeout: 1000*600000
  })
}
