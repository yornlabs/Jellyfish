import React, { useMemo } from 'react'
import { Layout, Menu, theme, Dropdown, Space, Avatar, Typography, Select } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  PieChartOutlined,
  UnorderedListOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAppStore } from '../store/useAppStore'
import { useTranslation } from 'react-i18next'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const MainLayout: React.FC = () => {
  const { t, i18n } = useTranslation('layout')
  const location = useLocation()
  const navigate = useNavigate()
  const { token } = theme.useToken()

  const collapsed = useAppStore((state) => state.siderCollapsed)
  const toggleCollapsed = useAppStore((state) => state.toggleSider)
  const user = useAppStore((state) => state.user)
  const language = useAppStore((state) => state.language)
  const setLanguage = useAppStore((state) => state.setLanguage)

  const selectedKeys = useMemo(() => {
    if (location.pathname.startsWith('/dashboard')) return ['dashboard']
    if (location.pathname.startsWith('/list')) return ['list']
    if (location.pathname.startsWith('/settings')) return ['settings']
    return []
  }, [location.pathname])

  const menuItems = [
    {
      key: 'dashboard',
      icon: <PieChartOutlined />,
      label: <Link to="/dashboard">{t('menu.dashboard')}</Link>,
    },
    {
      key: 'list',
      icon: <UnorderedListOutlined />,
      label: <Link to="/list">{t('menu.list')}</Link>,
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">{t('menu.settings')}</Link>,
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      label: t('user.profile'),
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      label: t('user.logout'),
      onClick: () => {
        // 这里保留占位，实际项目中可接入登录逻辑
      },
    },
  ]

  return (
    <Layout className="min-h-screen">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        style={{
          background: token.colorBgContainer,
          borderRight: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <div className="flex items-center h-16 px-4 border-b border-solid" style={{ borderColor: token.colorBorderSecondary }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-500 flex items-center justify-center text-white font-bold">
              J
            </div>
            {!collapsed && (
              <div>
                <div className="text-base font-semibold text-gray-900">
                  {t('title')}
                </div>
                <div className="text-xs text-gray-500">
                  {t('subtitle')}
                </div>
              </div>
            )}
          </div>
        </div>

        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          style={{ borderRight: 'none', paddingTop: 8 }}
        />
      </Sider>

      <Layout>
        <Header
          className="flex items-center justify-between px-4"
          style={{
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Space size="large">
            <span
              className="cursor-pointer text-xl"
              onClick={toggleCollapsed}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </span>
            <Text className="hidden md:inline-block font-medium text-gray-800">
              {t('welcome')}
            </Text>
          </Space>

          <Space size="middle">
            <Select
              size="small"
              value={language}
              style={{ width: 120 }}
              onChange={(value) => {
                setLanguage(value)
                void i18n.changeLanguage(value)
                window.localStorage.setItem('jellyfish_language', value)
                document.documentElement.lang = value === 'en-US' ? 'en' : 'zh-CN'
              }}
              options={[
                { label: t('lang.zh'), value: 'zh-CN' },
                { label: t('lang.en'), value: 'en-US' },
              ]}
            />

            <Dropdown
              menu={{
                items: userMenuItems,
              }}
              placement="bottomRight"
            >
              <div className="flex items-center gap-2 cursor-pointer">
                <Avatar size={32} icon={<UserOutlined />} />
                <div className="hidden md:flex flex-col leading-tight">
                  <span className="text-sm font-medium text-gray-800">{user.name}</span>
                  <span className="text-xs text-gray-500">{user.role}</span>
                </div>
              </div>
            </Dropdown>
          </Space>
        </Header>

        <Content
          style={{
            margin: 16,
            padding: 16,
            background: token.colorBgLayout,
          }}
        >
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout

