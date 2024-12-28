<template>
  <div id="app">
    <Login v-if="!isLoggedIn" @loginSuccess="handleLoginSuccess" />
    <FloodData v-else />
  </div>
</template>

<script>
import Login from "./components/Login.vue";
import FloodData from "./components/FloodData.vue";

export default {
  name: "App",
  components: {
    Login,
    FloodData,
  },
  data() {
    return {
      isLoggedIn: false,
    };
  },
  methods: {
    handleLoginSuccess() {
      this.isLoggedIn = true;
    },
  },
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
