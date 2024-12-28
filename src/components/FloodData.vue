<template>
  <div>
    <!-- Title Section with Add User Button -->
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h1 style="text-align: center; width: 100%;">Flood Monitoring System</h1>
      <button
        @click="toggleAddUserForm"
        style="
          font-size: 2rem; 
          padding: 10px 20px; 
          border: 2px solid white; 
          background-color: #007bff; 
          color: white; 
          border-radius: 50%; 
          cursor: pointer; 
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);"
        title="Add New User"
      >
        +
      </button>

    </div>
    <h2>Real-Time Flood Data</h2>

    <!-- Main Layout -->
    <div style="display: flex; justify-content: space-between; gap: 20px; flex-wrap: wrap;">
      <!-- Chart Section -->
      <div style="flex: 1; min-width: 50%; max-width: 50%; margin-top: 20px;">
        <label for="location" style="display: block; margin-bottom: 10px;">Select Location:</label>
        <select id="location" v-model="selectedLocation" @change="fetchFloodData" style="width: 100%; padding: 10px; font-size: 1rem;">
          <option value="hanoi">Hanoi</option>
          <option value="hochiminh">Ho Chi Minh</option>
          <option value="danang">Da Nang</option>
        </select>

        <!-- Chart -->
        <div v-if="chartData" style="margin-top: 20px;">
          <line-chart :chart-data="chartData" :chart-options="chartOptions"></line-chart>
        </div>
        <p v-else>Loading data...</p>
      </div>

      <!-- Weather Forecast and Flood Prediction Section -->
      <div style="flex: 1; min-width: 45%; max-width: 45%; border: 1px solid #ccc; border-radius: 8px; padding: 20px; background-color: #f9f9f9; margin-top: 20px;">
        <h3 style="text-align: center; margin-bottom: 10px; font-size: 1.2em; color: #333;">Weather Forecast (Tomorrow)</h3>
        <div v-if="forecast" style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
          <!-- Temperature -->
          <div style="text-align: center;">
            <p style="font-size: 2em; font-weight: bold; margin: 0; color: #007BFF;">
              {{ forecast.temp }}°C
            </p>
            <p style="margin: 0; font-size: 0.9em; color: #666;">Tomorrow</p>
          </div>

          <!-- Weather Condition -->
          <div style="text-align: center;">
            <img :src="getWeatherIcon(forecast.condition)" alt="Weather Icon" style="width: 50px; height: 50px;" />
            <p style="margin: 5px 0; font-size: 1em; color: #333;">{{ forecast.condition }}</p>
          </div>

          <!-- Details -->
          <div style="text-align: center; font-size: 0.9em; color: #666;">
            <p><strong>Humidity:</strong> {{ forecast.humidity }}%</p>
            <p><strong>Wind:</strong> {{ forecast.wind }} km/h</p>
          </div>
        </div>
        <p v-else style="text-align: center; color: #666;">Loading weather forecast...</p>

        <!-- Flood Prediction -->
        <div style="margin-top: 20px;">
          <h3 style="text-align: center;">Flood Risk Prediction</h3>
          <p>
            <strong>Rainfall Today:</strong> {{ rainfallToday }} mm <br />
            <strong>Flood Prediction:</strong> {{ floodPrediction ? "Flood" : "No Flood" }} <br />
            <strong>Flood Risk:</strong> {{ floodRiskMessage }}
          </p>
        </div>
      </div>
    </div>

    <!-- Add User Modal -->
    <div v-if="showAddUserForm" class="modal-overlay" @click="toggleAddUserForm">
      <div class="add-user-modal" @click.stop>
        <h3 style="text-align: center;">Add New User</h3>
        <form @submit.prevent="addUser">
          <div class="form-group" style="margin-bottom: 15px;">
            <label for="newUsername" style="display: block; font-weight: bold;">Username:</label>
            <input type="text" id="newUsername" v-model="newUsername" required style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" />
          </div>
          <div class="form-group" style="margin-bottom: 15px;">
            <label for="newPassword" style="display: block; font-weight: bold;">Password:</label>
            <input type="password" id="newPassword" v-model="newPassword" required style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" />
          </div>
          <button type="submit" style="width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Add User</button>
        </form>
        <p v-if="userMessage" style="color: green; margin-top: 10px;">{{ userMessage }}</p>
      </div>
    </div>
  </div>
</template>






<script>
import { defineComponent, h, ref, watch } from "vue";
import { Chart } from "chart.js/auto";
import axios from "axios";

const LineChart = defineComponent({
  name: "LineChart",
  props: {
    chartData: {
      type: Object,
      required: true,
    },
    chartOptions: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const canvasRef = ref(null);
    let chartInstance = null;

    const createChart = () => {
      if (canvasRef.value) {
        chartInstance = new Chart(canvasRef.value, {
          type: "line",
          data: props.chartData,
          options: props.chartOptions,
        });
      }
    };

    const destroyChart = () => {
      if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
      }
    };

    watch(
      () => props.chartData,
      () => {
        destroyChart();
        createChart();
      },
      { deep: true }
    );

    return {
      canvasRef,
    };
  },
  render() {
    return h("canvas", { ref: "canvasRef" });
  },
});

