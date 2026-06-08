import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import { useNotificationStore } from "../notifications";

describe("notification store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("deduplicates websocket events by id", () => {
    const store = useNotificationStore();
    const event = { id: 10, event: "task.updated", payload: { task_id: "task-1", status: "RUNNING" } };

    store.pushEvent(event);
    store.pushEvent(event);

    expect(store.recent).toHaveLength(1);
    expect(store.taskUpdates["task-1"].status).toBe("RUNNING");
  });
});
