import { ref } from "vue";

import { tasks as tasksApi } from "../api";

export function useTaskActions(onSuccess) {
  const actionLoading = ref("");

  async function dispatchTask(taskId) {
    actionLoading.value = taskId;
    try {
      await tasksApi.dispatch(taskId);
      onSuccess?.("dispatch");
    } finally {
      actionLoading.value = "";
    }
  }

  async function retryTask(taskId) {
    actionLoading.value = taskId;
    try {
      await tasksApi.retry(taskId);
      onSuccess?.("retry");
    } finally {
      actionLoading.value = "";
    }
  }

  async function cancelTask(taskId) {
    actionLoading.value = taskId;
    try {
      await tasksApi.cancel(taskId);
      onSuccess?.("cancel");
    } finally {
      actionLoading.value = "";
    }
  }

  return {
    actionLoading,
    dispatchTask,
    retryTask,
    cancelTask
  };
}
