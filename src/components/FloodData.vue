<template>
  <div>
    <h1>Flood Monitoring System</h1>
    <h2>Real-Time Flood Data</h2>
    <!-- Dropdown để chọn khu vực -->
    <div style="display: flex; justify-content: space-between;">
      <div style="width: 70%;">
        <label for="location">Select Location:</label>
        <select id="location" v-model="selectedLocation" @change="fetchFloodData">
          <option value="hanoi">Hanoi</option>
          <option value="hochiminh">Ho Chi Minh</option>
          <option value="danang">Da Nang</option>
        </select>

        <!-- Biểu đồ hiển thị lượng mưa -->
        <div v-if="chartData">
          <line-chart :chart-data="chartData" :chart-options="chartOptions"></line-chart>
        </div>
        <p v-else>Loading data...</p>

        <!-- Hiển thị khả năng lũ lụt -->
        <div style="margin-top: 20px;" >
          <h3>Flood Risk Prediction</h3>
          <p>
            <strong>Rainfall Today:</strong> {{ rainfallToday }} mm <br />
            <strong>Flood Prediction:</strong> {{ floodPrediction ? "Flood" : "No Flood" }} <br />
            <strong>Flood Risk:</strong> {{ floodRiskMessage }}
          </p>
        </div>
      </div>

      <!-- Hiển thị dự báo thời tiết vào ngày mai -->
      <div style="width: 25%; border-left: 1px solid #ccc; padding-left: 20px;">
        <h3>Weather Forecast (Tomorrow)</h3>
        <p v-if="forecast">
          <strong>Temperature:</strong> {{ forecast.temp }}°C <br />
          <strong>Condition:</strong> {{ forecast.condition }} <br />
          <strong>Humidity:</strong> {{ forecast.humidity }}% <br />
          <strong>Wind Speed:</strong> {{ forecast.wind }} km/h
        </p>
        <p v-else>Loading weather forecast...</p>
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
      floodPrediction: null, // Dự đoán khả năng xảy ra lũ lụt
      floodRisk: null,
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
/* Tiêu đề */
h1 {
  color: #004c99;
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 10px;
}

h2 {
  color: #0077b6;
  text-align: center;
  font-size: 1.8rem;
  margin-bottom: 20px;
}

/* Khu vực chọn địa điểm */
label {
  font-weight: bold;
  margin-right: 10px;
  font-size: 1rem;
}

select {
  padding: 10px;
  margin-bottom: 20px;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 5px;
}

/* Bố cục chính */
div {
  font-family: "Arial", sans-serif;
}

div[style="display: flex; justify-content: space-between;"] {
  margin-top: 20px;
}

/* Biểu đồ */
canvas {
  max-width: 100%;
  height: 400px; /* Đặt chiều cao lớn hơn */
  width: 100%; /* Chiều rộng đầy đủ */
  margin: 0 auto;
}

/* Khu vực dự báo thời tiết */
h3 {
  color: #0077b6;
  font-size: 1.5rem;
  margin-bottom: 10px;
  text-align: center;
}

p {
  font-size: 1rem;
  line-height: 1.5;
  color: #333;
  margin: 5px 0;
}

div[style="width: 25%; border-left: 1px solid #ccc; padding-left: 20px;"] {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

strong {
  color: #333;
}
</style>


