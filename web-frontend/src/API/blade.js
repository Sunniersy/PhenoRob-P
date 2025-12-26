import request from '@/utils/request';

export function getImagesBynodeId(treeId) {
  return request({
    url: 'system/picture/list',
    method: 'get',
    params: {
      treeId
    },
    timeout: 1000*600
  });
}

// 叶片检测
export function getCheckedLeafImgByImg(pictureUrl) {
  return request({
    url: '/python/detectLeaf',
    method: 'get',
    params: {
      fileUrl:pictureUrl
    },
    timeout: 1000*600
  })
}
// 图片检测后的结果保存
export function saveAfterCheck(nodeId, result) {
  return request({
    url: '/identifypre/saveAfterCheck',
    method: 'post',
    data: {
      nodeId,
      result
    }
  })
}
