import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import { setUnauthorizedHandler } from "./api/client";
import router from "./router";
import "./styles.css";

setUnauthorizedHandler(() => router.push("/login"));

const app = createApp(App);

app.config.errorHandler = (err, instance, info) => {
  console.error("[Global Error]", err);
  console.error("[Global Error] component:", instance?.$?.type?.name || instance);
  console.error("[Global Error] info:", info);
};

app.use(createPinia());
app.use(router);
app.mount("#app");
