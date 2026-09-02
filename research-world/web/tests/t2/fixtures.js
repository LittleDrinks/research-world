// T2 用例基础夹具：自动挂线缆采集，用例结束后断言无凭证泄露（失败输出已脱敏）。
import { test as base } from "@playwright/test";
import { assertNoCredentialLeak, attachWireCollector } from "./helpers/wire.js";

export const test = base.extend({
  wire: [async ({ page }, use) => {
    const wire = attachWireCollector(page);
    await use(wire);
    await assertNoCredentialLeak(wire, page);
  }, { auto: true }],
});

export { expect } from "@playwright/test";
