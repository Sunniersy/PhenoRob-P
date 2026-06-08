import { mount, flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { push, bootstrapAdmin, login, get } = vi.hoisted(() => ({
  push: vi.fn(),
  bootstrapAdmin: vi.fn(),
  login: vi.fn(),
  get: vi.fn()
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push })
}));

vi.mock("../../api/client", () => ({
  default: { get }
}));

vi.mock("../../stores/auth", () => ({
  useAuthStore: () => ({
    bootstrapAdmin,
    login
  })
}));

vi.mock("../../composables/useMotionReveal", () => ({
  useMotionReveal: () => {}
}));

import LoginView from "../LoginView.vue";

describe("LoginView", () => {
  beforeEach(() => {
    push.mockReset();
    bootstrapAdmin.mockReset();
    login.mockReset();
    get.mockReset();
  });

  it("switches to bootstrap mode when the system has no initial admin", async () => {
    get.mockResolvedValue({
      needs_initial_admin: true,
      initialization_ok: false,
      checks: {}
    });
    bootstrapAdmin.mockResolvedValue(undefined);

    const wrapper = mount(LoginView);
    await flushPromises();

    expect(wrapper.text()).toContain("初始化首个管理员");
    expect(wrapper.text()).toContain("初始化令牌");

    // Set all form fields
    await wrapper.find('input[autocomplete="username"]').setValue("admin");
    await wrapper.find('input[autocomplete="new-password"]').setValue("super-secret123");
    await wrapper.find('input[autocomplete="one-time-code"]').setValue("bootstrap-secret");

    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(bootstrapAdmin).toHaveBeenCalledWith("admin", "super-secret123", "bootstrap-secret");
    expect(push).toHaveBeenCalledWith("/dashboard");
  });

  it("uses standard login mode after initialization", async () => {
    get.mockResolvedValue({
      needs_initial_admin: false,
      initialization_ok: true,
      checks: {}
    });
    login.mockResolvedValue(undefined);

    const wrapper = mount(LoginView);
    await flushPromises();

    expect(wrapper.text()).toContain("进入控制台");
    expect(wrapper.text()).not.toContain("演示环境");
  });
});
