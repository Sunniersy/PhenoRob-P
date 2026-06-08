import { describe, expect, it } from "vitest";

import { mergeRealtimeRobotState, pickDefaultRobotId, robotToneForStatus } from "../robotMonitor.model";

describe("pickDefaultRobotId", () => {
  it("returns the first robot when there is no current selection", () => {
    expect(
      pickDefaultRobotId("", [
        { id: "robot-1", name: "Robot 1" },
        { id: "robot-2", name: "Robot 2" }
      ])
    ).toBe("robot-1");
  });

  it("keeps the current selection when it still exists", () => {
    expect(
      pickDefaultRobotId("robot-2", [
        { id: "robot-1", name: "Robot 1" },
        { id: "robot-2", name: "Robot 2" }
      ])
    ).toBe("robot-2");
  });
});

describe("mergeRealtimeRobotState", () => {
  it("overlays live status and heartbeat values without mutating the source robot", () => {
    const robot = {
      id: "robot-1",
      robot_code: "robot-alpha",
      status: "OFFLINE",
      last_heartbeat_at: "2026-04-24T08:00:00Z"
    };

    const [merged] = mergeRealtimeRobotState(
      [robot],
      { "robot-alpha": { status: "RUNNING" } },
      { "robot-alpha": { timestamp: "2026-04-24T09:00:00Z", battery: 86 } }
    );

    expect(merged).toEqual({
      ...robot,
      status: "RUNNING",
      last_heartbeat_at: "2026-04-24T09:00:00Z",
      battery: 86
    });
    expect(robot.status).toBe("OFFLINE");
  });
});

describe("robotToneForStatus", () => {
  it("maps robot states to stable visual tones", () => {
    expect(robotToneForStatus("OFFLINE")).toBe("danger");
    expect(robotToneForStatus("IDLE")).toBe("warn");
    expect(robotToneForStatus("RUNNING")).toBe("success");
    expect(robotToneForStatus("UNKNOWN")).toBe("default");
  });
});
