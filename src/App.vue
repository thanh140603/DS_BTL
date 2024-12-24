<template>
  <div id="app">
    <FloodData />
  </div>
</template>

<script>
import FloodData from './components/FloodData.vue';

export default {
  name: 'App',
  components: {
    FloodData
  }
};
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  margin: 20px;
  padding: 20px;
  text-align: center;
}
</style>
