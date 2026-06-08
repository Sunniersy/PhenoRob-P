import { defineStore } from "pinia";

const MAX_SEEN_EVENTS = 200;

export const useNotificationStore = defineStore("notifications", {
  state: () => ({
    connected: false,
    recent: [],
    seenEventIds: new Set(),
    taskUpdates: {},
    robotStates: {},
    robotHeartbeats: {},
    analysisByTask: {},
    robotCommands: {}
  }),
  actions: {
    markConnected(value) {
      this.connected = value;
    },
    pushEvent(message) {
      if (message.id && this.seenEventIds.has(message.id)) {
        return;
      }
      if (message.id) {
        this.seenEventIds.add(message.id);
        if (this.seenEventIds.size > MAX_SEEN_EVENTS) {
          const first = this.seenEventIds.values().next().value;
          this.seenEventIds.delete(first);
        }
      }
      this.recent.unshift(message);
      this.recent = this.recent.slice(0, 20);
      if (message.event === "task.updated" && message.payload?.task_id) {
        this.taskUpdates[message.payload.task_id] = message.payload;
      }
      if (message.event === "robot.status_changed" && message.payload?.robot_code) {
        this.robotStates[message.payload.robot_code] = message.payload.payload || {};
      }
      if (message.event === "robot.heartbeat" && message.payload?.robot_code) {
        this.robotHeartbeats[message.payload.robot_code] = {
          ...(message.payload.payload || {}),
          timestamp: message.timestamp
        };
        this.robotStates[message.payload.robot_code] = {
          ...(this.robotStates[message.payload.robot_code] || {}),
          ...(message.payload.payload || {})
        };
      }
      if (message.event === "analysis.finished" && message.payload?.task_id) {
        this.analysisByTask[message.payload.task_id] = message.payload;
      }
      if (message.event === "robot.command_updated" && message.payload?.robot_id) {
        const list = this.robotCommands[message.payload.robot_id] || [];
        const next = [message.payload, ...list.filter((item) => item.id !== message.payload.id)].slice(0, 12);
        this.robotCommands[message.payload.robot_id] = next;
      }
    }
  }
});
