import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import App from './App.tsx'
import 'antd/dist/reset.css'
import './index.css'
import './i18n'
import { useAppStore } from './store/useAppStore'

const RootApp: React.FC = () => {
  const language = useAppStore((state) => state.language)

  const antdLocale = language === 'en-US' ? enUS : zhCN

  return (
    <ConfigProvider
      locale={antdLocale}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <App />
    </ConfigProvider>
  )
}

async function enableMocking() {
  if (!import.meta.env.DEV) {
    return
  }

  try {
    const { worker } = await import('./mocks/browser')

    await worker.start({
      onUnhandledRequest: 'bypass',
    })
  } catch (error) {
    // 本地开发环境下，如果 MSW 初始化失败，不阻塞应用渲染
    // 只在控制台输出错误，方便排查
    // eslint-disable-next-line no-console
    console.error('Failed to start MSW, continue without mocks:', error)
  }
}

async function bootstrap() {
  await enableMocking()

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <RootApp />
    </React.StrictMode>,
  )
}

void bootstrap()

