import { defineStore } from "pinia";

import { dashboard as dashboardApi, system as systemApi } from "../api";

const TTL_MS = 5000;

export const useDashboardStore = defineStore("dashboard", {
  state: () => ({
    overview: null,
    bootstrap: null,
    runtime: null,
    loading: false,
    error: "",
    _lastFetchedAt: 0
  }),
  actions: {
    async fetchOverview() {
      const now = Date.now();
      if (this.overview && now - this._lastFetchedAt < TTL_MS) {
        return;
      }
      if (this.loading) return;
      this.loading = true;
      this.error = "";
      try {
        const [overviewData, bootstrapData, runtimeData] = await Promise.all([
          dashboardApi.overview(),
          systemApi.bootstrapCheck(),
          systemApi.runtime()
        ]);
        this.overview = overviewData;
        this.bootstrap = bootstrapData;
        this.runtime = runtimeData;
        this._lastFetchedAt = Date.now();
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
});
