export function pickDefaultRobotId(currentId, robots) {
  if (currentId && robots.some((robot) => robot.id === currentId)) {
    return currentId;
  }
  return robots[0]?.id || "";
}

export function mergeRealtimeRobotState(robots, robotStates = {}, robotHeartbeats = {}) {
  return robots.map((robot) => {
    const liveState = robotStates[robot.robot_code] || {};
    const heartbeat = robotHeartbeats[robot.robot_code] || {};

    return {
      ...robot,
      status: liveState.status || robot.status,
      last_heartbeat_at: heartbeat.timestamp || robot.last_heartbeat_at,
      battery: heartbeat.battery
    };
  });
}

export function robotToneForStatus(status) {
  if (status === "OFFLINE") return "danger";
  if (status === "IDLE") return "warn";
  if (status === "RUNNING" || status === "BUSY") return "success";
  return "default";
}
