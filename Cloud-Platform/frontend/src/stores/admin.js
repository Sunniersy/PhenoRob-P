import { defineStore } from "pinia";

import { admin as adminApi, system as systemApi, robots as robotsApi } from "../api";

export const useAdminStore = defineStore("admin", {
  state: () => ({
    users: [],
    roles: [],
    robots: [],
    alerts: [],
    system: null,
    loading: false,
    error: ""
  }),
  actions: {
    async fetchUsers() {
      const payload = await adminApi.listUsers({ page: 1, page_size: 50 });
      this.users = payload.items;
      return payload;
    },
    async fetchRoles() {
      const payload = await adminApi.listRoles({ page: 1, page_size: 20 });
      this.roles = payload.items;
      return payload;
    },
    async fetchRobots() {
      const payload = await robotsApi.list({ page: 1, page_size: 50 });
      this.robots = payload.items;
      return payload;
    },
    async fetchAlerts() {
      const payload = await adminApi.listAlerts({ page: 1, page_size: 20 });
      this.alerts = payload.items;
      return payload;
    },
    async fetchSystem() {
      const payload = await systemApi.bootstrapCheck();
      this.system = payload;
      return payload;
    },
    async fetchAll() {
      this.loading = true;
      this.error = "";
      try {
        const [bootstrap, userList, roleList, robotList, alertList] = await Promise.all([
          this.fetchSystem(),
          this.fetchUsers(),
          this.fetchRoles(),
          this.fetchRobots(),
          this.fetchAlerts()
        ]);
        return { bootstrap, userList, roleList, robotList, alertList };
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
});
