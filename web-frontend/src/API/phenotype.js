import request from '@/utils/request';

// 查询树节点上的文件列表
export function listFile(query) {
  return request({
    url: '/system/file/list',
    method: 'get',
    params: query
  });
}


// 根据文件url获取文件内容
export function getFileContent(fileUrl) {
  return request({
    baseURL: `${import.meta.env.VITE_APP_UPLOAD_URL}/csv/${fileUrl}`,
    method: 'get',
    responseType: 'arraybuffer'
  });
}



// 新增树节点上的文件
export function addFile(data) {
  data.fileStatus = data.fileStatus ? 1 : 0;
  return request({
    url: '/system/file',
    method: 'post',
    data
  });
}

// 修改树节点上的文件
export function updateFile(data) {
  data.fileStatus = data.fileStatus ? 1 : 0;
  return request({
    url: '/system/file',
    method: 'put',
    data
  });
}

// 删除树节点上的文件
export function delFile(fileId) {
  return request({
    url: '/system/file/' + fileId,
    method: 'delete'
  });
}

//发送文件
export function getNewFiles(){
  return request({
    url:'/system/file/prcess',
    method:'get'
  })
}
