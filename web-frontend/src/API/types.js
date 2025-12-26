import request from '@/utils/request';

export function addImages(imageList) {
  return request({
    url: '/image/addImages',
    method: 'post',
  });
}

export function getImagesBynodeId(treeId) {
  return request({
    url: 'system/picture/list',
    method: 'get',
    params: {
      treeId
    }
  });
}

export function deleteImageByIdAndUrl(pictureId,pictureUrl) {
  return request({
    url: '/system/picture/remove',
    method: 'get',
    params: {
      pictureId,
      pictureUrl
    }
  });
}

//自动上传接口
export function updateByIp(ip,parentFile,treeId){
  return request({
    url:'/system/picture/uploadByIp',
    method:'post',
    params:{
      ip,
      parentFile,
      treeId
    }
  })
}

//图片数据统计接口
export function treeCount(treeId){
  return request({
    url:'/system/picture/count',
    method:'get',
    params:{
      treeId
    }
  })
}
