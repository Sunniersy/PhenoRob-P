<template>
  <div>
    <div class="themeBg"></div>
   <div class="app">
      <div class="weather-monitoring">
        <weather-monitor></weather-monitor>
      </div>
      <div class="video">
        <video-page></video-page>
      </div>
      <div class="nutrient-monitoring">
        <nutrient-monitor></nutrient-monitor>
      </div>
    </div>

    <div class="someInfo">

      <div>
        <div class="box">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <div class="content">
          <!-- <h2>实时秒钟</h2> -->
          <p style="font-size: 40px;font-weight: bolder;"><a>{{ currentTime }}</a></p>
          <p style="font-size: 15px;"><a>小车运行时长：</a></p>
          <p style="font-size: 20px;font-weight: bolder;"><a>xx天xx小时xx分</a></p>
        </div>
        
        </div>

      </div>
      <div class="Info"> 
        <div class="InfoTitle">
          <el-icon :size="25"><PictureFilled /></el-icon> &nbsp;温室环境
        </div>
        
        <img src="../assets/sensor_imge/wenshi.jpg" alt="" class="wenshi">
      </div>
      <div class="Info">
        <div class="InfoTitle">
          <el-icon :size="25"><TrendCharts /></el-icon> &nbsp;养分气象监测
        </div>
         <div id="lineChart"></div>
      </div>
      <div class="Info">
        <div class="InfoTitle">
          <el-icon :size="25"><TrendCharts /></el-icon> &nbsp;模拟数据
        </div>
        
        <div id="histogramChart"></div>
      </div>
      <!-- <div class="Info">
        <p>模拟数据</p>
        <div id="scatterChart"></div>
      </div> -->
    </div>

    <div class="someInfo" style="margin-top: 50px">
      <button class="button">
        Fancy Button
        <div class="button__horizontal"></div>
        <div class="button__vertical"></div>
      </button>
      <button class="button">
        Fancy Button
        <div class="button__horizontal"></div>
        <div class="button__vertical"></div>
      </button>
      <button class="button">
        Fancy Button
        <div class="button__horizontal"></div>
        <div class="button__vertical"></div>
      </button>
      <button class="button">
        Fancy Button
        <div class="button__horizontal"></div>
        <div class="button__vertical"></div>
      </button>
    </div>



    <div class="monitor-platform">
      <monitor-platform></monitor-platform>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted ,ref} from "vue";
import { useRouter } from "vue-router";
import weatherMonitor from "@/views/sensor/monitor_page/weatherMonitor.vue";
import nutrientMonitor from "@/views/sensor/monitor_page/nutrientMonitor.vue"
import videoPage from "@/views/sensor/monitor_page/videoPage.vue";
import monitorPlatform from "@/views/sensor/monitorplatform/monitorPlatform.vue";
// import {ref} from 'vue'
// import { onMounted, onUnmounted } from 'vue'
import * as echarts from "echarts";


/*export default {
  components: {
    weatherMonitor,
    nutrientMonitor,
    videoPage,
    monitorPlatform,
  },*/
  
   /* 折线图数据 */
const lineOption = {
  xAxis: {
    type: 'category',
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      data: [150, 230, 224, 218, 135, 147, 260],
      type: 'line'
    }
  ]
};
// 散点图
const scatterOption = {
  dataset: [
    {
      source: [
        [1, 4862.4],
        [2, 5294.7],
        [3, 5934.5],
        [4, 7171.0],
        [5, 8964.4],
        [6, 10202.2],
        [7, 11962.5],
        [8, 14928.3],
        [9, 16909.2],
        [10, 18547.9],
        [11, 21617.8],
        [12, 26638.1],
        [13, 34634.4],
        [14, 46759.4],
        [15, 58478.1],
        [16, 67884.6],
        [17, 74462.6],
        [18, 79395.7]
      ]
    },
    // {
    //   transform: {
    //     type: 'ecStat:regression',
    //     config: {
    //       method: 'exponential'
    //       // 'end' by default
    //       // formulaOn: 'start'
    //     }
    //   }
    // }
  ],
  // title: {
  //   text: '1981 - 1998 gross domestic product GDP (trillion yuan)',
  //   subtext: 'By ecStat.regression',
  //   sublink: 'https://github.com/ecomfe/echarts-stat',
  //   left: 'center'
  // },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    }
  },
  xAxis: {
    splitLine: {
      lineStyle: {
        type: 'dashed'
      }
    }
  },
  yAxis: {
    splitLine: {
      lineStyle: {
        type: 'dashed'
      }
    }
  },
  series: [
    {
      name: 'scatter',
      type: 'scatter',
      datasetIndex: 0
    },
    {
      name: 'line',
      type: 'line',
      smooth: true,
      datasetIndex: 1,
      symbolSize: 0.1,
      symbol: 'circle',
      label: { show: true, fontSize: 16 },
      labelLayout: { dx: -20 },
      encode: { label: 2, tooltip: 1 }
    }
  ]
}
// 柱状图
  const histogramOption = {
    xAxis: {
    type: 'category',
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      data: [120, 200, 150, 80, 70, 110, 130],
      type: 'bar'
    }
  ]
  }

    //const mainElement = ref(null);
    /*折线图 */
