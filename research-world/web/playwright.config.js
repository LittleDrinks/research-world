import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir:'tests',
  timeout:180000,
  expect:{timeout:15000},
  use:{baseURL:process.env.RW_TEST_URL||'http://127.0.0.1:8095',browserName:'chromium',trace:'retain-on-failure'},
});
