<template>
  <div class="home_container">
    <div class="container-fuild">
      <!-- 导航 -->
      <div class="header-nav">
        <!-- 导航logo -->
        <div class="header-nav-logo">
          <img src="@/assets/img/hzauLogo.png" />
        </div>
      </div>
      <!-- banner -->
      <div class="article_banner">
        <img src="@/assets/img/banner/banner1.jpg" alt="banner" />
      </div>
      <!-- 科研项目 -->
      <div class="container-stage" style="margin-top: 30px;">
        <div class="stage-row">
          <div class="stage-col" v-for="(item, index) in typeList" :key="index">
            <div class="col-container">
              <img :src="item.logo" alt=""/>
              <div class="overlay">
                <span>{{ item.title }}</span>
                <h4>
                  <a href="">{{ item.titleDescription }}</a>
                </h4>
              </div>
            </div>
           <!--  <div>
              <p>{{ item.description }}</p>
            </div> -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup name="Index">
import useUserStore from "@/store/modules/user";
import type1 from "@/assets/img/1.jpg"
import type2 from "@/assets/img/2.jpg"
import type3 from "@/assets/img/3.jpg"
const user = useUserStore();
const version = ref("3.8.2");

function goTarget(url) {
  window.open(url, "__blank");
}

const typeList = reactive([
  {
    logo: type1,
    title: "表型文件",
    description:"这是作物表型管理平台的表型管理部分"
  },
  {
    logo: type2,
    title: "数据转换",
    description:"这是作物表型管理平台的图片管理部分"
  },
  {
    logo: type3,
    title: "用户管理",
    description:"这是作物表型管理平台的图片自动上传部分"
  },
  {
    logo: type2,
    title: "角色管理",
    description:"这是作物表型管理平台的图片自动上传部分"
  },
])


</script>

<style scoped lang="less">
.home_container {
  width: 100%;
}

.container-fuild {
  position: relative;
}

.container-fuild::after {
  position: absolute;
  left: 0;
  bottom: -40px;
  content: "";
  height: 50px;
  width: 100%;
  background: url(@/assets/img/brush-down.png);
  z-index: 2;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: bottom;
  box-sizing: border-box;
}


/* 顶部 */
.container-fuild {
  background: #fff;
  transition: all ease 0.6s;
  width: 100%;
  height: 80px;
  left: 0;
  top: 0;
}

/* 导航栏 */
.container-fuild .header-nav {
  height: 110px;
  display: flex;
  justify-content: space-between;
}

/* 导航栏logo */
.container-fuild .header-nav .header-nav-logo {
  width: 400px;
  height: 100%;
  float: left;
  position: relative;
}

/* 导航栏logo图片 */
.container-fuild .header-nav .header-nav-logo img {
  height: 65px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: auto;
}

.article_banner {
  width: 100%;
  height: 22vh;
  overflow: hidden;
}
.article_banner img {
  width: 100vw;
  height: 100%;
  object-fit: cover;
}


/* 为什么选择我们 */
.container {
  width: 1170px;
  margin: auto;
}

.text-center {
  text-align: center;
  margin-top: 30px;
}

.server-wrapper {
  margin: 10px;
}

.center-block {
  display: block;
  margin-right: auto;
  margin-left: auto;
}

.row {
  margin-right: -15px;
  margin-left: -15px;
  display: flex;
  color: #1f4e3d;
  border-color: #1f4e3d;
}

.col-md-3 {
  width: 25%;
}

/* 科研项目 */
.container-stage {
  width: auto;
  min-width: auto;
  max-width: inherit;
  padding-right: 0;
  .stage-row {
    --bs-gutter-x: 30px;
    --bs-gutter-y: 0;
    display: flex;
    flex-wrap: wrap;
    margin-top: calc(-1 * var(--bs-gutter-y));
    margin-right: calc(-0.5 * var(--bs-gutter-x));
    margin-left: calc(-0.5 * var(--bs-gutter-x));
    justify-content: center !important;

    .stage-col {
      flex: 0 0 auto;
      width: 23%;
      max-width: 90%;
      padding-right: calc(var(--bs-gutter-x) * 0.5);
      padding-left: calc(var(--bs-gutter-x) * 0.5);
      margin-top: var(--bs-gutter-y);

      .col-container {
        position: relative;
        padding-bottom: 30px;
        overflow: hidden;
        cursor: pointer;
        display: flex;
        align-items: flex-end;

        img {
          border: none;
          outline: none;
          max-width: 100%;
          height: 300px;
          vertical-align: middle;
        }

        .overlay {
          background: #1f4e3d;
          display: inline-block;
          position: absolute;
          z-index: 1;
          bottom: -10px;
          right: 16%;
          padding: 40px 80px;
          min-width: 65%;
          height: 100px;
          transition: height 0.3s;
          box-sizing: border-box;
          //visibility: hidden;
          //opacity: 0;

          span {
           display: inline-block;
            font-family: "Handlee", cursive;
            font-weight: 800;
            color: #fff;
            opacity: 0.95;
          }

          h4 {
            font-size: 20px;
            a {
              pointer-events: none;
              color: #fff;
            }
          }
        }

        .overlay::after {
          position: absolute;
          right: 0;
          bottom: 0;
          content: "";
          height: 100px;
          width: 100px;
          background: url(../assets/img/leaf-2.png);
          background-position-x: 0%;
          background-position-y: 0%;
          background-repeat: repeat;
          background-size: auto;
          background-repeat: no-repeat;
          background-position: right bottom;
          background-size: contain;
          z-index: -1;
          opacity: 0.1;
        }
      }

      .col-container:hover .overlay {
        visibility: visible;
        height: 120px;
        opacity: 1;
        box-sizing: border-box;
        margin-top: opx;
      }
    }
  }
}
</style>

