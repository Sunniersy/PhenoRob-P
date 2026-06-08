import { defineStore } from "pinia";
import { tasks } from "../api";

export const useTasksStore = defineStore("tasks", {
  state: () => ({
    items: [],
    total: 0,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchList(params) {
      this.loading = true;
      this.error = null;
      try {
        const data = await tasks.list(params);
        this.items = data.items || [];
        this.total = data.total || 0;
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
