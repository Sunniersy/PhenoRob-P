<template>
  <BaseModal
    :visible="visible"
    :title="title"
    :mask-closable="true"
    @close="onCancel"
  >
    <p class="confirm-message">{{ message }}</p>
    <template #footer>
      <button class="btn ghost" @click="onCancel">取消</button>
      <button class="btn danger" @click="onConfirm">确认</button>
    </template>
  </BaseModal>
</template>

<script setup>
import BaseModal from "./BaseModal.vue";

defineProps({
  visible: Boolean,
  title: { type: String, default: "确认操作" },
  message: { type: String, default: "确定要执行此操作吗？" },
});

const emit = defineEmits(["confirm", "cancel"]);
const onConfirm = () => emit("confirm");
const onCancel = () => emit("cancel");
</script>

<style scoped>
.confirm-message {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.65;
}
</style>
