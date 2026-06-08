export const TaskStatus = {
  PENDING_DISPATCH: "PENDING_DISPATCH",
  DISPATCHED: "DISPATCHED",
  ROBOT_ACKED: "ROBOT_ACKED",
  RUNNING: "RUNNING",
  DATA_UPLOADING: "DATA_UPLOADING",
  ANALYZING: "ANALYZING",
  CANCELLING: "CANCELLING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
};

export const TaskStatusMeta = {
  [TaskStatus.PENDING_DISPATCH]: { label: "待下发", tone: "neutral" },
  [TaskStatus.DISPATCHED]: { label: "已下发", tone: "info" },
  [TaskStatus.ROBOT_ACKED]: { label: "机器人已确认", tone: "info" },
  [TaskStatus.RUNNING]: { label: "执行中", tone: "active" },
  [TaskStatus.DATA_UPLOADING]: { label: "数据上传中", tone: "active" },
  [TaskStatus.ANALYZING]: { label: "分析中", tone: "active" },
  [TaskStatus.CANCELLING]: { label: "取消中", tone: "warning" },
  [TaskStatus.COMPLETED]: { label: "已完成", tone: "success" },
  [TaskStatus.FAILED]: { label: "失败", tone: "error" },
};
