import { defineStore } from "pinia";
import { robots } from "../api";

export const useRobotsStore = defineStore("robots", {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchAll() {
      this.loading = true;
      this.error = null;
      try {
        const data = await robots.list({ page_size: 100 });
        this.items = data.items || [];
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
  },
});
