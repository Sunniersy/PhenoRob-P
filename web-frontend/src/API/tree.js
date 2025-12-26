import request from '@/utils/request';

// 获取整棵树
/* export function getTree(treeType, parentId, isShow) {
  return request({
    url: '/system/tree/list',
    method: 'get',
    params: {
      treeType,
      parentId,
      isShow
    }
  });
} */

export function getTree(treeType,parentId, isShow) {
  return request({
    url: '/system/tree/list',
    method: 'get',
    params: {
      treeType,
      parentId,
      isShow
    }
  });
}

// 删除树节点
export function deleteNodes(treeIds) {
  return request({
    url: '/system/tree/' + treeIds,
    method: 'delete'
  });
}

// 添加树节点
export function addNode(data) {
  return request({
    url: '/system/tree',
    method: 'post',
    data
  });
}

// 更新树节点
export function updateNode(data) {
  return request({
    url: '/system/tree',
    method: 'put',
    data
  })
}