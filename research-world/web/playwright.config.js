import {defineConfig} from '@playwright/test';

if(!process.env.RW_TEST_URL)throw new Error('请设置 RW_TEST_URL，指向隔离测试环境；不要使用正式研究数据。');

export default defineConfig({
  testDir:'tests',
  timeout:180000,
  expect:{timeout:15000},
  use:{baseURL:process.env.RW_TEST_URL,browserName:'chromium',trace:'retain-on-failure'},
});