export default {
  components: {
    LineChart,
  },
  data() {
    return {
      floodData: [],
      selectedLocation: "hanoi",
      chartData: null,
      chartOptions: {},
      forecast: null,
      rainfallToday: null,
      floodPrediction: null,
      floodRisk: null,
      showAddUserForm: false, // Controls visibility of the Add User form
      newUsername: "",
      newPassword: "",
      userMessage: "",
    };
  },
  computed: {
    floodRiskMessage() {
      if (this.floodRisk === null) return "Calculating...";
      if (this.floodRisk > 0.7) return "High Risk";
      if (this.floodRisk > 0.4) return "Moderate Risk";
      return "Low Risk";
    },
  },
  methods: {
    async fetchFloodData() {
      try {
        const floodResponse = await axios.get(
          `http://127.0.0.1:5000/api/flood-data?location=${this.selectedLocation}`
        );
        this.floodData = floodResponse.data;
        this.updateChart();

        const todayRainfall = this.floodData.find(
          (data) => data.date === new Date().toISOString().split("T")[0]
        );
        this.rainfallToday = todayRainfall ? todayRainfall.rain : null;

        if (this.rainfallToday !== null) {
          const predictionResponse = await axios.post(
            "http://127.0.0.1:5000/api/predict-flood",
            { rainfall_mm: this.rainfallToday }
          );
          this.floodPrediction = predictionResponse.data.flood_prediction;
          this.floodRisk = predictionResponse.data.flood_probability;
        }
      } catch (error) {
        console.error("Error fetching flood data:", error);
      }
    },
    async fetchForecastData() {
      try {
        const forecastResponse = await axios.get(
          `http://127.0.0.1:5000/api/weather-forecast?location=${this.selectedLocation}`
        );
        this.forecast = {
          temp: forecastResponse.data.temp,
          condition: forecastResponse.data.condition,
          humidity: forecastResponse.data.humidity,
          wind: forecastResponse.data.wind,
        };
      } catch (error) {
        console.error("Error fetching weather forecast:", error);
        this.forecast = null;
      }
    },
    updateChart() {
      const sortedData = [...this.floodData].sort((a, b) => new Date(a.date) - new Date(b.date));
      const labels = sortedData.map((data) => data.date);
      const data = sortedData.map((data) => data.rain);

      this.chartData = {
        labels: labels,
        datasets: [
          {
            label: "Rainfall (mm)",
            data: data,
            borderColor: "#0077b6",
            backgroundColor: "rgba(0, 119, 182, 0.2)",
          },
        ],
      };

      this.chartOptions = {
        responsive: true,
        plugins: {
          legend: {
            position: "top",
          },
          title: {
            display: true,
            text: "Daily Rainfall",
          },
        },
      };
    },
    async addUser() {
      try {
        const response = await axios.post("http://127.0.0.1:5000/api/add-user", {
          username: this.newUsername,
          password: this.newPassword,
        });
        if (response.data.success) {
          this.userMessage = "User added successfully!";
          this.newUsername = "";
          this.newPassword = "";
          this.showAddUserForm = false; // Close the form
        } else {
          this.userMessage = `Error: ${response.data.error}`;
        }
      } catch (error) {
        console.error("Error adding user:", error);
        this.userMessage = "An error occurred while adding the user.";
      }
    },
    toggleAddUserForm() {
      this.showAddUserForm = !this.showAddUserForm;
    },
    getWeatherIcon(condition) {
      const normalizedCondition = condition.trim().toLowerCase();
      if (normalizedCondition.includes("sun")) {
        return "/icons/sunny-icon.jpg";
      } else if (normalizedCondition.includes("cloud")) {
        return "/icons/cloudy-icon.jpg";
      } else if (normalizedCondition.includes("rain")) {
        return "/icons/rainy-icon.jpg";
      } else {
        return "/icons/default-weather-icon.png";
      }
    },
  },
  watch: {
    selectedLocation(newLocation) {
      this.fetchFloodData();
      this.fetchForecastData();
    },
  },
  mounted() {
    this.fetchFloodData();
    this.fetchForecastData();
  },
};
</script>






<style scoped>
/* Center the title */
h1 {
  color: #004c99;
  text-align: center;
  font-size: 2.5rem;
  margin: 20px 0;
}

/* Adjust the modal popup */
.add-user-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 400px;
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  z-index: 1000;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.add-user-modal h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  text-align: center;
}

.add-user-modal .form-group {
  margin-bottom: 15px;
}

.add-user-modal label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
}

.add-user-modal input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.add-user-modal button {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.add-user-modal button:hover {
  background-color: #0056b3;
}

/* Overlay background */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

/* Hide the modal initially */
.hidden {
  display: none;
}
</style>

