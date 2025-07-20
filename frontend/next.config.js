/** @type {import('next').NextConfig} */
const nextConfig = {
  // 添加 rewrites 配置来实现 API 代理
  async rewrites() {
    return [
      {
        source: '/api/:path*', // 匹配所有以 /api/ 开头的请求
        destination: 'http://backend:8000/api/:path*', // 将它们代理到后端服务
      },
    ];
  },
};

module.exports = nextConfig; 