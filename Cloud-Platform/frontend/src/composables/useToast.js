import { ref } from 'vue'

const toastRef = ref(null)

export function useToast() {
  function setRef(ref) {
    toastRef.value = ref
  }

  function success(title, message) {
    return toastRef.value?.success(title, message)
  }

  function error(title, message) {
    return toastRef.value?.error(title, message)
  }

  function warning(title, message) {
    return toastRef.value?.warning(title, message)
  }

  function info(title, message) {
    return toastRef.value?.info(title, message)
  }

  return {
    setRef,
    success,
    error,
    warning,
    info
  }
}
