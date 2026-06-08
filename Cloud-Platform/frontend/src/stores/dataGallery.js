import { defineStore } from "pinia";

import { assets as assetsApi } from "../api";

export const useDataGalleryStore = defineStore("dataGallery", {
  state: () => ({
    assets: [],
    total: 0,
    loading: false,
    error: "",
    filters: {
      task_id: "",
      robot_id: "",
      asset_type: ""
    }
  }),
  actions: {
    async fetchAssets(overrides = {}) {
      this.loading = true;
      this.error = "";
      try {
        const merged = { ...this.filters, ...overrides };
        const query = Object.fromEntries(Object.entries(merged).filter(([, value]) => value));
        const payload = await assetsApi.list({ ...query, page: 1, page_size: 60 });
        this.assets = payload.items;
        this.total = payload.total ?? payload.items.length;
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    clearFilters() {
      this.filters.task_id = "";
      this.filters.robot_id = "";
      this.filters.asset_type = "";
    }
  }
});
