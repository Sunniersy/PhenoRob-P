import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import createVitePlugins from './vite/plugins'
// import babel from "vite-babel-plugin";


export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd())
  const { VITE_APP_ENV, VITE_APP_UPLOAD_URL } = env
  return {
    base: VITE_APP_ENV === 'production' ? '/' : '/',
    plugins: [createVitePlugins(env, command === 'build'),
        // babel({
        //    babelConfig:{
        //     configFile:true
        //   }
        // })
],
    define: {
    },
    resolve: {
      alias: {
        '~': path.resolve(__dirname, './'),
        '@': path.resolve(__dirname, './src')
      },
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    // vite 相关配置
    server: {
      port: 81,
      host: true,
      open: true,
      proxy: {
        '/dev-api': {
          target: VITE_APP_UPLOAD_URL,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/dev-api/, '')
        },
          '/robot': {
              target: `http://192.168.0.13:8012`,
              ws: true,
              changeOrigin: true,
              rewrite: (p) => p.replace(/^\/robot/, '')
          },
      }
    },
    css: {
      postcss: {
        plugins: [
          {
            postcssPlugin: 'internal:charset-removal',
            AtRule: {
              charset: (atRule) => {
                if (atRule.name === 'charset') {
                  atRule.remove();
                }
              }
            }
          }
        ]
      }
    },
    //  transpileDependencies:['*'] //最开始这里的值为 true,查到的改成 * , 
    //   //应该是 转成es5,大佬知道的话,可留言解答!
  }
})
