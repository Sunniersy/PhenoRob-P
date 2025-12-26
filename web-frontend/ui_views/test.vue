<template>
<button @click="change">改变</button>
</template>

<script setup>
import {ref,reactive,nextTick} from 'vue';

const url = ref('url')
const form = reactive({
  name: '111',
  url:url.value
})

function change(){
  url.value = 'url2'
  nextTick(()=>{
    console.log(form)
  })
}
</script>

<style scoped>
</style>