function initHistogram() {
  console.log("1213");
  let chartDoms = document.querySelector("#lineChart");
  let myChart = echarts.init(chartDoms);
  lineOption && myChart.setOption(lineOption);
// 散点图
  // let chartDoms2 = document.querySelector("#scatterChart");
  // let myChart2 = echarts.init(chartDoms2);
  // lineOption && myChart2.setOption(scatterOption);
//柱状图
let chartDoms3 = document.querySelector("#histogramChart");
  let myChart3 = echarts.init(chartDoms3);
  lineOption && myChart3.setOption(histogramOption);
}

const currentTime = ref(new Date().toLocaleTimeString());
let timer=ref(null);
onMounted(()=>{
  console.log('123');
  initHistogram();
  timer = setInterval(() => {
        currentTime.value = new Date().toLocaleTimeString();
      }, 1000);
})

onBeforeUnmount(() => {
      clearInterval(timer.value);
    });

  // setup() {
  //   const displayData = ref(null) //存储大屏展示数据的响应式变量

  // },
  // 从后端 API 获取传感器数据
  // const fetchSensorData = () => {
  //   // 使用适当的 API 请求库（如 axios）从后端获取数据
  //   // 更新 nutrientSensors 和 weatherSensors 中的传感器数值
  // };

  // onMounted(() => {
  //   fetchSensorData(); // 在组件挂载后获取传感器数据
  // });

</script>

<style lang='scss' scoped>
.app {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  /* background-color: #7fb7a191; */
  padding-bottom: 1em;
}

.nutrient-monitoring,
.weather-monitoring {
  /* flex: 1 1 30%;
  justify-content: center;
  margin-bottom: 20px;
  width: 35%;
  padding: 0 20px; */

  display: flex;
  justify-content: center;
  align-items: center;
  align-items: flex-start;
  flex-direction: column;
  width: 30%;
}
.video {
  /* flex: 1 1 40%; */
  display: flex;
  justify-content: center;
  align-items: center;
  width: 40%;
  /* margin-bottom: 20px;
  padding: 0 20px; */
}
/* .nutrient-monitoring{
  
} */
.sensor-card {
  background-color: #f2f2f2;
  padding: 10px;
  margin-bottom: 10px;
}
.someInfo {
  display: flex;
  justify-content: space-around;
}
.Info {
  height: 325px;
  width: 350px;

  padding: 20px;

  background: linear-gradient(
    to right bottom,
    rgba(255, 255, 255, 0.7),
    rgba(255, 255, 255, 0.5),
    rgba(255, 255, 255, 0.4)
  );
  background-color: #ececec;

  /* 使背景模糊化 */
  backdrop-filter: blur(10px);
  box-shadow: 0 0 10px #3c9f64;
  border-radius: 15px;

}
.wenshi{
    height: 70%;
    width: 100%;
}
#lineChart{
    height:300px;
    width: 350px;
  }
#scatterChart{
  height:300px;
  width: 350px;
}
#histogramChart{
  height:300px;
  width: 350px;
}



body {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #fcf3ec;
}

