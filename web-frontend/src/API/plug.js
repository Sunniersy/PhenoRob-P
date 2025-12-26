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

// 根据图片进行超绿检测
export function getCheckedGreenImgByImg(pictureUrl) {
  return request({
    url: '/python/checkGreen',
    method: 'get',
    params: {
      fileUrl: pictureUrl
    },
    timeout: 1000*600
  })
}

// 根据图片进行穴孔检测
export function getCheckedHoleImgByImg(pictureUrl) {
  return request({
    url: '/python/checkHole',
    method: 'get',
    params: {
      fileUrl: pictureUrl
    },
    timeout: 1000*600
  })
}


export function getCheckedGrowthImgByImg(treeId) {
  return request({
    url:'/python/predictGrowPoint',
    method:'get',
    params:{
      treeId
    },
    timeout: 1000*600
  })
}

/*
// 根据图片进行生长点检测
export function getCheckedGrowthImgByImg(pictureUrl) {
  return request({
    url: '/python/predictGrowPoint',
    method: 'get',
    params: {
      fileUrl: pictureUrl
    },
    timeout: 1000*60
  })
}
*/