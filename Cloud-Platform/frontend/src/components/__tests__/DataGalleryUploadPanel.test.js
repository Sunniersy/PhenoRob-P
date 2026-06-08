import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DataGalleryUploadPanel from "../DataGalleryUploadPanel.vue";

describe("DataGalleryUploadPanel", () => {
  it("renders production import copy without simulator actions", () => {
    const wrapper = mount(DataGalleryUploadPanel, {
      props: {
        form: { robot_id: "", task_name: "手动导入任务" },
        "onUpdate:form": () => {},
        robots: [{ id: "robot-1", name: "Robot 1" }],
        uploadCount: 2,
        uploading: false
      }
    });

    expect(wrapper.text()).toContain("手动导入资产");
    expect(wrapper.text()).toContain("正式功能");
    expect(wrapper.text()).not.toContain("模拟上传");
    expect(wrapper.text()).not.toContain("开始模拟上传");
  });
});