.button {
  --offset: 10px;
  --border-size: 2px;

  display: block;
  position: relative;
  padding: 1.5em 3em;
  appearance: none;
  border: 0;
  background: transparent;
  color: #3c9f64;
  text-transform: uppercase;
  letter-spacing: 0.25em;
  outline: none;
  cursor: pointer;
  font-weight: bold;
  border-radius: 0;
  box-shadow: inset 0 0 0 var(--border-size) currentcolor;
  transition: background 0.8s ease;

  // font-size: 15px;
  // padding: 1em 2em;
  &:hover {
    background: rgba(100, 0, 0, 0.03);
  }

  &__horizontal,
  &__vertical {
    position: absolute;
    top: var(--horizontal-offset, 0);
    right: var(--vertical-offset, 0);
    bottom: var(--horizontal-offset, 0);
    left: var(--vertical-offset, 0);
    transition: transform 0.8s ease;
    will-change: transform;

    &::before {
      content: "";
      position: absolute;
      border: inherit;
    }
  }

  &__horizontal {
    --vertical-offset: calc(var(--offset) * -1);
    border-top: var(--border-size) solid currentcolor;
    border-bottom: var(--border-size) solid currentcolor;

    &::before {
      top: calc(var(--vertical-offset) - var(--border-size));
      bottom: calc(var(--vertical-offset) - var(--border-size));
      left: calc(var(--vertical-offset) * -1);
      right: calc(var(--vertical-offset) * -1);
    }
  }

  &:hover &__horizontal {
    transform: scaleX(0);
  }

  &__vertical {
    --horizontal-offset: calc(var(--offset) * -1);
    border-left: var(--border-size) solid currentcolor;
    border-right: var(--border-size) solid currentcolor;

    &::before {
      top: calc(var(--horizontal-offset) * -1);
      bottom: calc(var(--horizontal-offset) * -1);
      left: calc(var(--horizontal-offset) - var(--border-size));
      right: calc(var(--horizontal-offset) - var(--border-size));
    }
  }

  &:hover &__vertical {
    transform: scaleY(0);
  }
}

.box {
  // position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-0%, -0%);
  width: 325px;
  height: 325px;
  background: #114525a6;
  box-sizing: border-box;
  overflow: hidden;
  box-shadow: 0 20px 50px #3c9f64;
  border: 2px solid #3c9f64;
  color: white;
  padding: 20px;
}

.box:before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  transition: 0.5s;
  pointer-events: none;
}

.box:hover:before {
  left: -50%;
  transform: skewX(-5deg);
}

.box .content {
  position: absolute;
  top: 15px;
  left: 15px;
  right: 15px;
  bottom: 15px;
  border: 1px solid #f0a591;
  padding: 20px;
  text-align: center;
  box-shadow: 0 5px 10px rgba(9, 0, 0, 0.5);
}

.box span {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: block;
  box-sizing: border-box;
}

.box span:nth-child(1) {
  transform: rotate(0deg);
}

.box span:nth-child(2) {
  transform: rotate(90deg);
}

.box span:nth-child(3) {
  transform: rotate(180deg);
}

.box span:nth-child(4) {
  transform: rotate(270deg);
}

.box span:before {
  content: "";
  position: absolute;
  width: 100%;
  height: 2px;
  background: #50dfdb;
  animation: animate 30s linear infinite;
}

@keyframes animate {
  0% {
    transform: scaleX(0);
    transform-origin: left;
  }
  50% {
    transform: scaleX(1);
    transform-origin: left;
  }
  50.1% {
    transform: scaleX(1);
    transform-origin: right;
  }

  100% {
    transform: scaleX(0);
    transform-origin: right;
  }
}

.themeBg {
  content: "";
  width: 100%;
  height: 100%;
  position: fixed;
  left: 0;
  top: 0;
  --color-filter: hue-rotate(25.4219deg);
  background-size: cover;
  background-image: linear-gradient(
      rgba(255, 255, 255, 0.2),
      rgba(255, 255, 255, 0.2)
    ),
    url("../assets/img/homeback3.png");
  /* background-image: linear-gradient(transparent, rgb(250, 250, 250) 85%),
    url("../img/homeback.png"); */

  z-index: -2;

  opacity: 0.6
}

.InfoTitle{
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;

  font-weight: bolder;
  letter-spacing: 0.15em;
}
</style>